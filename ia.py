"""
E.H - Asistente AI (Esteban Hernandez)
Archivo: eh_assistant.py
Descripción: Un asistente conversacional en Python llamado "E.H".

Características:
- Modo local (reglas simples, respuesta por plantilla).
- Modo GPT (usa OpenAI si el usuario configura OPENAI_API_KEY en variables de entorno).
- Memoria local en ./eh_memory.json (guarda notas cortas: preferencias, recordatorios, datos "de usuario").
- Plugins: calculadora simple, recordatorio, búsqueda web (si se instala y configura).
- Interfaz: CLI interactiva y función para integrarlo en otros proyectos.

Instrucciones:
- Ejecutar: python eh_assistant.py
- Para habilitar modo GPT, exporta OPENAI_API_KEY y opcionalmente setea EH_USE_GPT=1
- Memoria se guarda automáticamente.

NOTA: Este archivo no envia nada por internet por defecto. Si habilitas GPT, el código llamará a la API de OpenAI y necesitarás conectividad.
"""

import os
import json
import time
import readline
import math
from typing import Optional, Dict, Any

# Optional: import OpenAI only if user enables GPT mode
try:
    import openai
except Exception:
    openai = None

MEMORY_FILE = "eh_memory.json"


class Memory:
    """Simple JSON-backed memory for E.H."""

    def __init__(self, path: str = MEMORY_FILE):
        self.path = path
        self._data = {"notes": {}, "prefs": {}}
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                print("[E.H] Aviso: no se pudo leer la memoria; inicializando nueva memoria.")

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[E.H] Error al guardar la memoria: {e}")

    def set_note(self, key: str, value: str):
        self._data.setdefault("notes", {})[key] = {"text": value, "ts": time.time()}
        self.save()

    def get_note(self, key: str) -> Optional[Dict[str, Any]]:
        return self._data.get("notes", {}).get(key)

    def delete_note(self, key: str):
        if key in self._data.get("notes", {}):
            del self._data["notes"][key]
            self.save()
            return True
        return False

    def list_notes(self):
        return self._data.get("notes", {})

    def set_pref(self, key: str, value: Any):
        self._data.setdefault("prefs", {})[key] = value
        self.save()

    def get_pref(self, key: str, default=None):
        return self._data.get("prefs", {}).get(key, default)


