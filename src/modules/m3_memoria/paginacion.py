"""Reemplazo de páginas con marcos inicialmente vacíos."""

from collections import deque
from core.pagina import Pagina

ALGORITMOS = ("FIFO", "LRU", "OPTIMO")


def validar_datos(datos):
    if not isinstance(datos, dict):
        raise ValueError("La configuración de memoria debe ser un objeto.")
    marcos = datos.get("marcos")
    referencias = datos.get("referencias")
    if type(marcos) is not int or not 1 <= marcos <= 20:
        raise ValueError("La cantidad de marcos debe estar entre 1 y 20.")
    if not isinstance(referencias, list) or not 1 <= len(referencias) <= 1000:
        raise ValueError("Ingrese entre 1 y 1000 referencias de páginas.")
    return marcos, [Pagina(numero) for numero in referencias]


def simular(datos, algoritmo="FIFO"):
    """Devuelve una copia de los marcos en cada acceso y sus métricas."""
    if algoritmo not in ALGORITMOS:
        raise ValueError("Algoritmo de reemplazo desconocido.")
    cantidad, referencias = validar_datos(datos)
    marcos = [None] * cantidad
    cola_fifo = deque()
    ultimo_uso = {}
    traza = []
    fallos = 0

    for paso, pagina in enumerate(referencias):
        acierto = pagina in marcos
        victima = None
        if not acierto:
            fallos += 1
            if None in marcos:
                indice = marcos.index(None)
            elif algoritmo == "FIFO":
                indice = cola_fifo.popleft()
            elif algoritmo == "LRU":
                indice = min(range(cantidad), key=lambda i: ultimo_uso[marcos[i]])
            else:
                # Óptimo conoce toda la secuencia futura (referencia teórica).
                def proximo_uso(i):
                    for futuro in range(paso + 1, len(referencias)):
                        if referencias[futuro] == marcos[i]:
                            return futuro
                    return float("inf")
                indice = max(range(cantidad), key=proximo_uso)
            if marcos[indice] is not None:
                victima = marcos[indice].numero
            marcos[indice] = pagina
            if algoritmo == "FIFO":
                cola_fifo.append(indice)
        ultimo_uso[pagina] = paso
        traza.append({"paso": paso + 1, "pagina": pagina.numero,
                      "acierto": acierto, "victima": victima,
                      "marcos": [p.numero if p is not None else None for p in marcos]})

    return {"algoritmo": algoritmo, "traza": traza, "fallos": fallos,
            "aciertos": len(referencias) - fallos, "total": len(referencias),
            "tasa_fallos": fallos / len(referencias)}


def comparar(datos):
    return [simular(datos, algoritmo) for algoritmo in ALGORITMOS]
