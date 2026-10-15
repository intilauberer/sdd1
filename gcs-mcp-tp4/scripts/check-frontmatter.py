#!/usr/bin/env python3
"""check-frontmatter — el frontmatter YAML de cada agent y skill parsea (spec v1.8.1, VC-11a).

Por qué existe: en Claude Code 2.1.300, una `description` con ": " adentro sin comillas
hace que el frontmatter de un agent no parsee. El agent carga igual, con el nombre tomado
del archivo y **todo lo demás descartado en silencio**, incluido `tools:`; así el subagent
`lector-fixtures` heredaría Bash y red (revisión cruzada, ronda 1, hallazgo B1). Lo detecta
`claude plugin validate`, pero CI no tiene Claude Code: este script parsea el frontmatter
de `.claude/agents/*.md`, `.claude/skills/*/SKILL.md` y sus copias en el plugin, exige
`name` y, en `lector-fixtures`, exige `tools:` con exactamente las 3 tools de lectura.

Salida en inglés (D-6). exit 0 si todo parsea · exit 1 con un FAIL por archivo.
Requiere PyYAML (`pip install pyyaml`).
"""

import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("check-frontmatter: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

RAIZ = Path(__file__).resolve().parents[2]
PLUGIN = RAIZ / "gcs-mcp-tp4/plugin/gcsgrep-toolkit"
LECTURA = ("list_objects", "read_object_metadata", "read_object_content")


def archivos():
    yield from sorted((RAIZ / ".claude/agents").glob("*.md"))
    yield from sorted((RAIZ / ".claude/skills").glob("*/SKILL.md"))
    yield from sorted((PLUGIN / "agents").glob("*.md"))
    yield from sorted((PLUGIN / "skills").glob("*/SKILL.md"))


def frontmatter(texto: str):
    if not texto.startswith("---\n"):
        raise ValueError("no frontmatter (file does not start with ---)")
    fin = texto.find("\n---", 4)
    if fin < 0:
        raise ValueError("frontmatter is not closed")
    datos = yaml.safe_load(texto[4:fin])
    if not isinstance(datos, dict):
        raise ValueError("frontmatter is not a YAML mapping")
    return datos


def main() -> int:
    fallas = 0
    for f in archivos():
        rel = f.relative_to(RAIZ).as_posix()
        try:
            datos = frontmatter(f.read_text(encoding="utf-8"))
            if not isinstance(datos.get("name"), str):
                raise ValueError("missing `name`")
            if f.name == "lector-fixtures.md":
                tools = datos.get("tools")
                if not isinstance(tools, str):
                    raise ValueError("`tools:` missing or not a string: the subagent would inherit Bash and network")
                sufijos = tuple(t.strip().split("__")[-1] for t in tools.split(","))
                if sufijos != LECTURA:
                    raise ValueError(f"`tools:` is {tools!r}, expected exactly the 3 read tools")
        except Exception as exc:  # noqa: BLE001 — cualquier fallo de parseo es un FAIL
            print(f"FAIL {rel}: {exc}")
            fallas += 1
            continue
        print(f"OK   {rel}")
    if fallas:
        print(f"check-frontmatter: {fallas} file(s) with unparseable or wrong frontmatter")
        return 1
    print("check-frontmatter: OK, every agent and skill frontmatter parses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
