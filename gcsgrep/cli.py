"""Parsea argv, arma la config de búsqueda, traduce el resultado a exit code.

Es también la **frontera de manejo de excepciones** del programa: el borde del
proceso es el único lugar que ve todas las excepciones, y por lo tanto el único
donde se puede garantizar que ningún error termine en un traceback (NFR-3,
FR-12, ADR-0013). Ver H-12 en docs/hallazgos/.
"""

import argparse
import os
import sys
from typing import Optional, Sequence

from . import core, errors, gcs

#: Variable de entorno que desactiva la frontera para diagnosticar. Con esto en
#: "1" la excepción se re-lanza con su traceback: es la vía de escape explícita
#: para que el caso genérico no esconda el problema (ADR-0013).
DEBUG_ENV = "GCSGREP_DEBUG"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gcsgrep",
        description="grep sobre el contenido de objetos de Google Cloud Storage.",
    )
    parser.add_argument("-i", "--ignore-case", action="store_true", help="búsqueda sin distinguir mayúsculas")
    parser.add_argument("-n", "--line-number", action="store_true", help="mostrar el número de línea de cada match")
    parser.add_argument("pattern", help="texto literal a buscar")
    parser.add_argument("location", help="gs://bucket/prefijo")
    return parser


def format_match(match: core.Match, show_line_numbers: bool) -> str:
    """Formato estilo `grep` (ADR-0007)."""
    uri = f"gs://{match.bucket}/{match.object_name}"
    if show_line_numbers:
        return f"{uri}:{match.line_number}:{match.text}"
    return f"{uri}:{match.text}"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        bucket, prefix = core.parse_location(args.location)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    config = core.SearchConfig(
        pattern=args.pattern,
        ignore_case=args.ignore_case,
        show_line_numbers=args.line_number,
    )

    # Se imprime cada match en cuanto aparece, con flush, para que la salida
    # sea incremental (FR-11 / ADR-0011). Consecuencia: no se puede contar los
    # matches antes de imprimirlos, así que el exit code sale de un flag.
    #
    # El try envuelve el recorrido completo, no cada match: los matches ya
    # emitidos quedan emitidos (VC-17 de punta a punta) y el fallo posterior
    # decide el exit code.
    found_any = False
    try:
        for match in core.search(bucket, prefix, config, gcs.list_objects, gcs.open_text_stream):
            found_any = True
            print(format_match(match, args.line_number), flush=True)
    except errors.ErrorDeAcceso as exc:
        # Fallos que `gcs` supo identificar: el mensaje ya está escrito para
        # quien corrió el comando (FR-12 / VC-18).
        print(f"gcsgrep: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 — ver el docstring del módulo
        # Caso genérico: cualquier excepción que nadie previó. Existe para que
        # NFR-3 ("ningún caso de error imprime un stack trace") sea cierto para
        # *todos* los caminos y no solo para los enumerados (VC-16 b).
        #
        # No es una implementación de NFR-2: no reintenta, no distingue causas y
        # no clasifica nada. Es el piso que evita el traceback.
        if os.environ.get(DEBUG_ENV) == "1":
            raise
        print(
            f"gcsgrep: error inesperado al acceder a gs://{bucket}: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        print(
            f"gcsgrep: corré con {DEBUG_ENV}=1 para ver el detalle completo.",
            file=sys.stderr,
        )
        return 2

    return 0 if found_any else 1


if __name__ == "__main__":
    sys.exit(main())
