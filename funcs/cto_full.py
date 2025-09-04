import asyncio
import logging
import os
from typing import Any, Dict, List

import utils.convert_funcs as cfs
import utils.requests as reqs


class CtoFull:
    def __init__(self):
        self.token = os.environ.get("N2BOT_CTO_TOKEN")
        self.base_url = os.environ.get("N2BOT_CTO_URL")
        self.url_cpe = os.environ.get("N2BOT_CPESTATUS_URL")
        self.cpe_path = "/acs/cpestatus/"
        self.box_path = '/getbox?box_id='
        self.req = reqs.RequestsMethods()
        self.cf = cfs.ConvertFuncs()

    async def get_cto_data_by_box(self, box_id: str) -> dict:
        url = f"{self.base_url}{self.box_path}{box_id}"
        headers = {"Token": self.token}

        data = await self.req.get(url, headers=headers, timeout=60)

        if data.get("error"):
            logging.error(f"Erro ao consultar API da CTO (box_id={box_id}): {data.get('message')}")
            return {}

        if data.get("status_code") == 400:
            logging.warning("Os parâmetros de busca inseridos são inválidos.")
            return "⚠️ <b>Caixa não encontrado.</b>\n\nVerifique o código informado e tente novamente."
        
        if data.get("status_code") == 500:
            logging.warning("O servidor pode estar temporariamente indisponível.")
            return "⚙️ O servidor está temporariamente indisponível. Tente novamente mais tarde."
        
        result = data.get("result")
        if not result:
            logging.warning(f"⚠️ Resposta da API da CTO não contém 'result' (box_id={box_id})")
            return {}

        return result

    async def _fetch_cpe_status_for_point(self, point: Dict[str, Any]) -> Dict[str, Any]:
        attributes = point.get("attributes", {})
        cod_srv_hsi = attributes.get("cod_srv_hsi")
        cod_cli_active = attributes.get("cod_cli_active")

        if not cod_cli_active:
            return {}

        url_cpe = f"{self.url_cpe}{self.cpe_path}{cod_cli_active}"
        data_cpe = await self.req.get(url_cpe)

        if data_cpe.get("error"):
            logging.warning(f"Erro ao consultar CPE do cliente {cod_cli_active}: {data_cpe.get('message')}")
            return {cod_cli_active: {"Sinal": "N/A", "state": "Erro na Consulta"}}

        result = data_cpe.get("Result", {})
        if result.get("code") in (400, 500):
            logging.info(f"Cliente {cod_cli_active} cancelado ou sem dados relevantes.")
            return {cod_cli_active: {"Sinal": "Cliente Cancelado ❌", "state": "Desc 1"}}

        details_list = result.get("details", [])
        if not details_list:
            logging.info(f"Cliente {cod_cli_active} sem lista de detalhes.")
            return {cod_cli_active: {"Sinal": "N/A", "state": "Desc 2"}}

        cpe_details = {}
        accept_strings = ["48", "5a"]
        for cpe in details_list:
            if cpe.get("cid") == cod_srv_hsi and any(item in cpe.get("cpeid", "") for item in accept_strings):
                cpe_details = cpe
                break
        
        modelo = cpe_details.get("Modelo")
        sinal_raw = cpe_details.get("Sinal")
        sinal_calc = self.cf.eval_power(sinal_raw) if modelo == 'ONT142NG' and sinal_raw is not None else sinal_raw
        
        sinal = self.cf.eval_power_pretty(sinal_calc)
        state = cpe_details.get("state", "Desconhecido(sem dados)")

        return {cod_cli_active: {"Sinal": sinal, "state": state}}

    async def get_status_box(self, box_id: str, points: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        cpe_status_data = {}
        logging.info(f"Iniciando verificação da box_id: {box_id} com {len(points)} pontos.")

        tasks = [self._fetch_cpe_status_for_point(point) for point in points]

        results = await asyncio.gather(*tasks)

        for res_dict in results:
            if res_dict:
                cpe_status_data.update(res_dict)

        logging.info(f"Finalizada verificação da box_id: {box_id}")
        return cpe_status_data
