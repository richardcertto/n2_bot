import logging
import os

import utils.messages as msgs
import utils.requests as reqs


class CtoData:
    def __init__(self):
        self.token = os.environ.get('N2BOT_CTO_TOKEN')
        self.base_url = os.environ.get('N2BOT_CTO_URL')
        self.path_getpoint = '/getpoint?point_id='
        self.path_getbox = '/getbox?box_id='
        self.path_client = '/searchclient?cod_cli='
        self.path_boxname = '/searchbox?box_name='
        self.path_reservation = '/searchreservations?reservation_id='
        self.req = reqs.RequestsMethods()

    async def validate_pon_port(self, point_id: str) -> dict:
        url_point = f"{self.base_url}{self.path_getpoint}{point_id}"
        header = {"Token": self.token}

        data = await self.req.get(url_point, headers=header)
        if data.get("error"):
            print(f"Erro ao validar porta PON: {data['message']}")
            return True
        return data.get("result", {}).get("point", {}).get("pon_port", True)

    async def get_name_boxid(self, context):
        box_name = context.args[0]
        header = {"Token": self.token}
        url_search = f"{self.base_url}{self.path_boxname}{box_name}"
        response = await self.req.get(url_search, headers=header)

        results = response.get("results", [])
        if not results:
            return None

        return results[0].get("box_id")
    
    async def get_client_signal_status(self, client_id: str, service_hsi: str, box_id: str = None) -> dict:
        header = {"Token": self.token}
        code_box = box_id

        if not code_box:
            url = f"{self.base_url}{self.path_client}{client_id}"
            data = await self.req.get(url, headers=header)
            if data.get("error"):
                return f"Erro ao obter dados do cliente: {data['message']}"
            
            results = data.get('results', [])
            if len(results) == 1:
                code_box = results[0].get("box_id")
                if service_hsi:
                    cod_srv_hsi = results[0].get("point", {}).get("attributes", {}).get("cod_srv_hsi")
                    if cod_srv_hsi != str(service_hsi):
                        code_box = None
            elif service_hsi:
                for cto in results:
                    cod_srv_hsi = cto.get("point", {}).get("attributes", {}).get("cod_srv_hsi")
                    if cod_srv_hsi == str(service_hsi):
                        code_box = cto.get("box_id")
                        break
            
            if not code_box and results:
                code_box = results[0].get("box_id")

        if not code_box:
            return {"error": True, "message": "Nenhum CTO/Box ID encontrado para o cliente."}
        
        url_box = f"{self.base_url}{self.path_getbox}{code_box}"
        data_box = await self.req.get(url_box, headers=header)

        if data_box.get("error"):
            return f"Erro ao obter dados da box: {data_box['message']}"
        
        points = data_box.get("result", {}).get("points", [])
        for point in points:
            attributes = point.get("attributes", {})
            is_active_client = client_id in attributes.get("cod_cli_active", "").split('/')
            is_opportunity_client = str(client_id) == attributes.get("cod_opportunity")

            if is_active_client or is_opportunity_client:
                service_matches = not service_hsi or (str(service_hsi) == attributes.get("cod_srv_hsi"))
                
                if service_matches:
                    return {
                        "box_id": code_box,
                        "verified_signal": point.get("verified_signal"),
                        "status_name": point.get("status_name")
                    }

        return {"error": True, "message": "Sinal não encontrado para o cliente na box especificada."}
    
    async def process_check(self, client_id: str, service_hsi: str, user) -> dict:
        if not self.base_url:
            return {"message": "⚠️ Erro interno: URLs das APIs não configuradas corretamente."}

        header = {"Token": self.token}
        msg_handler = msgs.BotMessage(user)

        try:
            url_reserva = f"{self.base_url}{self.path_reservation}{client_id}"
            reservas_data = await self.req.get(url_reserva, headers=header)
            
            for res in reservas_data.get("results", []):
                if res.get("status_id") == 4 and (not service_hsi or res.get("attributes", {}).get("cod_srv_hsi") == service_hsi):
                    if not service_hsi:
                        service_hsi = res.get("attributes", {}).get("cod_srv_hsi")

                    if not await self.validate_pon_port(res.get("point_id")):
                        msg = "A porta reservada para este cliente não possui uma porta PON válida. Revise a reserva deste cliente!"
                        return {"message": msg_handler.mensagem_cto_data().format(cli=client_id, serv=service_hsi or "N/A", msg=msg, signal="", status="")}
                    
                    box_info = res.get("box", {})
                    box_id = box_info.get("box_id")
                    box_name = box_info.get("box_full_name", "CTO desconhecida")
                    point_name = res.get("point_name", "Ponto desconhecido")
                    client_status_info = await self.get_client_signal_status(client_id, service_hsi, box_id=box_id)
                    signal_str = f"{client_status_info.get('verified_signal')} dBm\n" if client_status_info.get("verified_signal") else ""
                    status_str = res.get("status_name", "") + "\n" if res.get("status_name") else ""

                    keyboard = [[{"text": f"Ver Detalhes da CTO {box_name}", "callback_data": f"cto_full_{box_id}"}]] if box_id else []
                    
                    return {
                        "message": msg_handler.mensagem_cto_data().format(cli=client_id, serv=service_hsi or "N/A", signal=signal_str, status=status_str, cto=box_name, point=point_name),
                        "reply_markup": {"inline_keyboard": keyboard}
                    }

            url_client = f"{self.base_url}{self.path_client}{client_id}"
            client_data = await self.req.get(url_client, headers=header)
            results_cliente = client_data.get("results", [])

            if not results_cliente:
                message = f"❌ Nenhuma conexão ativa ou reserva válida encontrada para o cliente <b>{client_id}</b>. Verifique a documentação."
                return {"message": message}

            if not service_hsi and len(results_cliente) > 1:
                services_list = []
                for service in results_cliente:
                    serv_id = service.get("point", {}).get("attributes", {}).get("cod_srv_hsi", "N/A")
                    box_name = service.get("box_full_name", "CTO desconhecida")
                    services_list.append(f"⚙️ Serviço <code>{serv_id}</code> na CTO <code>{box_name}</code>")
                
                message = (
                    f"⚠️ Cliente <b>{client_id}</b> possui múltiplos serviços ativos.\n\n"
                    f"Por favor, especifique o código do serviço desejado.\n\n"
                    f"<b>Exemplo:</b> <code>/cto {client_id} código_do_serviço</code>\n\n"
                    "<b>Serviços encontrados:</b>\n" + "\n".join(services_list)
                )
                return {"message": message}

            target_service_data = None
            if service_hsi:
                target_service_data = next((p for p in results_cliente if p.get("point", {}).get("attributes", {}).get("cod_srv_hsi") == str(service_hsi)), None)
            elif len(results_cliente) == 1:
                target_service_data = results_cliente[0]
                service_hsi = target_service_data.get("point", {}).get("attributes", {}).get("cod_srv_hsi")

            if target_service_data and target_service_data.get("point", {}).get("status_id") == 8:
                point_info = target_service_data.get("point", {})
                if not await self.validate_pon_port(point_info.get("point_id")):
                    return {"message": "A porta do cliente não possui uma PON válida. Revise o registro!"}

                box_id_cliente = target_service_data.get("box_id")
                box_name_cliente = target_service_data.get("box_full_name", "CTO desconhecida")
                point_name = target_service_data.get("point", {}).get("point_name", "Ponto desconhecido")
                client_status_info = await self.get_client_signal_status(client_id, service_hsi)
                signal_str = f"{client_status_info.get('verified_signal')} dBm\n" if client_status_info.get("verified_signal") else ""
                status_str = f"{client_status_info.get('status_name')}\n" if client_status_info.get("status_name") else ""
                
                keyboard = [[{"text": f"Ver Detalhes da CTO {box_name_cliente}", "callback_data": f"cto_full_{box_id_cliente}"}]] if box_id_cliente else []
                
                return {
                    "message": msg_handler.mensagem_cto_data().format(cli=client_id, serv=service_hsi or "N/A", signal=signal_str, status=status_str, cto=box_name_cliente, point=point_name),
                    "reply_markup": {"inline_keyboard": keyboard}
                }

            message = f"❌ Nenhuma conexão ativa ou reserva válida encontrada para o cliente <b>{client_id}</b>"
            if service_hsi:
                message += f" com o serviço <code>{service_hsi}</code>"
            message += ". Verifique os dados informados e a documentação."
            return {"message": message}

        except Exception as e:
            logging.exception(f"Erro ao processar a verificação CTO para o cliente {client_id}: {e}")
            return {"message": "⚠️ Ocorreu um erro inesperado. Tente novamente mais tarde."}
