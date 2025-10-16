from eh import EH


def main() -> None:
    agente = EH()
    print("Bienvenido. Soy E.H (Esteban Hernandez). Escribe 'salir' para terminar.")
    while True:
        try:
            texto = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSaliendo. ¡Hasta luego!")
            break
        if texto.lower() in {"salir", "exit", "quit"}:
            print("Hasta luego.")
            break
        respuesta = agente.responder(usuario="usuario", texto=texto)
        print(f"E.H: {respuesta}")


if __name__ == "__main__":
    main()
