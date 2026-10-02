"""Iteración 2 · contenido no-texto: FR-9, FR-10, FR-17, FR-22, FR-27 y el
`chunk_size` del lector de GCS (NFR-1, VC-14 (c))."""

import gzip
import tracemalloc

import pytest

from gcsgrep import cli, core, gcs
from .fakes import FakeGCS


class _ContadorGCS(FakeGCS):
    def __init__(self) -> None:
        super().__init__()
        self.aperturas = []

    def open_stream(self, bucket, name):
        self.aperturas.append(name)
        return super().open_stream(bucket, name)


@pytest.fixture
def fake(monkeypatch):
    f = _ContadorGCS()
    monkeypatch.setattr(gcs, "list_objects", f.list_objects)
    monkeypatch.setattr(gcs, "open_stream", f.open_stream)
    return f


def _correr(capsys, argv):
    exit_code = cli.main(argv)
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


# --- FR-9 · binarios -------------------------------------------------------------


def _binario_con_timeout():
    return b"\x01\x02" * 5 + b"\x00" + b"\xff\xfe timeout \x00\x10"


def test_vc9_binario_se_saltea_con_una_linea_por_stderr(fake, capsys):
    fake.put("b", "p/blob.bin", _binario_con_timeout())
    fake.put("b", "p/a.txt", "connection timeout\n")

    assert _correr(capsys, ["timeout", "gs://b/p/"]) == (
        0,
        "gs://b/p/a.txt:connection timeout\n",
        "gcsgrep: salteado (binario): gs://b/p/blob.bin\n",
    )


def test_vc9_solo_el_binario(fake, capsys):
    fake.put("b", "p/blob.bin", _binario_con_timeout())

    assert _correr(capsys, ["timeout", "gs://b/p/"]) == (
        1, "", "gcsgrep: salteado (binario): gs://b/p/blob.bin\n"
    )


def test_vc20_nul_en_el_offset_8191_es_binario(fake, capsys):
    fake.put("b", "p/a.bin", b"a" * 8191 + b"\x00" + b"\ntimeout\n")

    assert _correr(capsys, ["-n", "timeout", "gs://b/p/"]) == (
        1, "", "gcsgrep: salteado (binario): gs://b/p/a.bin\n"
    )


def test_vc20_nul_en_el_offset_8192_es_texto_y_sale_tal_cual(fake, capsys):
    fake.put("b", "p/a.txt", b"a" * 8191 + b"\n" + b"\x00" + b" timeout\n")

    assert _correr(capsys, ["-n", "timeout", "gs://b/p/"]) == (
        0, "gs://b/p/a.txt:2:\x00 timeout\n", ""
    )


# --- FR-10 · .gz -----------------------------------------------------------------


def test_vc10_gz_se_saltea_sin_abrirlo(fake, capsys):
    fake.put("b", "p/access.log.gz", gzip.compress(b"timeout\n"))

    assert _correr(capsys, ["timeout", "gs://b/p/"]) == (
        1, "", "gcsgrep: salteado (.gz): gs://b/p/access.log.gz\n"
    )
    assert fake.aperturas == []


# --- FR-17 · UTF-8 con reemplazo ----------------------------------------------------


def test_vc25_latin1_se_decodifica_con_reemplazo(fake, capsys):
    fake.put("b", "p/a.txt", b"caf\xe9 timeout\n")

    assert _correr(capsys, ["timeout", "gs://b/p/"]) == (
        0, "gs://b/p/a.txt:caf� timeout\n", ""
    )


def test_vc25_un_caracter_multibyte_partido_entre_lecturas_no_se_rompe(fake, capsys):
    """El borde de bloque cae en medio de `ñ`: el decodificador es incremental."""
    relleno = b"a" * (core.BLOQUE_DE_LECTURA - 1)
    fake.put("b", "p/a.txt", relleno + "ñandú timeout\n".encode("utf-8"))

    exit_code, out, _ = _correr(capsys, ["timeout", "gs://b/p/"])

    assert exit_code == 0
    assert out.endswith("ñandú timeout\n")
    assert "�" not in out


# --- FR-22 · terminador -------------------------------------------------------------


def test_vc34_terminador_de_linea(fake, capsys):
    fake.put("b", "p/a.txt", b"uno\r\ndos\rtres\n")

    assert _correr(capsys, ["-n", "tres", "gs://b/p/"]) == (
        0, "gs://b/p/a.txt:2:dos\rtres\n", ""
    )
    assert _correr(capsys, ["-n", "uno", "gs://b/p/"]) == (
        0, "gs://b/p/a.txt:1:uno\n", ""
    )


# --- FR-27 · BOM --------------------------------------------------------------------


def test_vc44_bom_inicial_se_descarta(fake, capsys):
    fake.put("b", "p/a.txt", b"\xef\xbb\xbftimeout\n")

    assert _correr(capsys, ["-n", "timeout", "gs://b/p/"]) == (
        0, "gs://b/p/a.txt:1:timeout\n", ""
    )


def test_vc44_bom_fuera_del_principio_se_conserva(fake, capsys):
    """Excepción registrada, acción 15."""
    fake.put("b", "p/a.txt", b"uno\n\xef\xbb\xbftimeout\n")

    assert _correr(capsys, ["-n", "timeout", "gs://b/p/"]) == (
        0, "gs://b/p/a.txt:2:﻿timeout\n", ""
    )


# --- NFR-1 · VC-14 (c): a través del lector real de la librería cliente ----------------

_LINEA = b"x" * 200 + b"\n"
_TOTAL = 200 * 1024 * 1024
_UMBRAL = 20 * 1024 * 1024


class _BlobEnMemoria:
    """Blob falso que sirve 200 MiB virtuales por `download_as_bytes(start, end)`,
    la única operación que `BlobReader` le pide. `end` es inclusivo, como en GCS."""

    def __init__(self):
        self.open_kwargs = None

    def download_as_bytes(self, start=0, end=None, **kwargs):
        fin = _TOTAL if end is None else min(end + 1, _TOTAL)
        if start >= fin:
            return b""
        largo = len(_LINEA)
        offset = start % largo
        n = fin - start
        return (_LINEA * ((offset + n) // largo + 1))[offset:offset + n]

    def open(self, mode, **kwargs):
        from google.cloud.storage.fileio import BlobReader

        assert mode == "rb"
        self.open_kwargs = kwargs
        return BlobReader(self, **kwargs)


def test_vc14c_memoria_acotada_a_traves_de_blobreader(monkeypatch):
    blob = _BlobEnMemoria()

    class _Cliente:
        def bucket(self, name):
            class _Bucket:
                def blob(self, nombre):
                    return blob

            return _Bucket()

    monkeypatch.setattr(gcs, "_get_client", lambda: _Cliente())
    config = core.SearchConfig(pattern="patron-que-nunca-aparece")

    tracemalloc.start()
    base, _ = tracemalloc.get_traced_memory()
    eventos = list(core.search("b", "", config, lambda b, p: ["huge.txt"], gcs.open_stream))
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert eventos == []
    assert blob.open_kwargs.get("chunk_size", 0) <= 1024 * 1024
    assert pico - base < _UMBRAL, f"pico {(pico - base) / 1024 / 1024:.1f} MiB"
