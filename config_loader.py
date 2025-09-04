import os
from configparser import ConfigParser


class LoaderInit:
    def __init__(self):
        self._config_loaded = False

    def loader(self):
        if self._config_loaded:
            return
        try:
            absolute_path = os.path.dirname(__file__)
            config_path = os.path.join(absolute_path, "config.ini")
            if not os.path.exists(config_path):
                raise FileNotFoundError('Arquivo de configuração de ambiente não foi encontrado')
            config = ConfigParser()
            config.read(config_path)
            os.environ['N2BOT_TOKEN'] = config['token']['TOKEN']
            os.environ['N2BOT_CTO_TOKEN'] = config['token']['TOKEN_CTO']
            os.environ['N2BOT_MYSQL_HOST'] = config['mysql']['host']
            os.environ['N2BOT_MYSQL_PORT'] = config['mysql']['port']
            os.environ['N2BOT_MYSQL_USER'] = config['mysql']['user']
            os.environ['N2BOT_MYSQL_PASSWD'] = config['mysql']['passwd']
            os.environ['N2BOT_MYSQL_DB'] = config['mysql']['db']
            os.environ['N2BOT_CLISTATUS_URL'] = config['urls']['URL_CLISTATUS']
            os.environ['N2BOT_CPESTATUS_URL'] = config['urls']['URL_CPESTATUS']
            os.environ['N2BOT_CTO_URL'] = config['urls']['URL_CHECK_CTO']
            os.environ['N2BOT_SOBREAVISO_URL'] = config['urls']['URL_SOBREAVISO']
            self._config_loaded = True
        except KeyError as e:
            raise KeyError(f"Chave {e} não encontrada no arquivo de configuração")
        except FileNotFoundError as e:
            raise FileNotFoundError(e)
