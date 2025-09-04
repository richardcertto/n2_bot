import textwrap
from math import log10


class ConvertFuncs:
    def __init__(self):
        pass

    def convert_uptime(self, val):
        try:
            seconds = float(val)
            days, remainder = divmod(seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, _ = divmod(remainder, 60)
            parts = []
            if days:
                parts.append(f"{int(days)}d")
            if hours:
                parts.append(f"{int(hours)}h")
            if minutes or not parts:
                parts.append(f"{int(minutes)}m")
            return ' '.join(parts)
        except (ValueError, TypeError) as e:
            return str(val)

    def eval_power(self, val):
        try:
            if val is None:
                return 'Sem dados'
            val_str = str(val).strip()
            if len(val_str) == 2:
                val = float('0.00' + val_str)
            else:
                val = float('0.0' + val_str)
            power_dbm = 10 * log10(val)
            return round(power_dbm, 2)
        except (ValueError, TypeError):
            return 'Valor inválido'

    def eval_power_pretty(self, val):
        try:
            if val is None:
                return "Sem dados ❌"
            val_str = str(val).strip().replace('dBm', '')
            temp_val = float(val_str)
            if temp_val > -24:
                return f"{temp_val:.2f} dBm ✅"
            else:
                return f"{temp_val:.2f} dBm ⚠️"
        except (ValueError, TypeError):
            return f"{val} ❌"

    def temp_f_2_c(self, val, model):
        if val is None:
            return '0'
        try:
            if model == 'ONT142NG':
                fahrenheit = int(val) / 100
                celsius = (fahrenheit - 32) * 5 / 9
                return f"{int(round(celsius))}"
            else:
                return str(val)
        except (ValueError, TypeError):
            return '0'

    def getState_pretty(self, state):
        CPEStateEnumeration = {
            0: ['ONLINE', '✅'],
            1: ['Pendente', '⚠️'],
            2: ['Configurando', '⏛'],
            3: ['Config Inicial', '➡️'],
            4: ['OFFLINE', '❌'],
            5: ['OFFLINE', '❌'],
            6: ['OFFLINE', '❌'],
            7: ['Falha na config', '❗'],
            8: ['Baixando firmware', '☁️'],
            9: ['Reiniciando...', '⚡']
        }
        try:
            label, emoji = CPEStateEnumeration[int(state)]
            return f"{label} {emoji}"
        except (KeyError, ValueError, TypeError):
            return "Cliente Cancelado ❌"
