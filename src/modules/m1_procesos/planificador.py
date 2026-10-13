"""CPU única, una ráfaga por proceso, sin E/S ni coste de contexto.

SJF y Prioridad no son expropiativos. Menor número = mayor prioridad.
Empates: llegada y posición en la lista de entrada. El reloj es simulado.
"""

from collections import deque
from core.pcb import ProcessControlBlock

ALGORITMOS = ("FCFS", "SJF", "RR", "PRIORIDAD")


def validar_datos(datos):
    if not isinstance(datos, dict):
        raise ValueError("La configuración de procesos debe ser un objeto.")
    registros = datos.get("procesos")
    if not isinstance(registros, list) or not 1 <= len(registros) <= 100:
        raise ValueError("Se requieren entre 1 y 100 procesos.")
    quantum = datos.get("quantum")
    if type(quantum) is not int or quantum <= 0:
        raise ValueError("El quantum debe ser un entero positivo.")
    procesos = [ProcessControlBlock.desde_diccionario(p) for p in registros]
    if len({p.pid for p in procesos}) != len(procesos):
        raise ValueError("Los pid deben ser únicos.")
    # Límite de la demostración: evita generar millones de filas en la CLI.
    turnos = sum((p.rafaga + quantum - 1) // quantum for p in procesos)
    if turnos > 10000:
        raise ValueError("Reduzca ráfagas o aumente quantum: máximo 10000 turnos RR.")
    return procesos, quantum


def simular(datos, algoritmo="FCFS"):
    """Devuelve métricas y cronograma nuevos; nunca modifica los datos recibidos."""
    if algoritmo not in ALGORITMOS:
        raise ValueError("Algoritmo de planificación desconocido.")
    procesos, quantum = validar_datos(datos)
    orden = {p.pid: i for i, p in enumerate(procesos)}
    pendientes = sorted(procesos, key=lambda p: (p.llegada, orden[p.pid]))
    listos = deque()
    cronograma = []
    tiempo = 0
    siguiente = 0

    def admitir():
        nonlocal siguiente
        while siguiente < len(pendientes) and pendientes[siguiente].llegada <= tiempo:
            listos.append(pendientes[siguiente])
            siguiente += 1

    while siguiente < len(pendientes) or listos:
        admitir()
        if not listos:
            llegada = pendientes[siguiente].llegada
            cronograma.append({"pid": None, "inicio": tiempo, "fin": llegada})
            tiempo = llegada
            admitir()

        if algoritmo in ("FCFS", "RR"):
            proceso = listos.popleft()
        else:
            campo = "rafaga" if algoritmo == "SJF" else "prioridad"
            proceso = min(listos, key=lambda p: (getattr(p, campo), p.llegada, orden[p.pid]))
            listos.remove(proceso)

        if proceso.primer_inicio is None:
            proceso.primer_inicio = tiempo
        duracion = min(quantum, proceso.restante) if algoritmo == "RR" else proceso.restante
        cronograma.append({"pid": proceso.pid, "inicio": tiempo, "fin": tiempo + duracion})
        tiempo += duracion
        proceso.restante -= duracion

        # En el límite del quantum entran primero las nuevas llegadas.
        admitir()
        if proceso.restante:
            listos.append(proceso)
        else:
            proceso.finalizacion = tiempo

    filas = [p.metricas() for p in procesos]
    promedios = {
        campo: sum(fila[campo] for fila in filas) / len(filas)
        for campo in ("espera", "respuesta", "retorno")
    }
    return {"algoritmo": algoritmo, "procesos": filas,
            "cronograma": cronograma, "promedios": promedios,
            "tiempo_total": tiempo}


def comparar(datos):
    return [simular(datos, algoritmo) for algoritmo in ALGORITMOS]
