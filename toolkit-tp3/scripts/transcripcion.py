#!/usr/bin/env python3
"""Convierte la salida `claude -p --output-format stream-json --verbose` en una
transcripción markdown legible: prompt, cada tool call con su resultado (los
bloqueos de hooks incluidos), el informe final de cada subagent y la respuesta final.

    python3 transcripcion.py corrida.jsonl "Título" "prompt" ["contexto del prompt"] > evidencia/x.md

El cuarto argumento reemplaza la leyenda por defecto "sesión nueva, sin nombrar
ninguna pieza del toolkit" (p. ej. para turnos `--resume`). Si el .jsonl concatena
varios turnos `--resume`, cada `init` abre una sección "Turno n".
"""

import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", newline="\n")  # LF también en Windows
MAX = 2500
TOOLKIT = {"write-spec-brownfield", "revisor-spec"}
RUTA_LOCAL = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/]+[\\/]+Downloads[\\/]+SDD[\\/]+sdd1(?:-demo[\w-]*)?[\\/]*")
HANDBACK = "[Subagent hand-back]"
_print = print


def print(*a, **k):
    # sin CR: el contenido del stream-json trae \r\n de Windows y el .md va con LF
    _print(*(RUTA_LOCAL.sub("<repo>/", str(x)).replace("\r\n", "\n").replace("\r", "") for x in a), **k)


def corto(texto: str, entero: bool = False) -> str:
    texto = texto.strip()
    if entero or len(texto) <= MAX:
        return texto
    return texto[:MAX] + f"\n… [{len(texto) - MAX} caracteres más]"


def contenido(c) -> str:
    if isinstance(c, list):
        return "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
    return str(c)


ruta, titulo, prompt = sys.argv[1:4]
contexto = sys.argv[4] if len(sys.argv) > 4 else "sesión nueva, sin nombrar ninguna pieza del toolkit"
print(f"# {titulo}\n\n**Prompt** ({contexto}):\n\n> {prompt}\n")
turno = 0
for linea in open(ruta, encoding="utf-8"):
    try:
        ev = json.loads(linea)
    except json.JSONDecodeError:
        continue
    if not isinstance(ev, dict):
        continue
    msg = ev.get("message") if isinstance(ev.get("message"), dict) else {}
    sub = " *(dentro del subagent)*" if ev.get("parent_tool_use_id") else ""
    if ev.get("type") == "system" and ev.get("subtype") == "init":
        turno += 1
        if turno > 1:
            print(f"\n## Turno {turno} (`--resume` sobre la misma sesión; el prompt del turno no "
                  f"queda en el stream-json)\n")
        print(f"- Sesión `{ev.get('session_id')}` · modelo `{ev.get('model')}` · "
              f"piezas del toolkit cargadas al arrancar: "
              f"{', '.join(sorted(TOOLKIT & set((ev.get('skills') or []) + (ev.get('agents') or [])))) or '—'}\n")
    for b in msg.get("content") if isinstance(msg.get("content"), list) else []:
        if not isinstance(b, dict):
            continue
        if ev["type"] == "assistant" and b.get("type") == "text" and b["text"].strip():
            if not sub:
                print(f"**Agente:** {corto(b['text'])}\n")
            elif "VEREDICTO" in b["text"]:  # informe final del subagent, entero
                print(f"**Subagent (informe final):**\n\n{corto(b['text'], entero=True)}\n")
        elif ev["type"] == "assistant" and b.get("type") == "tool_use":
            print(f"**→ {b['name']}**{sub}\n```json\n{corto(json.dumps(b['input'], ensure_ascii=False, indent=1))}\n```\n")
        elif ev["type"] == "user" and b.get("type") == "tool_result":
            marca = " ⛔ (error / bloqueado)" if b.get("is_error") else ""
            texto = contenido(b.get("content"))
            print(f"**← resultado**{marca}{sub}\n```\n{corto(texto, entero=texto.startswith(HANDBACK))}\n```\n")
    if ev.get("type") == "result":
        print(f"---\n**Resultado final** · turnos: {ev.get('num_turns')} · "
              f"duración: {ev.get('duration_ms', 0) // 1000}s\n\n{ev.get('result', '')}\n")