class EHAssistant:
    def __init__(self, name: str = "E.H", use_gpt: bool = False):
        self.name = name
        self.memory = Memory()
        self.use_gpt = use_gpt and (openai is not None) and bool(os.getenv("OPENAI_API_KEY"))
        if self.use_gpt:
            openai.api_key = os.getenv("OPENAI_API_KEY")
        print(f"[{self.name}] Iniciado. Modo GPT={'ON' if self.use_gpt else 'OFF'}")

    # ------------------ Core conversational layer ------------------
    def respond(self, user_input: str) -> str:
        """Main response dispatcher. """
        user_input_clean = user_input.strip().lower()

        # Short commands
        if user_input_clean in ("hola", "hi", "hola eh", "buenas", "buenos dias"):
            return self._greet()
        if user_input_clean.startswith("recordar:"):
            key, _, val = user_input.partition(":")
            note_key = f"note_{int(time.time())}"
            self.memory.set_note(note_key, val.strip())
            return f"He guardado tu nota con id '{note_key}'."
        if user_input_clean.startswith("nota " ):
            # nota <id>
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2:
                note = self.memory.get_note(parts[1])
                return json.dumps(note, ensure_ascii=False, indent=2) if note else "No encontré esa nota."

        # Utility intents
        if user_input_clean.startswith("calc ") or user_input_clean.startswith("calcular "):
            expr = user_input.split(maxsplit=1)[1]
            return self._safe_eval(expr)

        if user_input_clean.startswith("guardar pref "):
            try:
                _, _, rest = user_input.partition("guardar pref ")
                k, v = rest.split("=", 1)
                self.memory.set_pref(k.strip(), v.strip())
                return f"Preferencia '{k.strip()}' guardada."
            except Exception:
                return "Formato inválido. Uso: guardar pref <clave>=<valor>"

        if user_input_clean in ("mis notas", "listar notas"):
            notes = self.memory.list_notes()
            if not notes:
                return "No tienes notas guardadas."
            out = []
            for k, v in notes.items():
                ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(v['ts'])) if 'ts' in v else ''
                out.append(f"{k} ({ts}): {v['text']}")
            return "\n".join(out)

        # If GPT mode is enabled, prefer it for open-ended questions
        if self.use_gpt:
            try:
                return self._call_gpt(user_input)
            except Exception as e:
                # fallback
                print(f"[E.H] Error GPT: {e}")

        # Fallback local reply
        return self._local_reply(user_input)

    def _greet(self) -> str:
        user_name = self.memory.get_pref("user_name") or "amigo"
        return f"Hola {user_name}, soy {self.name}. ¿En qué puedo ayudarte hoy?"

    def _local_reply(self, text: str) -> str:
        # Very simple rule-based responses
        t = text.lower()
        if "ayuda" in t or "qué puedes hacer" in t or "que puedes hacer" in t:
            return ("Puedo: calcular expresiones (calc <expr>), guardar notas (recordar: tu nota), "
                    "gestionar preferencias (guardar pref <k>=<v>), y responder preguntas simples. "
                    "Activa el modo GPT para respuestas más completas.")
        if "gracias" in t or "muchas gracias" in t:
            return "De nada — siempre aquí para ayudar."
        if "quién eres" in t or "como te llamas" in t:
            return f"Soy {self.name}, tu asistente personal."
        if "hora" in t:
            return time.strftime("Son las %H:%M:%S del %Y-%m-%d", time.localtime())
        return "Lo siento, no sé eso todavía. Puedes pedirme que active el modo GPT para respuestas más complejas."

    # ------------------ Utilities ------------------
    def _safe_eval(self, expr: str) -> str:
        """Evaluate math expressions safely. Allows numbers and math functions only."""
        allowed_names = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
        allowed_names.update({"abs": abs, "round": round})
        try:
            code = compile(expr, "<string>", "eval")
            for name in code.co_names:
                if name not in allowed_names:
                    return "Expresión no permitida: uso de nombres no seguros."
            result = eval(code, {"__builtins__": {}}, allowed_names)
            return str(result)
        except Exception as e:
            return f"Error al calcular: {e}"

    def _call_gpt(self, prompt: str) -> str:
        """Call OpenAI's ChatCompletion (if openai is configured). Simple wrapper."""
        if openai is None:
            raise RuntimeError("OpenAI library no disponible.")
        # Build a small system prompt
        system = (
            f"Eres {self.name}, un asistente útil y conciso. Responde en el idioma del usuario (español). "
            "Si el usuario pide guardar una nota, explica cómo usar 'recordar: <texto>'." 
        )
        response = openai.ChatCompletion.create(
            model=os.getenv("EH_MODEL", "gpt-4o-mini") if os.getenv("EH_MODEL") else "gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.6,
        )
        text = response.choices[0].message.content.strip()
        return text


# ------------------ CLI Interface ------------------

def repl():
    use_gpt = bool(os.getenv("EH_USE_GPT", "0") in ("1", "true", "True"))
    assistant = EHAssistant(use_gpt=use_gpt)
    print("Escribe 'salir' para terminar. Usa 'ayuda' para ver comandos básicos.")
    while True:
        try:
            user_input = input("Tú: ")
        except (EOFError, KeyboardInterrupt):
            print("\nAdiós.")
            break
        if not user_input:
            continue
        if user_input.strip().lower() in ("salir", "exit", "quit"):
            print("Adiós — sesión terminada.")
            break
        # Quick special command: set username
        if user_input.startswith("setname "):
            name = user_input.split(maxsplit=1)[1]
            assistant.memory.set_pref("user_name", name)
            print(f"{assistant.name}: Listo, te llamaré {name} a partir de ahora.")
            continue
        resp = assistant.respond(user_input)
        print(f"{assistant.name}: {resp}")


if __name__ == "__main__":
    repl()
