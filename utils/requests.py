import asyncio
import logging
import time
from json import JSONDecodeError

import aiohttp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class RequestsMethods:
    def __init__(self):
        pass

    def _handle_exceptions(self, e: Exception, url: str, start_time: float):
        elapsed = time.time() - start_time

        if isinstance(e, aiohttp.ClientResponseError):
            status_code = e.status
            logging.error(f"Erro de Status HTTP {status_code} para a URL {url}: {e.message}")
            return {"error": True, "message": f"Erro no servidor ({status_code})", "status_code": status_code}
        
        elif isinstance(e, asyncio.TimeoutError):
            logging.warning(f"Timeout de '{type(e).__name__}' após {elapsed:.2f}s para a URL: {url}")
            return {"error": True, "message": "Erro: O tempo para resposta foi excedido."}

        elif isinstance(e, aiohttp.ClientConnectorError):
            logging.error(f"Erro de Conexão para a URL {url}: {e}")
            return {"error": True, "message": "Erro: Falha ao tentar conectar com o servidor."}

        elif isinstance(e, aiohttp.TooManyRedirects):
            logging.error(f"Muitos redirecionamentos para a URL {url}: {e}")
            return {"error": True, "message": "Erro: A solicitação resultou em muitos redirecionamentos."}
        
        elif isinstance(e, JSONDecodeError):
            logging.error(f"A resposta da URL {url} não é um JSON válido.")
            return {"error": True, "message": "Erro: A resposta do servidor não pôde ser decodificada."}

        elif isinstance(e, aiohttp.ClientError):
            logging.error(f"Erro de Requisição para a URL {url}: {e}")
            return {"error": True, "message": "Erro: Ocorreu um problema durante a requisição."}
        
        else:
            logging.exception(f"Erro inesperado '{type(e).__name__}' durante a requisição para {url}")
            return {"error": True, "message": "Ocorreu um erro inesperado."}

    async def get(self, url, headers=None, timeout=20, retries=3, delay=2):
        for attempt in range(retries):
            start_time = time.time()
            try:
                request_timeout = aiohttp.ClientTimeout(total=timeout)
                async with aiohttp.ClientSession(timeout=request_timeout) as session:
                    async with session.get(url, headers=headers, ssl=False) as response:
                        response.raise_for_status()
                        response = await response.json()
                        logging.info(f"GET para {url} concluído em {time.time() - start_time:.2f} segundos")
                        return response
            except asyncio.TimeoutError:
                logging.warning(f"Timeout na tentativa {attempt + 1}/{retries} para a URL: {url}. Nova tentativa em {delay}s...")
                await asyncio.sleep(delay)
            except Exception as e:
                return self._handle_exceptions(e, url, start_time)
        logging.error(f"Falha ao obter dados de {url} após {retries} tentativas.")
        return {
            "error": True,
            "message": f"A requisição excedeu o número máximo de {retries} tentativas devido a timeouts."
        }
        
    async def post(self, url, headers=None, json=None, timeout=20, retries=3, delay=2):
        for attempt in range(retries):
            start_time = time.time()
            try:
                request_timeout = aiohttp.ClientTimeout(total=timeout)
                async with aiohttp.ClientSession(timeout=request_timeout) as session:
                    async with session.post(url, headers=headers, json=json, ssl=False) as response:
                        response.raise_for_status()
                        response = await response.json()
                        logging.info(f"POST para {url} concluído em {time.time() - start_time:.2f} segundos")
                        return response
            except asyncio.TimeoutError:
                logging.warning(f"Timeout na tentativa {attempt + 1}/{retries} para a URL: {url}. Nova tentativa em {delay}s...")
                await asyncio.sleep(delay)
            except Exception as e:
                return self._handle_exceptions(e, url, start_time)
        logging.error(f"Falha ao obter dados de {url} após {retries} tentativas.")
        return {
            "error": True,
            "message": f"A requisição excedeu o número máximo de {retries} tentativas devido a timeouts."
        }
