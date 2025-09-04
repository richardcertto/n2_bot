import logging

from db_auth.db_connector import get_db


def authorized_user(user_id: int) -> bool:
    db, cursor = None, None
    try:
        db, cursor = get_db()
        query = "SELECT 1 FROM n2users WHERE telegramid = %s"
        cursor.execute(query, (user_id,))
        if cursor.fetchone():
            return True
        else:
            logging.warning(f"Tentativa de acesso não autorizado pelo usuário com ID: {user_id}")
            return
    except Exception:
        logging.exception(f"Erro no banco de dados ao verificar permissão para o usuário {user_id}")
    finally:
        if cursor: cursor.close()
        if db: db.close()
