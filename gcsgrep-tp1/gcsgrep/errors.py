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


class ErrorDeRedAlListar(ErrorDeAcceso):
    """El listado no obtuvo una respuesta HTTP completa, o recibió un `5xx`
    (definición de "error de red" de NFR-2). Aborta: no hay objetos sobre los que
    seguir. No se reintenta (ADR-0016)."""

    def __init__(self, bucket: str):
        self.bucket = bucket
        super().__init__(
            f"error de red al listar 'gs://{bucket}'. "
            f"No se reintenta: volvé a correr el comando."
        )


_COMANDO_DE_CREDENCIALES = "gcloud auth application-default login"


class SinCredenciales(ErrorDeAcceso):
    """ADC no resolvió ninguna credencial (FR-15)."""

    def __init__(self):
        super().__init__(
            f"no se encontraron credenciales de Google Cloud. "
            f"Obtenelas con: {_COMANDO_DE_CREDENCIALES}"
        )


class CredencialesInvalidas(ErrorDeAcceso):
    """Hay credenciales pero no producen un token (FR-26), o GCS responde `401`
    al listar (FR-28). Mensaje distinto del de `SinCredenciales` a propósito:
    "no se encontraron" mandaría a buscar algo que sí está."""

    def __init__(self):
        super().__init__(
            f"credenciales inválidas o vencidas. "
            f"Renovalas con: {_COMANDO_DE_CREDENCIALES}"
        )


class ErrorDeObjeto(Exception):
    """Un objeto puntual no se pudo leer (FR-6, FR-13, FR-21).

    **No** hereda de `ErrorDeAcceso` a propósito: no aborta la corrida. `core` lo
    convierte en un aviso por stderr y sigue con el objeto siguiente; `cli` lo
    cuenta para la precedencia de exit codes de BR-3.
    """

    def __init__(self, bucket: str, object_name: str, mensaje: str):
        self.bucket = bucket
        self.object_name = object_name
        super().__init__(mensaje)


class ObjetoSinPermiso(ErrorDeObjeto):
    """GCS respondió `403`, o `401` sobre un objeto (FR-6, spec v1.6)."""

    def __init__(self, bucket: str, object_name: str):
        super().__init__(
            bucket, object_name,
            f"sin permiso para leer 'gs://{bucket}/{object_name}'. Se sigue con el resto.",
        )


class ErrorDeRedAlLeer(ErrorDeObjeto):
    """Error de red (NFR-2) al abrir o a mitad de lectura de un objeto (FR-13).
    Los matches ya emitidos quedan; el objeto no se vuelve a abrir."""

    def __init__(self, bucket: str, object_name: str):
        super().__init__(
            bucket, object_name,
            f"error de red al leer 'gs://{bucket}/{object_name}'. Se sigue con el resto.",
        )


class ObjetoNoEncontrado(ErrorDeObjeto):
    """El objeto estaba en el listado y GCS responde `404` al ir a leerlo (FR-21).

    Distinto de `ObjetoSinPermiso`: acá no hay nada que revisar en IAM. Es la
    ventana de ADR-0010 (el bucket cambia mientras se lo recorre) manifestándose
    como un borrado en vez de una modificación. Hasta la Iteración 1 heredaba de
    `ErrorDeAcceso` y abortaba la corrida.
    """

    def __init__(self, bucket: str, object_name: str):
        super().__init__(
            bucket, object_name,
            f"el objeto 'gs://{bucket}/{object_name}' ya no existe "
            f"(se borró mientras la búsqueda estaba en curso). Se sigue con el resto.",
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
