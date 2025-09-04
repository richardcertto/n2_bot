import os

import mysql.connector


def get_db():
    try:
        db = mysql.connector.connect(
            host=os.environ.get('N2BOT_MYSQL_HOST'),
            port=os.environ.get('N2BOT_MYSQL_PORT'),
            user=os.environ.get('N2BOT_MYSQL_USER'),
            password=os.environ.get('N2BOT_MYSQL_PASSWD'),
            database=os.environ.get('N2BOT_MYSQL_DB'),
        )
        cursor = db.cursor(dictionary=True)
        return db, cursor
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados MySQL: {e}")
        raise
