# E.H (Esteban Hernandez)

Asistente conversacional minimalista en Python, sin dependencias externas.

## Requisitos
- Python 3.10+

## Ejecutar
```bash
python main.py
```

## Capacidades
- Saludo e identidad.
- Hora y fecha actuales.
- Cálculos simples (ej.: `2+2`, `3^2 + 5*(4-1)`).
- Memoria breve de tu nombre y del historial reciente.

## Comandos
- Salir del chat: `salir`, `exit` o `quit`.

## Estructura
- `eh.py`: clase `EH` con NLU básico, memoria y herramientas.
- `main.py`: bucle de chat en consola.
