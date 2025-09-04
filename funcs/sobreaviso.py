import logging
import os

import utils.messages as msgs
import utils.requests as reqs


class Sobreaviso:
    def __init__(self):
        self.url = os.environ.get('N2BOT_SOBREAVISO_URL')
        self.path = "/api/sobreaviso"
        self.req = reqs.RequestsMethods()

    async def sobreaviso_ope(self, user):
        url = f'{self.url}{self.path}'
        msg = msgs.BotMessage(user)
        try:
            data = await self.req.get(url)
            if not data or data.get("error"):
                logging.warning("message", "Erro: Não foi possível obter os dados de sobreaviso.")
                return msg.sobreaviso_error()
            response = msg.message_sobreaviso(data)
            return response
        except Exception as e:
            logging.error(f"Exceção não tratada em sobreaviso: {e}")
            return msg.sobreaviso_error()
