import datetime
import math
import re
from typing import Any, Dict, List


class EH:
    def __init__(self) -> None:
        self.nombre = "E.H (Esteban Hernandez)"
        self.memoria: Dict[str, Any] = {"usuario_nombre": None, "historial": []}

    def _add_historial(self, usuario: str, texto: str, rol: str) -> None:
        self.memoria["historial"].append({"usuario": usuario, "texto": texto, "rol": rol})
        if len(self.memoria["historial"]) > 50:
            self.memoria["historial"] = self.memoria["historial"][25:]

    def _extraer_nombre(self, texto: str) -> str | None:
        patron = r"(?:soy|me llamo|mi nombre es)\s+([A-Za-zÁÉÍÓÚáéíóúÑñ]+)"
        m = re.search(patron, texto, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return None

    def _es_operacion(self, texto: str) -> bool:
        texto = texto.replace(",", ".")
        return bool(re.fullmatch(r"[0-9+\-*/().%\s^]+", texto))

    def _calcular(self, texto: str) -> str:
        expr = texto.replace("^", "**").replace(",", ".")
        permitido = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
        permitido.update({"__builtins": {}})
        try:
            res = eval(expr, permitido, {})
            if isinstance(res, float):
                if abs(res) < 1e-10:
                    res = 0.0
                return str(round(res, 6))
            return str(res)
        except Exception:
            return "No pude resolver esa operación. Usa solo números y + - * / ( ) ^ %"

    def _intencion(self, texto: str) -> str:
        t = texto.lower().strip()
        if any(x in t for x in ["hola", "buenas", "hey"]):
            return "saludo"
        if any(x in t for x in ["tu nombre", "quien eres", "cómo te llamas", "como te llamas"]):
            return "identidad"
        if "hora" in t:
            return "hora"
        if any(x in t for x in ["fecha", "dia", "día"]):
            return "fecha"
        if any(x in t for x in ["calcul", "resuelve", "opera"]):
            return "calculo_texto"
        if self._es_operacion(t):
            return "calculo_directo"
        if any(x in t for x in ["me llamo", "mi nombre es", "soy "]):
            return "presentacion"
        return "libre"

    def responder(self, usuario: str, texto: str) -> str:
        self._add_historial(usuario, texto, "usuario")
        nombre_detectado = self._extraer_nombre(texto)
        if nombre_detectado:
            self.memoria["usuario_nombre"] = nombre_detectado
        intent = self._intencion(texto)
        if intent == "saludo":
            if self.memoria["usuario_nombre"]:
                r = f"Hola {self.memoria['usuario_nombre']}, soy {self.nombre}. ¿En qué te ayudo?"
            else:
                r = f"Hola, soy {self.nombre}. ¿Cómo te llamas y en qué te ayudo?"
        elif intent == "identidad":
            r = f"Soy {self.nombre}. Puedo decirte la hora/fecha y ayudarte con cálculos básicos."
        elif intent == "hora":
            ahora = datetime.datetime.now().strftime("%H:%M:%S")
            r = f"La hora actual es {ahora}."
        elif intent == "fecha":
            hoy = datetime.date.today().strftime("%Y-%m-%d")
            r = f"La fecha de hoy es {hoy}."
        elif intent == "calculo_texto":
            nums = re.findall(r"[0-9+\-*/().%\s^]+", texto)
            if nums:
                r = self._calcular(nums[0])
            else:
                r = "Indica la operación. Ejemplo: 2+2*3"
        elif intent == "calculo_directo":
            r = self._calcular(texto)
        elif intent == "presentacion":
            if self.memoria["usuario_nombre"]:
                r = f"Encantado, {self.memoria['usuario_nombre']}. ¿Qué necesitas hoy?"
            else:
                r = "Encantado. ¿Qué necesitas hoy?"
        else:
            if self.memoria["usuario_nombre"]:
                r = f"Te escucho, {self.memoria['usuario_nombre']}. Puedes pedirme hora, fecha o un cálculo."
            else:
                r = "Te escucho. Puedes pedirme hora, fecha o un cálculo."
        self._add_historial("E.H", r, "asistente")
        return r
