"""Productor-consumidor real con hilos, semáforos y exclusión mutua.

Los meseros producen pedidos; los baristas los retiran y usan una única
máquina de café. El búfer y la máquina son recursos protegidos distintos.
La traza puede variar entre ejecuciones: depende del planificador de Linux.
"""

from collections import deque
import threading
import time


def validar_config(config):
    if not isinstance(config, dict):
        raise ValueError("La configuración concurrente debe ser un objeto.")
    limites = {"capacidad": (1, 20), "productores": (1, 8),
               "consumidores": (1, 8), "pedidos_por_productor": (1, 30),
               "pausa_ms": (0, 100)}
    for campo, (minimo, maximo) in limites.items():
        valor = config.get(campo)
        if type(valor) is not int or not minimo <= valor <= maximo:
            raise ValueError(f"{campo} debe ser entero entre {minimo} y {maximo}.")
    return {campo: config[campo] for campo in limites}


def ejecutar(config):
    """Finaliza todos los hilos y devuelve traza e invariantes verificables."""
    config = validar_config(config)
    buffer = deque()
    huecos = threading.Semaphore(config["capacidad"])
    disponibles = threading.Semaphore(0)
    mutex = threading.Lock()
    cafetera = threading.Lock()
    inicio = threading.Event()
    cancelar = threading.Event()
    fin = object()
    eventos, producidos, consumidos, errores = [], [], [], []
    max_ocupacion = 0
    pausa = config["pausa_ms"] / 1000

    def registrar(actor, accion, pedido=None):
        # Invocar siempre dentro de mutex para obtener una instantánea coherente.
        eventos.append({"paso": len(eventos) + 1, "actor": actor,
                        "accion": accion, "pedido": pedido,
                        "buffer": ["FIN" if x is fin else x for x in buffer]})

    def adquirir(semaforo):
        # La espera con timeout permite cancelar si un hilo falla.
        while not cancelar.is_set():
            if semaforo.acquire(timeout=0.1):
                return True
        return False

    def insertar(pedido, actor):
        nonlocal max_ocupacion
        if not adquirir(huecos):
            return False
        with mutex:
            buffer.append(pedido)
            max_ocupacion = max(max_ocupacion, len(buffer))
            if pedido is fin:
                registrar(actor, "señal de cierre")
            else:
                producidos.append(pedido)
                registrar(actor, "produce", pedido)
        disponibles.release()
        return True

    def productor(numero):
        for indice in range(1, config["pedidos_por_productor"] + 1):
            if not insertar(f"M{numero}-{indice}", f"Mesero {numero}"):
                return
            if pausa:
                time.sleep(pausa)

    def consumidor(numero):
        actor = f"Barista {numero}"
        while adquirir(disponibles):
            with mutex:
                pedido = buffer.popleft()
                registrar(actor, "cierre" if pedido is fin else "retira",
                          None if pedido is fin else pedido)
            huecos.release()
            if pedido is fin:
                return
            # No se retiene el mutex del búfer mientras se espera la máquina.
            with cafetera:
                with mutex:
                    registrar(actor, "inicia café", pedido)
                if pausa:
                    time.sleep(pausa)
                with mutex:
                    consumidos.append(pedido)
                    registrar(actor, "termina café", pedido)

    def protegido(funcion, numero):
        inicio.wait()
        if cancelar.is_set():
            return
        try:
            funcion(numero)
        except Exception as error:
            with mutex:
                errores.append(f"{threading.current_thread().name}: {error}")
            cancelar.set()

    productores = [threading.Thread(target=protegido, args=(productor, i), name=f"Mesero-{i}")
                   for i in range(1, config["productores"] + 1)]
    consumidores = [threading.Thread(target=protegido, args=(consumidor, i), name=f"Barista-{i}")
                   for i in range(1, config["consumidores"] + 1)]
    iniciados = []
    try:
        for hilo in consumidores + productores:
            hilo.start()
            iniciados.append(hilo)
        inicio.set()
        for hilo in productores:
            hilo.join()
        # Un centinela por consumidor; jamás se confunde con un pedido real.
        if not cancelar.is_set():
            for _ in consumidores:
                if not insertar(fin, "Controlador"):
                    break
        for hilo in consumidores:
            hilo.join()
    finally:
        cancelar.set()
        inicio.set()
        for hilo in iniciados:
            hilo.join()

    if errores:
        raise RuntimeError("Fallo de concurrencia: " + "; ".join(errores))
    esperados = config["productores"] * config["pedidos_por_productor"]
    correcto = (len(producidos) == len(consumidos) == esperados
                and len(set(consumidos)) == esperados
                and set(producidos) == set(consumidos)
                and not buffer and max_ocupacion <= config["capacidad"])
    return {"eventos": eventos, "producidos": producidos, "consumidos": consumidos,
            "esperados": esperados, "capacidad": config["capacidad"],
            "max_ocupacion": max_ocupacion, "buffer_final": list(buffer),
            "correcto": correcto}
