"""Errores de dominio de gcsgrep.

Existe para que `cli` pueda distinguir fallos de acceso a GCS **sin importar
`google.api_core`**: la única capa que conoce el SDK sigue siendo `gcs` (ver
ADR-0013 y la arquitectura `cli → core → gcs` del README).

El mensaje de cada error está escrito para que `cli` lo imprima tal cual por
stderr: es texto para quien corrió el comando, no la representación de una
excepción de librería (NFR-2, NFR-3).
"""


class ErrorDeAcceso(Exception):
    """Fallo al acceder a GCS que aborta la corrida con exit 2.

    `cli` imprime `str(exc)` y sale con `2`. Cualquier subclase nueva hereda ese
    comportamiento sin tocar `cli`.
    """


class BucketNoEncontrado(ErrorDeAcceso):
    """El bucket no existe (FR-12). Quien lo lea tiene que revisar el nombre."""

    def __init__(self, bucket: str):
        self.bucket = bucket
        super().__init__(
            f"el bucket 'gs://{bucket}' no existe. Revisá el nombre."
        )


class AccesoDenegado(ErrorDeAcceso):
    """Sin permiso sobre el bucket o el objeto (FR-12).

    Mensaje distinto del de `BucketNoEncontrado` a propósito: "no existe" manda a
    revisar el nombre, "sin permiso" manda a revisar IAM. Son acciones distintas.
    """

    def __init__(self, bucket: str, object_name: str = ""):
        self.bucket = bucket
        self.object_name = object_name
        destino = f"gs://{bucket}/{object_name}" if object_name else f"gs://{bucket}"
        super().__init__(
            f"sin permiso para acceder a '{destino}'. "
            f"Revisá los permisos de tus credenciales (IAM)."
        )


class ObjetoNoEncontrado(ErrorDeAcceso):
    """El objeto estaba en el listado y ya no está al ir a leerlo.

    Distinto de `AccesoDenegado`: acá no hay nada que revisar en IAM. Es la
    ventana de ADR-0010 (el bucket cambia mientras se lo recorre) manifestándose
    como un borrado en vez de una modificación.
    """

    def __init__(self, bucket: str, object_name: str):
        self.bucket = bucket
        self.object_name = object_name
        super().__init__(
            f"el objeto 'gs://{bucket}/{object_name}' ya no existe "
            f"(se borró mientras la búsqueda estaba en curso)."
        )


class TopeExcedido(Exception):
    """El prefijo tiene más objetos que el tope del guardrail (BR-2).

    **No** hereda de `ErrorDeAcceso` a propósito: ese sale con exit `2` (error), y
    esto sale con `1`. No es un fallo — es la herramienta negándose a hacer algo
    caro que nadie le pidió explícitamente (ADR-0006).
    """

    def __init__(self, encontrados: int, tope: int):
        self.encontrados = encontrados
        self.tope = tope
        super().__init__(
            f"el prefijo tiene {encontrados} objetos y el tope es {tope}: "
            f"no se leyó ninguno. "
            f"Acotá el prefijo, subí el tope con --max N, o quitalo con --max 0."
        )
