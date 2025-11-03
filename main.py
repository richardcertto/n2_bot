import asyncio
import logging
import os
import re
from warnings import filterwarnings

import nest_asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, ApplicationBuilder,
                          CallbackQueryHandler, CommandHandler, ContextTypes)
from telegram.warnings import PTBUserWarning

import config_loader as config
import db_auth.users_auth as auth
import funcs.clients as clis
import funcs.cpe as cpes
import funcs.cto as ctos
import funcs.cto_full as ctfs
import funcs.sobreaviso as sobre
import utils.messages as msgs

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

# Configuração de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers.clear()
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
nest_asyncio.apply()

# Inicializações
loader = config.LoaderInit()
loader.loader()
cli = clis.ClientStatus()
cpe = cpes.CpeStatus()
cto = ctos.CtoData()
ctf = ctfs.CtoFull()

cto_regex = "([A-Z]{2,4}-A[0-9]{3}-CTO[1-9]{1,3}|[A-Z]{2,4}_A[0-9]{3}_CD[0-9]{1,2}_(C[1-9]{1,2})-(A[0-9]{1,3}|T[0-9]{1,3}|D[0-9]{1,2})-(T[0-9]{1,3}|T[0-9]{1,3}-FTTA_(.*))_CTO[1-9]{1,3}|[A-Z]{2,4}_A[0-9]{3}_CTO[1-9]{1,3})"

async def denied(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    msg = msgs.BotMessage(user)
    message = msg.access_denied()
    await update.effective_message.reply_text(message, parse_mode="HTML")

async def is_user_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if not auth.authorized_user(user_id):
        await denied(update, context)
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_authorized(update, context):
        return
    user = update.effective_user
    message = msgs.BotMessage(user)
    text, reply_markup = message.welcome_message()
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == '_help':
        user = query.from_user
        msg = msgs.BotMessage(user)
        message = msg.help_message()
        await query.edit_message_text(text=message, parse_mode="HTML")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await is_user_authorized(update, context):
        return
    
    wait_message = await update.effective_message.reply_text(
        text="⏳ Processando sua solicitação, aguarde...",
        parse_mode="HTML"
    )

    user = update.effective_user
    bot_messege = msgs.BotMessage(user)
    message = bot_messege.help_message()

    await wait_message.delete()
    await update.effective_message.reply_text(message, parse_mode="HTML")

async def sobreaviso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    wait_message = await update.effective_message.reply_text(
        text="⏳ Processando sua solicitação, aguarde...",
        parse_mode="HTML"
    )

    user = update.effective_user
    sob = sobre.Sobreaviso()
    message = await sob.sobreaviso_ope(user)

    await wait_message.delete()
    await update.effective_message.reply_text(message, parse_mode="HTML")

async def client(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_authorized(update, context):
        return
    
    if not context.args:
        await update.effective_message.reply_text("❗ Você precisa fornecer o código do cliente.")
        return
    
    wait_message = await update.effective_message.reply_text(
        text="⏳ Processando sua solicitação, aguarde...",
        parse_mode="HTML"
    )

    user = update.effective_user
    cliente_id = context.args[0]
    message = await cli.get_client_status(cliente_id, user)

    await wait_message.delete()
    await update.effective_message.reply_text(message, parse_mode="HTML")

async def cpestatus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_authorized(update, context):
        return
    
    if not context.args:
        await update.effective_message.reply_text("❗ Você precisa fornecer o código do cliente.")
        return
    
    wait_message = await update.effective_message.reply_text(
        text="⏳ Processando sua solicitação, aguarde...",
        parse_mode="HTML"
    )

    user = update.effective_user
    client_id = context.args[0]
    mensagem = await cpe.get_cep_status(client_id, user)

    await wait_message.delete()
    await update.effective_message.reply_text(mensagem, parse_mode="HTML")

async def cto_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_authorized(update, context):
        return

    if not context.args:
        await update.effective_message.reply_text("❗ Você precisa fornecer o código do cliente ou o nome da CTO.")
        return

    wait_message = await update.effective_message.reply_text("⏳ Processando sua solicitação, aguarde...")

    try:
        user = update.effective_user
        first_arg = context.args[0]
        msg_handler = msgs.BotMessage(user)
        if re.match(cto_regex, first_arg, re.IGNORECASE):
            box_id = await cto.get_name_boxid(context)
            if not box_id:
                await wait_message.edit_text("❗ CTO não encontrada na base de dados.")
                return
            result = await ctf.get_cto_data_by_box(box_id)
            if isinstance(result, str):
                await wait_message.edit_text(result, parse_mode="HTML")
                return
            cpe_status = await ctf.get_status_box(box_id, result.get("points", []))
            mensagem = msg_handler.build_message_cto(result, cpe_status)
            await wait_message.edit_text(mensagem, parse_mode="HTML")
        else:
            client_id = first_arg
            service_hsi = context.args[1] if len(context.args) > 1 else None
            result = await cto.process_check(client_id, service_hsi, user)
            reply_markup = None
            if "reply_markup" in result and result.get("reply_markup"):
                keyboard_layout = result["reply_markup"].get("inline_keyboard", [])
                if keyboard_layout:
                    keyboard = [
                        [InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"]) for btn in row]
                        for row in keyboard_layout
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

            await wait_message.edit_text(
                text=result.get("message", "Ocorreu um erro inesperado."),
                reply_markup=reply_markup,
                parse_mode="HTML"
            )

    except Exception as e:
        logging.error(f"Erro na função cto_data: {e}", exc_info=True)
        await wait_message.edit_text(f"❌ Ocorreu um erro ao processar sua solicitação: {e}")

async def cto_full(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query_data = update.callback_query.data
    user = update.effective_user
    msg = msgs.BotMessage(user)

    try:
        box_id = query_data.split("_")[2]
    except IndexError:
        await update.effective_message.reply_text("Erro ao processar ID da CTO a partir do callback.")
        return

    try:
        result = await ctf.get_cto_data_by_box(box_id)
        cpe_status = await ctf.get_status_box(box_id, result.get("points", []))
        mensagem = msg.build_message_cto(result, cpe_status)
        await update.effective_message.edit_text(mensagem, parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"Erro no processo do cto_full: {e}", exc_info=True)
        await update.effective_message.reply_text(f"Ocorreu um erro ao processar a CTO: {e}")

def get_bot_token() -> str:
    token = os.environ.get('N2BOT_TOKEN')
    if not token:
        logger.critical("Variável de ambiente 'TOKEN' não definida.")
    return token

def register_handlers(app: Application):
    command_handlers = {
        "start": start,
        "cliente": client,
        "ont": cpestatus,
        "cto": cto_data,
        "sobreaviso": sobreaviso,
        "ajuda": help,
    }

    for command, handler_func in command_handlers.items():
        app.add_handler(CommandHandler(command, handler_func))
    app.add_handler(CallbackQueryHandler(cto_full, pattern=r"^cto_full_"))
    app.add_handler(CallbackQueryHandler(button_handler))

async def main() -> None:
    try:
        token = get_bot_token()
        app = ApplicationBuilder().token(token).build()
        register_handlers(app)
        logger.info("Bot iniciando...")
        await app.run_polling()

    except Exception as e:
        logger.error(f"Erro inesperado ao executar o bot: {e}", exc_info=True)

if __name__=='__main__':
    asyncio.get_event_loop().run_until_complete(main())
