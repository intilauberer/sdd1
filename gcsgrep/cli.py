"""Parsea argv, arma la config de búsqueda, traduce el resultado a exit code."""

import argparse
import sys
from typing import List, Optional, Sequence

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

    matches: List[core.Match] = core.search(
        bucket, prefix, config, gcs.list_objects, gcs.open_text_stream
    )

    for match in matches:
        print(format_match(match, args.line_number))

    return 0 if matches else 1


if __name__ == "__main__":
    sys.exit(main())
