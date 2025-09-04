import logging
import os

import utils.messages as msgs
import utils.requests as reqs


class ClientStatus:
    def __init__(self):
        self.base_url = os.environ.get('N2BOT_CLISTATUS_URL')
        self.path = '/isp/getclistatus/'
        self.req = reqs.RequestsMethods()

    async def get_client_status(self, client_id: str, user) -> dict:
        logging.info("Iniciando get_client_status para cliente_id: %s", client_id)

        if not self.base_url:
            logging.warning("URL da API não configurada.")
            return {"error": True, "message": "⚠️ Erro interno: URL da API não configurada."}

        url = f"{self.base_url}{self.path}{client_id}"
        msg = msgs.BotMessage(user)

        try:
            data = await self.req.get(url)

            api_error_msg = data.get("error")
            if isinstance(api_error_msg, str):
                logging.warning("API retornou erro para cliente %s: %s", client_id, api_error_msg)
                return msg.api_error_message(api_error_msg)
            
            status_code = data.get("status_code")
            if status_code == 404:
                return "⚠️ <b>Cliente não encontrado</b>\n\nVerifique o código informado e tente novamente."
            elif status_code == 500:
                return "⚙️ <b>Erro no Servidor</b>\n\nOcorreu um erro interno ao tentar consultar os dados."
            
            client_status = data.get("result", [])
            response = msg.client_status_message(client_status)

            if not response:
                logging.info("Nenhum plano com login PPPoE encontrado.")
                return "⚠️ <b>Cliente não encontrado</b>\n\nVerifique o código informado e tente novamente."
            
            return response

        except Exception:
            logging.error("Erro ao fazer requisição para a API de status dos clientes.")
            return msg.client_status_error()    
