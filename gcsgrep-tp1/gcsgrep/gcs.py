"""Única capa que habla con la API real de Google Cloud Storage.

Usa Application Default Credentials (ver gcsgrep-base-context.md, punto 2):
no se pide ni se acepta ningún flag de credenciales explícito.

Es también el único lugar que conoce las excepciones del SDK: las traduce a los
errores de dominio de `errors`, para que `cli` pueda reportarlas sin importar
`google.api_core` (ADR-0013).
"""

import os
import warnings
from contextlib import contextmanager
from typing import Iterator, Optional

# NFR-3: en una corrida sin errores stderr queda vacío. `google-api-core` y
# `google-auth` emiten `FutureWarning` **al importarse** cuando el Python ya no
# tiene soporte (3.9), o sea en toda corrida. Es un aviso sobre el runtime, no
# sobre la búsqueda: se silencia solo esa categoría y solo para módulos
# `google.*`, y antes de importarlos. Encontrado por CI el 2026-10-02 (VC-35).
warnings.filterwarnings("ignore", category=FutureWarning, module=r"google\.")

import requests  # noqa: E402 — después del filtro, a propósito
from google.api_core import exceptions as gcs_exceptions
from google.auth import exceptions as auth_exceptions
from google.cloud import storage

from . import errors

#: "Error de red", con la definición única de NFR-2: la operación no obtuvo una
#: respuesta HTTP completa (conexión rechazada o cortada, timeout) o recibió un
#: `5xx`. Un `4xx` nunca está acá: la red funcionó y la respuesta fue explícita.
_ERRORES_DE_RED = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.ChunkedEncodingError,
    auth_exceptions.TransportError,
    ConnectionError,
    TimeoutError,
    gcs_exceptions.ServerError,
)

#: Tamaño de bloque del lector de la librería cliente (NFR-1, spec v1.6). El
#: default de `BlobReader` es ~40 MiB y leyendo a través de él el pico medido fue
#: de ≈120 MiB; con 1 MiB queda bajo el umbral de 20 MiB (VC-14 (c)). Costo: más
#: pedidos HTTP por objeto (1 por MiB), que pesa en la latencia real, no en NFR-4.
CHUNK_SIZE = 1024 * 1024

_client: Optional[storage.Client] = None


def _get_client() -> storage.Client:
    global _client
    if _client is None:
        _client = storage.Client()
    return _client


def _crear_cliente() -> storage.Client:
    """Crea el cliente traduciendo la falla de ADC (FR-15 / FR-26).

    `DefaultCredentialsError` cubre los dos casos: no hay ninguna fuente, o la
    fuente que `GOOGLE_APPLICATION_CREDENTIALS` nombra no sirve (archivo
    inexistente o mal formado). Si la variable está definida, ADC encontró una
    fuente y lo que falla es esa fuente: credenciales inválidas, no ausentes.
    """
    try:
        return _get_client()
    except auth_exceptions.DefaultCredentialsError:
        if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            raise errors.CredencialesInvalidas() from None
        raise errors.SinCredenciales() from None


def list_objects(bucket: str, prefix: str) -> Iterator[str]:
    client = _crear_cliente()
    try:
        # `retry=None`: 0 reintentos también dentro del SDK (NFR-2, ADR-0016).
        for blob in client.list_blobs(bucket, prefix=prefix, retry=None):
            yield blob.name
    except gcs_exceptions.NotFound:
        raise errors.BucketNoEncontrado(bucket) from None
    except gcs_exceptions.Forbidden:
        raise errors.AccesoDenegado(bucket) from None
    except (gcs_exceptions.Unauthorized, auth_exceptions.RefreshError):
        # `401` al listar (FR-28) o un refresh rechazado (FR-26). Va antes que la
        # red: `RefreshError` no es `TransportError`, pero conviene no depender de eso.
        raise errors.CredencialesInvalidas() from None
    except _ERRORES_DE_RED:
        raise errors.ErrorDeRedAlListar(bucket) from None


@contextmanager
def _traducir_errores_de_objeto(bucket: str, object_name: str):
    """Traduce lo que el SDK levanta sobre **un objeto** a los errores de dominio
    que no abortan la corrida (FR-6, FR-13, FR-21).

    Envuelve tanto la apertura como cada lectura: con el SDK real `blob.open` es
    perezoso y el `403`/`404` llega recién en la primera lectura (excepción
    registrada de la revisión v1.5, acción 3).
    """
    try:
        yield
    except gcs_exceptions.NotFound:
        raise errors.ObjetoNoEncontrado(bucket, object_name) from None
    except (gcs_exceptions.Forbidden, gcs_exceptions.Unauthorized):
        # Un `401` sobre un objeto, con el listado ya aceptado, es FR-6 (v1.6).
        raise errors.ObjetoSinPermiso(bucket, object_name) from None
    except _ERRORES_DE_RED:
        raise errors.ErrorDeRedAlLeer(bucket, object_name) from None


class _LectorTraducido:
    """El lector del SDK, con cada operación pasada por la traducción de errores."""

    def __init__(self, lector, bucket: str, object_name: str) -> None:
        self._lector = lector
        self._bucket = bucket
        self._object_name = object_name

    def _traducir(self):
        return _traducir_errores_de_objeto(self._bucket, self._object_name)

    def __enter__(self) -> "_LectorTraducido":
        return self

    def __exit__(self, *exc_info) -> bool:
        close = getattr(self._lector, "close", None)
        if close is not None:
            close()
        return False

    def __iter__(self):
        with self._traducir():
            yield from self._lector

    def read(self, size: int = -1):
        with self._traducir():
            return self._lector.read(size)


def open_stream(bucket: str, object_name: str):
    """Devuelve un lector de **bytes** que streamea el contenido del objeto.

    Binario a propósito: qué es texto lo decide `core` (FR-9, FR-17, FR-22, FR-27).
    """
    client = _get_client()
    blob = client.bucket(bucket).blob(object_name)
    with _traducir_errores_de_objeto(bucket, object_name):
        lector = blob.open("rb", chunk_size=CHUNK_SIZE, retry=None)
    return _LectorTraducido(lector, bucket, object_name)
