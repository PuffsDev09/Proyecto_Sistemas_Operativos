"""Demostración Linux real, separada del reloj del planificador.

El hijo ejecuta otro intérprete Python. Su informe viaja por una tubería;
solo la CLI muestra el resultado. Ejecutar desde el controlador sin otros
procesos hijos activos y una vez que hayan terminado los hilos de M2.
"""

import json
import os
import sys
import threading


def demostrar():
    if not sys.platform.startswith("linux") or not hasattr(os, "fork"):
        raise RuntimeError("Esta demostración requiere Linux (Ubuntu o WSL).")
    if threading.active_count() != 1:
        raise RuntimeError("Finalice los hilos antes de ejecutar fork.")

    lectura, escritura = os.pipe()
    os.set_inheritable(escritura, True)
    padre = os.getpid()
    try:
        hijo = os.fork()
    except OSError:
        os.close(lectura)
        os.close(escritura)
        raise

    if hijo == 0:
        try:
            os.close(lectura)
            # execvp reemplaza al hijo; el PID permanece igual.
            codigo = (
                "import json, os, sys; "
                "fd = int(sys.argv[1]); "
                "dato = {'pid': os.getpid(), 'ppid': os.getppid(), "
                "'mensaje': 'Nuevo programa Python ejecutado mediante execvp'}; "
                "os.write(fd, json.dumps(dato).encode('utf-8')); os.close(fd)"
            )
            os.execvp(sys.executable, [sys.executable, "-I", "-c", codigo, str(escritura)])
        except BaseException as error:
            try:
                os.write(escritura, json.dumps({"error": str(error)}).encode("utf-8"))
            finally:
                os._exit(127)

    os.close(escritura)
    # Leer antes de esperar evita bloquear al hijo por una tubería llena.
    try:
        with os.fdopen(lectura, "rb") as canal:
            contenido = canal.read()
    finally:
        while True:
            pid_recogido, estado = os.wait()
            if pid_recogido == hijo:
                break

    codigo_salida = os.waitstatus_to_exitcode(estado)
    if codigo_salida != 0:
        raise RuntimeError(f"El hijo terminó con estado {codigo_salida}: "
                           + contenido.decode("utf-8", errors="replace"))
    informe = json.loads(contenido.decode("utf-8"))
    return {"pid_padre": padre, "pid_hijo": hijo, "pid_tras_exec": informe["pid"],
            "ppid_tras_exec": informe["ppid"], "pid_recogido": pid_recogido,
            "codigo_salida": codigo_salida, "mensaje": informe["mensaje"]}
