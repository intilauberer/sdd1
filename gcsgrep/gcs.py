"""Única capa que habla con la API real de Google Cloud Storage.

Usa Application Default Credentials (ver gcsgrep-base-context.md, punto 2):
no se pide ni se acepta ningún flag de credenciales explícito.
"""

from typing import Iterator, Optional

from google.cloud import storage

_client: Optional[storage.Client] = None


def _get_client() -> storage.Client:
    global _client
    if _client is None:
        _client = storage.Client()
    return _client


def list_objects(bucket: str, prefix: str) -> Iterator[str]:
    client = _get_client()
    for blob in client.list_blobs(bucket, prefix=prefix):
        yield blob.name


def open_text_stream(bucket: str, object_name: str):
    """Devuelve un file-like de texto que streamea el contenido del objeto."""
    client = _get_client()
    blob = client.bucket(bucket).blob(object_name)
    return blob.open("r")
