import textwrap

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, User

import utils.convert_funcs as cfs

cf = cfs.ConvertFuncs()

class BotMessage:
    def __init__(self, user: User):
        self.user = user

    def welcome_message(self) -> tuple[str, InlineKeyboardMarkup]:
        text = textwrap.dedent(f"""\
            👋 Olá, <b>{self.user.first_name}</b>!

            Bem-vindo(a) ao Assistente Virtual da Certto para o time N2.
            Seu acesso foi verificado com sucesso. ✅

            Estou aqui para simplificar suas tarefas operacionais do dia a dia.
        """)

        keyboard = [
            [InlineKeyboardButton("Ver Comandos Disponíveis", callback_data="_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        return text, reply_markup
    
    def access_denied(self) -> str:
        message = (
            f"<b>🚫 Acesso negado, {self.user.first_name}.</b>\n\n"
            "⚠️ Seu ID do Telegram não foi encontrado na lista de usuários autorizados.\n"
            "ℹ️ Se achar que se trata de um erro, contate o setor de Operações."
        )
        return message

    def help_message(self) -> str:
        message = textwrap.dedent(f"""\
            👋 Olá, <b>{self.user.first_name}</b>!
            Aqui está a lista de comandos que você pode usar:

            👤 <b>Clientes:</b>
            • <code>/cliente &lt;código_do_cliente&gt;</code> — Exibe o status do cliente.

            📡 <b>Equipamentos:</b>
            • <code>/ont &lt;código_do_cliente&gt;</code> — Verifica o status da ONT.
            • <code>/cto &lt;código_do_cliente&gt; &lt;código_do_plano&gt;</code> — Verifica a CTO.
              🔸 <i>Se houver múltiplos planos, informe o código.</i>
              🔸 <i>Consulta também por <code>/cto &lt;nome_da_cto&gt;</code>.</i>

            📋 <b>Outros Comandos:</b>
            • <code>/sobreaviso</code> — Mostra o plantonista atual.
            • <code>/ajuda</code> — Exibe esta mensagem de ajuda.
        """)
        return message
    
    def message_sobreaviso(self, data: dict) -> str:
        try:
            nome = data.get("nome", "Desconhecido")
            periodo_inicio = data.get("periodo_inicio", "Início não informado")
            periodo_fim = data.get("periodo_fim", "Fim não informado")
            telefone_plantao = data.get("tel_plantao", "Não informado")
            telefones = data.get("tel", [])
            
            telefone_particular = telefones[0] if len(telefones) > 0 else "Não informado"
            ramal_interno = telefones[1] if len(telefones) > 1 else "Não informado"

            message = textwrap.dedent(f"""\
                ⚠️ <b>Sobreaviso</b>
                <i>(Válido após horário comercial, sábados, domingos e feriados)</i>

                <b>Procedimento:</b> Se o plantonista não atender na primeira tentativa, insista com novas ligações a cada 5 minutos e registre o ocorrido no Redmine.

                • <b>Período:</b> {periodo_inicio} até {periodo_fim}
                • <b>Plantonista:</b> {nome}
                • <b>Telefone de plantão:</b> {telefone_plantao}
                • <b>Telefone particular:</b> {telefone_particular}
                • <b>Ramal interno:</b> {ramal_interno}
            """)
            return message
        except Exception:
            return "Não foi possível formatar as informações de sobreaviso."
        
    def sobreaviso_error(self) -> str:
        message = textwrap.dedent("""\
            🤖❌ <b>Falha na consulta</b>

            Houve um problema ao consultar o serviço de sobreaviso. 
            
            O sistema pode estar temporariamente indisponível. Por favor, tente novamente em alguns instantes.
        """)
        return message
    
    def client_status_message(self, data: list) -> str:
        status_emoji = {
            'Connected': '✅',
            'Disconnected': '❌',
            'Desconhecido': '❓'
        }

        message_parts = ["👤 <b>Status do Cliente:</b>"]

        for item in data:
            if item.get('login_pppoe'):
                status = item.get('status_pppoe', 'Desconhecido')
                emoji = status_emoji.get(status)
                ponto_acesso = item.get('ponto_acesso') or 'Não informado'
                
                plan_info = textwrap.dedent(f"""\
                    <b>📶 Plano:</b> ({item.get('numero_plano', 'N/A')}) {item.get('nome_plano', 'N/A')}
                    <b>ℹ️ Status PPPoE:</b> {status} {emoji}
                    <b>📄 Estado do Contrato:</b> {item.get('status_plano', 'N/A')}
                    <b>🌐 IP:</b> <code>{item.get('last_ip', 'N/A')}</code>
                    <b>📍 Ponto de Acesso:</b> {ponto_acesso}""")
                
                message_parts.append(plan_info)

        header = message_parts[0]
        plans_section = "\n\n— — — — — — — — — —\n\n".join(message_parts[1:])
        
        if not plans_section:
            return ""

        return f"{header}\n\n{plans_section}"
    
    def client_status_error(self) -> str:
        message = textwrap.dedent("""\
            🤖❌ <b>Falha na consulta</b>

            Houve um problema ao consultar o status do cliente. 
            
            O sistema pode estar temporariamente indisponível. Por favor, tente novamente em alguns instantes.
        """)
        return message
    
    def api_error_message(self, api_error_msg) -> str:
        message = textwrap.dedent(f"""\
            ⚠️ <b>Consulta Inválida</b>

            <b>Motivo:</b> "{api_error_msg}"

            Por favor, verifique o código do cliente e tente novamente.
        """)
        return message

    def build_cpestatus_message(self, details: list) -> str:
        if not details:
            return "⚠️ Nenhum equipamento encontrado para este cliente."

        ont_blocks = []

        for item in details:
            cid = item.get('cid') or 'Sem dados'
            cid2 = item.get('cid2') or 'Sem dados'
            cpeid = item.get('cpeid') or 'Sem dados'
            modelo = item.get('Modelo') or 'Sem dados'
            sinal_raw = item.get('Sinal')
            sinal = cf.eval_power(sinal_raw) if modelo == 'ONT142NG' else sinal_raw
            
            ont_info = textwrap.dedent(f"""\
                <b>⚙️ Status:</b> <code>{cf.getState_pretty(item.get('state'))}</code>
                <b>🔢 Serial:</b> <code>{cpeid}</code>
                <b>📍 Modelo:</b> <code>{modelo}</code>
                <b>📶 Sinal:</b> <code>{cf.eval_power_pretty(sinal)}</code>
                <b>⏱️ Uptime:</b> <code>{cf.convert_uptime(item.get('Uptime'))}</code>
                <b>🌡️ Temp:</b> <code>{cf.temp_f_2_c(item.get('Temp'), modelo)}°C</code>
                <b>👤 Cliente:</b> <code>{cid2}</code>
                <b>📡 Plano:</b> <code>{cid}</code>
            """)
            ont_blocks.append(ont_info)

        header = f"<b>📡 Equipamentos do Cliente:</b>"
        
        body = "\n— — — — — — — — — —\n\n".join(ont_blocks)
        
        return f"{header}\n\n{body}"
    
    def mensagem_cto_data(self) -> str:
        return (
            "<b>🔍 Resultado da Verificação</b>\n"
            "<b>👤 Cliente:</b> {cli}\n"
            "<b>📡 Serviço:</b> {serv}\n"
            "<b>💡 λ base:</b> {signal}"
            "<b>📌 Status:</b> {status}"
            "<b>📝 CTO:</b> {cto}\n"
            "<b>🔌 Saída:</b> {point}"
        )
    
    def build_message_cto(self, result: dict, cpe_status: dict = None) -> str:
        box_name = result.get("box_full_name", "N/A")
        points = result.get("points", [])
        if not points:
            return f"Nenhuma saída encontrada para a CTO {box_name}."
        status_emojis = {
            "disponível": "🟢",
            "em operação": "🔵",
            "reservado": "🟠",
            "bloqueado": "🔴"
        }
        status_counts = {
            "disponível": 0,
            "em operação": 0,
            "reservado": 0,
            "bloqueado": 0
        }
        mensagem = (
            f"<b>📡 {box_name}:</b>\n\n"
            "— — — — — — — — — — — — —\n\n"
        )
        for point in points:
            status = point.get("status_name", "N/A").lower()
            if status in status_counts:
                status_counts[status] += 1
            attributes = point.get("attributes", {})
            sinal_base = point.get("verified_signal", "N/A")
            saida = point.get("point_name", "N/A")
            cliente = attributes.get("cod_cli_active", "N/A")
            plano = attributes.get("cod_srv_hsi", "N/A")
            cod_reserva = attributes.get("cod_opportunity")
            status_emoji = status_emojis.get(status, "⚪")
            if status == "em operação":
                sinal_cpe = "N/A"
                cpe_online_status = "Desconhecido ❓"
                if cpe_status and cliente in cpe_status:
                    sinal_cpe = cpe_status[cliente].get("Sinal", "Desconhecido")
                    state = cpe_status[cliente].get("state")
                    cpe_online_status = cf.getState_pretty(state)
                mensagem += (
                    f"<b>🔹 Saída:</b> {saida}\n"
                    f"<b>💡 λ base:</b> {sinal_base}\n"
                    f"<b>👤 Cliente:</b> {cliente}\n"
                    f"<b>📶 Plano:</b> {plano}\n"
                    f"<b>📊 Sinal CPE:</b> {sinal_cpe}\n"
                    f"<b>📟 ONT:</b> {cpe_online_status}\n"
                    f"<b>📌 Status:</b> {status_emoji} {status.title()}\n\n"
                    "— — — — — — — — — — — — —\n\n"
                )
            elif status == "reservado":
                mensagem += (
                    f"<b>🔹 Saída:</b> {saida}\n"
                    f"<b>💡 λ base:</b> {sinal_base}\n"
                    f"<b>👤 Cliente:</b> {cod_reserva}\n"
                    f"<b>📶 Plano:</b> {plano}\n"
                    f"<b>📌 Status:</b> {status_emoji} {status.title()}\n\n"
                    "— — — — — — — — — — — — —\n\n"
                )
        mensagem += "<b>📊 Resumo por status:</b>\n"
        for stat_key in ["disponível", "em operação"]:
            count = status_counts[stat_key]
            emoji = status_emojis.get(stat_key, "⚪")
            mensagem += f"{emoji} {stat_key.title()}: {count}\n"
        for stat_key in ["reservado", "bloqueado"]:
            count = status_counts[stat_key]
            if count > 0:
                emoji = status_emojis.get(stat_key, "⚪")
                mensagem += f"{emoji} {stat_key.title()}: {count}\n"
        return mensagem.strip()
