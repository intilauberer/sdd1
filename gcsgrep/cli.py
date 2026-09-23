"""Parsea argv, arma la config de búsqueda, traduce el resultado a exit code."""

import argparse
import sys
from typing import Optional, Sequence

from . import core, gcs


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
    found_any = False
    for match in core.search(bucket, prefix, config, gcs.list_objects, gcs.open_text_stream):
        found_any = True
        print(format_match(match, args.line_number), flush=True)

    return 0 if found_any else 1


if __name__ == "__main__":
    sys.exit(main())
