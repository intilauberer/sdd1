"""Única capa que habla con la API real de Google Cloud Storage.

Usa Application Default Credentials (ver gcsgrep-base-context.md, punto 2):
no se pide ni se acepta ningún flag de credenciales explícito.

Es también el único lugar que conoce las excepciones del SDK: las traduce a los
errores de dominio de `errors`, para que `cli` pueda reportarlas sin importar
`google.api_core` (ADR-0013).
"""

from typing import Iterator, Optional

from google.api_core import exceptions as gcs_exceptions
from google.cloud import storage

from . import errors

_client: Optional[storage.Client] = None


def _get_client() -> storage.Client:
    global _client
    if _client is None:
        _client = storage.Client()
    return _client


def list_objects(bucket: str, prefix: str) -> Iterator[str]:
    client = _get_client()
    try:
        for blob in client.list_blobs(bucket, prefix=prefix):
            yield blob.name
    except gcs_exceptions.NotFound:
        raise errors.BucketNoEncontrado(bucket) from None
    except gcs_exceptions.Forbidden:
        raise errors.AccesoDenegado(bucket) from None


def open_text_stream(bucket: str, object_name: str):
    """Devuelve un file-like de texto que streamea el contenido del objeto."""
    client = _get_client()
    blob = client.bucket(bucket).blob(object_name)
    try:
        return blob.open("r")
    except gcs_exceptions.NotFound:
        # El objeto estaba en el listado y ya no está. Hoy aborta la corrida; que
        # no la aborte es FR-6, alcance de la Iteración 2.
        raise errors.ObjetoNoEncontrado(bucket, object_name) from None
    except gcs_exceptions.Forbidden:
        raise errors.AccesoDenegado(bucket, object_name) from None
