"""Datos de un proceso simulado; tiempos enteros en ticks."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProcessControlBlock:
    pid: str
    nombre: str
    llegada: int
    rafaga: int
    prioridad: int
    restante: int = field(init=False)
    primer_inicio: Optional[int] = field(default=None, init=False)
    finalizacion: Optional[int] = field(default=None, init=False)

    def __post_init__(self):
        if not isinstance(self.pid, str) or not self.pid.strip():
            raise ValueError("Cada proceso necesita un pid de texto no vacío.")
        if not isinstance(self.nombre, str) or not self.nombre.strip():
            raise ValueError("Cada proceso necesita un nombre no vacío.")
        for campo, minimo in (("llegada", 0), ("rafaga", 1), ("prioridad", 1)):
            valor = getattr(self, campo)
            if type(valor) is not int or valor < minimo:
                raise ValueError(f"{self.pid}: {campo} debe ser entero >= {minimo}.")
        self.restante = self.rafaga

    @classmethod
    def desde_diccionario(cls, datos):
        if not isinstance(datos, dict):
            raise ValueError("Cada proceso debe ser un objeto JSON.")
        campos = ("pid", "nombre", "llegada", "rafaga", "prioridad")
        if any(campo not in datos for campo in campos):
            raise ValueError("Proceso incompleto: se requiere " + ", ".join(campos))
        return cls(**{campo: datos[campo] for campo in campos})

    def metricas(self):
        if self.finalizacion is None or self.primer_inicio is None:
            raise ValueError("El proceso todavía no terminó.")
        retorno = self.finalizacion - self.llegada
        return {
            "pid": self.pid, "nombre": self.nombre,
            "llegada": self.llegada, "rafaga": self.rafaga,
            "prioridad": self.prioridad, "inicio": self.primer_inicio,
            "fin": self.finalizacion, "retorno": retorno,
            "espera": retorno - self.rafaga,
            "respuesta": self.primer_inicio - self.llegada,
        }
