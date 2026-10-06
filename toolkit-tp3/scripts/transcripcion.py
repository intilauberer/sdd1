#!/usr/bin/env python3
"""Convierte la salida `claude -p --output-format stream-json --verbose` en una
transcripción markdown legible: prompt, cada tool call con su resultado (los
bloqueos de hooks incluidos) y la respuesta final.

    python3 transcripcion.py corrida.jsonl "Título" "prompt" > evidencia/x.md
"""

import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
MAX = 2500
TOOLKIT = {"write-spec-brownfield", "revisor-spec"}
RUTA_LOCAL = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/]+[\\/]+Downloads[\\/]+SDD[\\/]+sdd1(?:-demo(?:-skill)?)?[\\/]*")
_print = print


def print(*a, **k):
    _print(*(RUTA_LOCAL.sub("<repo>/", str(x)) for x in a), **k)


def corto(texto: str) -> str:
    texto = texto.strip()
    return texto if len(texto) <= MAX else texto[:MAX] + f"\n… [{len(texto) - MAX} caracteres más]"


def contenido(c) -> str:
    if isinstance(c, list):
        return "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
    return str(c)


ruta, titulo, prompt = sys.argv[1:4]
print(f"# {titulo}\n\n**Prompt** (sesión nueva, sin nombrar ninguna pieza del toolkit):\n\n> {prompt}\n")
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
        print(f"- Sesión `{ev.get('session_id')}` · modelo `{ev.get('model')}` · "
              f"piezas del toolkit cargadas al arrancar: "
              f"{', '.join(sorted(TOOLKIT & set((ev.get('skills') or []) + (ev.get('agents') or [])))) or '—'}\n")
    for b in msg.get("content") if isinstance(msg.get("content"), list) else []:
        if ev["type"] == "assistant" and b.get("type") == "text" and b["text"].strip() and not sub:
            print(f"**Agente:** {corto(b['text'])}\n")
        elif ev["type"] == "assistant" and b.get("type") == "tool_use":
            print(f"**→ {b['name']}**{sub}\n```json\n{corto(json.dumps(b['input'], ensure_ascii=False, indent=1))}\n```\n")
        elif ev["type"] == "user" and b.get("type") == "tool_result":
            marca = " ⛔ (error / bloqueado)" if b.get("is_error") else ""
            print(f"**← resultado**{marca}{sub}\n```\n{corto(contenido(b.get('content')))}\n```\n")
    if ev.get("type") == "result":
        print(f"---\n**Resultado final** · turnos: {ev.get('num_turns')} · "
              f"duración: {ev.get('duration_ms', 0) // 1000}s\n\n{ev.get('result', '')}\n")
