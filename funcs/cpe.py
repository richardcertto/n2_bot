import logging
import os

import utils.messages as msgs
import utils.requests as reqs


class CpeStatus:
    def __init__(self):
        self.base_url = os.environ.get('N2BOT_CPESTATUS_URL')
        self.path = '/acs/cpestatus/'
        self.req = reqs.RequestsMethods()

    async def get_cep_status(self, client_id: str, user) -> dict:
        logging.info("Iniciando get_cep_status para cliente_id: %s", client_id)

        if not self.base_url:
            logging.warning("URL da API não configurada.")
            return {"error": True, "message": "⚠️ Erro interno: URL da API não configurada."}
        
        url = f"{self.base_url}{self.path}{client_id}"
        msg = msgs.BotMessage(user)

        try:
            result = await self.req.get(url)
            result_data = result.get("Result", {})
            status_code = result_data.get("code")

            if status_code == 400:
                return "⚠️ <b>Cliente não encontrado.</b>\n\nVerifique o código informado e tente novamente."
            elif status_code == 500:
                return "⚙️ <b>Cliente não encontrado.</b>\n\nOs dados de busca podem estar inválidos."
            
            details = result_data.get("details", [])
            response = msg.build_cpestatus_message(details)

            if not response:
                logging.info("Nenhum plano com login PPPoE encontrado.")
                return "⚠️ <b>Cliente não encontrado</b>\n\nVerifique o código informado e tente novamente."
            
            return response
        
        except Exception as e:
            logging.error(f"Ocorreu um erro inesperado ao processar o status da CPE: {e}", exc_info=True)
            return msg.client_status_error()

