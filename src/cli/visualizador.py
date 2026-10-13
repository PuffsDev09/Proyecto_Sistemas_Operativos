"""Tablas ASCII sin dependencias externas ni lógica de los algoritmos."""


def tabla(encabezados, filas):
    def celda(valor):
        # Evita que saltos o caracteres de control de un JSON rompan la tabla.
        return "".join(c if c.isprintable() else " " for c in str(valor))
    contenido = [[celda(x) for x in encabezados]]
    contenido.extend([[celda(x) for x in fila] for fila in filas])
    anchos = [max(len(fila[i]) for fila in contenido) for i in range(len(encabezados))]
    borde = "+" + "+".join("-" * (ancho + 2) for ancho in anchos) + "+"
    print(borde)
    for indice, fila in enumerate(contenido):
        print("| " + " | ".join(valor.ljust(ancho) for valor, ancho in zip(fila, anchos)) + " |")
        if indice == 0:
            print(borde)
    print(borde)


def procesos(resultado):
    print(f"\nPlanificación: {resultado['algoritmo']} | Tiempos en ticks")
    tabla(["PID", "Orden", "Llegada", "Ráfaga", "Prior.", "Inicio", "Fin",
           "Espera", "Respuesta", "Retorno"], [
        [p[campo] for campo in ("pid", "nombre", "llegada", "rafaga", "prioridad",
                               "inicio", "fin", "espera", "respuesta", "retorno")]
        for p in resultado["procesos"]])
    print("Cronograma (inicio incluido, fin excluido):")
    tabla(["Inicio", "Fin", "CPU"], [
        [tramo["inicio"], tramo["fin"], tramo["pid"] if tramo["pid"] is not None else "OCIOSA"]
        for tramo in resultado["cronograma"]])
    medias = resultado["promedios"]
    print(f"Promedios: espera={medias['espera']:.2f}, respuesta={medias['respuesta']:.2f}, "
          f"retorno={medias['retorno']:.2f}")


def comparar_procesos(resultados):
    print("\nComparación sobre los mismos procesos:")
    tabla(["Algoritmo", "Espera media", "Respuesta media", "Retorno medio"], [
        [r["algoritmo"]] + [f"{r['promedios'][campo]:.2f}"
                            for campo in ("espera", "respuesta", "retorno")]
        for r in resultados])


def syscalls(resultado):
    print("\nCreación de procesos Linux (no es una simulación matemática):")
    tabla(["Dato", "Valor"], [
        ["PID del padre", resultado["pid_padre"]],
        ["PID obtenido con fork", resultado["pid_hijo"]],
        ["PID después de execvp", resultado["pid_tras_exec"]],
        ["Padre observado por el hijo", resultado["ppid_tras_exec"]],
        ["PID recogido por wait", resultado["pid_recogido"]],
        ["Código de salida", resultado["codigo_salida"]]])
    print(resultado["mensaje"])
    print("fork crea el hijo; execvp reemplaza su programa conservando el PID;")
    print("wait recoge su estado de terminación.")


def sincronizacion(resultado):
    print("\nTraza recogida durante la ejecución concurrente:")
    tabla(["Paso", "Actor", "Acción", "Pedido", "Bandeja"], [
        [e["paso"], e["actor"], e["accion"], e["pedido"] or "-",
         ", ".join(e["buffer"]) or "vacía"] for e in resultado["eventos"]])
    tabla(["Comprobación", "Resultado"], [
        ["Pedidos esperados", resultado["esperados"]],
        ["Producidos", len(resultado["producidos"])],
        ["Consumidos", len(resultado["consumidos"])],
        ["Máxima ocupación / capacidad", f"{resultado['max_ocupacion']} / {resultado['capacidad']}"],
        ["Búfer vacío al terminar", "Sí" if not resultado["buffer_final"] else "No"],
        ["Sin pérdidas, duplicados ni desbordamiento", "OK" if resultado["correcto"] else "FALLO"]])
    print("El orden de los hilos puede cambiar en otra ejecución; las invariantes deben mantenerse.")


def memoria(resultado):
    print(f"\nReemplazo: {resultado['algoritmo']} | '-' representa un marco vacío")
    n = len(resultado["traza"][0]["marcos"])
    filas = []
    for evento in resultado["traza"]:
        filas.append([evento["paso"], evento["pagina"]]
                     + ["-" if p is None else p for p in evento["marcos"]]
                     + ["ACIERTO" if evento["acierto"] else "FALLO",
                        "-" if evento["victima"] is None else evento["victima"]])
    tabla(["Paso", "Página"] + [f"Marco {i}" for i in range(n)] + ["Acceso", "Sale"], filas)
    print(f"Fallos: {resultado['fallos']} | Aciertos: {resultado['aciertos']} | "
          f"Tasa de fallos: {resultado['tasa_fallos']:.2%}")


def comparar_memoria(resultados):
    print("\nComparación con los mismos marcos y referencias:")
    tabla(["Algoritmo", "Fallos", "Aciertos", "Tasa de fallos"], [
        [r["algoritmo"], r["fallos"], r["aciertos"], f"{r['tasa_fallos']:.2%}"]
        for r in resultados])
