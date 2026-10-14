#!/usr/bin/env python3
"""Convierte la salida de `claude -p --output-format stream-json --verbose` en una
transcripción markdown legible sin correr nada (spec.md: evidencia/03…07).

Adaptado de `toolkit-tp3/scripts/transcripcion.py`. Muestra:
  - el prompt;
  - cada `tool_use` de la sesión principal con su resultado (los vetos de hooks y los
    permisos denegados incluidos);
  - las tool calls del subagent (mensajes con `parent_tool_use_id`), agrupadas bajo un
    encabezado "Subagent" y citadas (`>`), con los resultados recortados a 600 caracteres;
  - el informe final del subagent, entero: el `summary` de `system/task_notification`
    (subagent en segundo plano) o el `tool_result` del `Agent`;
  - el o los resultados finales.

Con `--marcar <texto>`, toda línea renderizada que contenga <texto> termina en
" ⟵ solo pudo venir del bucket". Las rutas locales se redactan (<repo>, <tmp>, ~).
"""

from __future__ import annotations

import argparse
import getpass
import json
import re
import sys
from pathlib import Path

MAX_MAIN = 2500
MAX_SUB = 600
MARCA = " ⟵ solo pudo venir del bucket"
ASYNC = "Async agent launched"

# Rutas locales: el repo (dos niveles arriba de scripts/), el home y el usuario de esta máquina.
REPO = str(Path(__file__).resolve().parents[2])
HOME = str(Path.home())
USUARIO = getpass.getuser()

REDACCIONES = [
    (re.compile(r"/private/tmp/claude-\d+/[^/\s\"'`]+"), "<tmp>"),
    (re.compile(r"/tmp/claude-\d+/[^/\s\"'`]+"), "<tmp>"),
    (re.compile(r"/var/folders/[^\s/]+/[^\s/]+/T/"), "<tmp>/"),
    (re.compile(re.escape(REPO)), "<repo>"),
    (re.compile(re.escape(REPO.replace("/", "-"))), "-<repo>"),
    (re.compile(re.escape(HOME)), "~"),
    (re.compile(rf"\b{re.escape(USUARIO)}\b"), "<user>"),  # dueño en salidas de `ls -l`
]

USO = """usage: transcripcion.py RUN.jsonl TITLE PROMPT [CONTEXT] [--marcar TEXT]

Render a `claude -p --output-format stream-json --verbose` run as markdown.
  RUN.jsonl   the raw stream-json output
  TITLE       H1 title of the transcript
  PROMPT      the prompt that was sent (stream-json does not repeat it)
  CONTEXT     optional legend for the prompt (default: fresh session, no toolkit piece named)
  --marcar T  append ' ⟵ solo pudo venir del bucket' to every rendered line containing T
"""


class Uso(argparse.ArgumentParser):
    def error(self, message):  # noqa: D401 — mensaje de CLI en inglés (D-6)
        sys.stderr.write(USO + f"\nerror: {message}\n")
        sys.exit(2)


def redactar(texto: str) -> str:
    for rx, rep in REDACCIONES:
        texto = rx.sub(rep, texto)
    return texto.replace("\r\n", "\n").replace("\r", "")


class Salida:
    def __init__(self, marcar: str | None):
        self.marcar = marcar
        self.lineas: list[str] = []

    def add(self, texto: str = "", cita: bool = False) -> None:
        for ln in redactar(texto).split("\n"):
            if self.marcar and self.marcar in ln:
                ln += MARCA
            self.lineas.append(("> " + ln if ln else ">") if cita else ln)

    def dump(self) -> str:
        return "\n".join(self.lineas).rstrip() + "\n"


def corto(texto: str, maximo: int | None) -> str:
    texto = texto.strip()
    if maximo is None or len(texto) <= maximo:
        return texto
    return texto[:maximo] + f"\n… [{len(texto) - maximo} caracteres más]"


def cerco(texto: str) -> str:
    """Un cerco de backticks más largo que cualquier racha del texto."""
    rachas = [len(m) for m in re.findall(r"`+", texto)]
    return "`" * max(3, max(rachas, default=0) + 1)


def bloque(texto: str, lang: str = "") -> str:
    f = cerco(texto)
    return f"{f}{lang}\n{texto}\n{f}"


def contenido(c) -> str:
    if isinstance(c, list):
        partes = []
        for x in c:
            if not isinstance(x, dict):
                continue
            if x.get("type") == "text":
                partes.append(x.get("text", ""))
            elif x.get("type") == "tool_reference":  # resultado de ToolSearch
                partes.append(f"[tool_reference] {x.get('tool_name', '')}")
        return "\n".join(partes)
    return "" if c is None else str(c)


def render_input(inp: dict, maximo: int | None) -> str:
    """JSON del input; los strings multilínea (content, prompt, command…) van aparte, sin escapar."""
    if not isinstance(inp, dict):
        return bloque(corto(json.dumps(inp, ensure_ascii=False), maximo), "json")
    largos = {k: v for k, v in inp.items() if isinstance(v, str) and "\n" in v}
    resto = {k: (f"<{k}: abajo>" if k in largos else v) for k, v in inp.items()}
    partes = [bloque(corto(json.dumps(resto, ensure_ascii=False, indent=1), maximo), "json")]
    for k, v in largos.items():
        partes.append(f"`{k}`:\n\n" + bloque(corto(v, maximo)))
    return "\n\n".join(partes)


def render_resultado(texto: str, maximo: int | None) -> str:
    """Si el resultado es JSON con un `content` de texto (read_object_content), lo despliega."""
    try:
        d = json.loads(texto)
    except (ValueError, TypeError):
        d = None
    if isinstance(d, dict) and isinstance(d.get("content"), str):
        meta = {k: v for k, v in d.items() if k != "content"}
        cuerpo = json.dumps(meta, ensure_ascii=False, indent=1) + "\ncontent:\n" + d["content"]
        return bloque(corto(cuerpo, maximo))
    return bloque(corto(texto, maximo))


def main(argv: list[str]) -> int:
    ap = Uso(add_help=True, usage=USO)
    ap.add_argument("jsonl")
    ap.add_argument("titulo")
    ap.add_argument("prompt")
    ap.add_argument("contexto", nargs="?",
                    default="sesión nueva, sin nombrar ninguna pieza del toolkit")
    ap.add_argument("--marcar", default=None)
    a = ap.parse_args(argv)

    try:
        eventos = []
        with open(a.jsonl, encoding="utf-8") as fh:
            for linea in fh:
                try:
                    ev = json.loads(linea)
                except json.JSONDecodeError:
                    continue
                if isinstance(ev, dict):
                    eventos.append(ev)
    except OSError as exc:
        sys.stderr.write(USO + f"\nerror: cannot read {a.jsonl}: {exc}\n")
        return 2

    out = Salida(a.marcar)
    out.add(f"# {a.titulo}\n")
    out.add(f"**Prompt** ({a.contexto}):\n")
    out.add("\n".join("> " + x for x in a.prompt.split("\n")) + "\n")

    agentes: dict[str, dict] = {}       # tool_use_id del Agent → input
    sub_buf: dict[str, list] = {}       # tool_use_id del Agent → eventos del subagent
    informe: dict[str, str] = {}        # tool_use_id del Agent → informe final
    emitidos: set[str] = set()
    inits = 0

    def emitir_subagent(pid: str) -> None:
        if pid in emitidos:
            return
        emitidos.add(pid)
        inp = agentes.get(pid, {})
        out.add(f"#### Subagent `{inp.get('subagent_type', '?')}` — {inp.get('description', '')}\n")
        for ev in sub_buf.get(pid, []):
            msg = ev.get("message") if isinstance(ev.get("message"), dict) else {}
            for b in msg.get("content") if isinstance(msg.get("content"), list) else []:
                if not isinstance(b, dict):
                    continue
                if ev["type"] == "assistant" and b.get("type") == "tool_use":
                    out.add(f"**→ {b['name']}** *(subagent)*\n", cita=True)
                    out.add(render_input(b.get("input"), MAX_SUB) + "\n", cita=True)
                elif ev["type"] == "user" and b.get("type") == "tool_result":
                    marca = " ⛔ (error / bloqueado)" if b.get("is_error") else ""
                    out.add(f"**← resultado**{marca} *(subagent, recortado a {MAX_SUB} caracteres)*\n", cita=True)
                    out.add(render_resultado(contenido(b.get("content")), MAX_SUB) + "\n", cita=True)
        rep = informe.get(pid)
        if rep is None:  # sin notificación ni tool_result: el último texto del subagent
            for ev in reversed(sub_buf.get(pid, [])):
                msg = ev.get("message") if isinstance(ev.get("message"), dict) else {}
                textos = [b.get("text", "") for b in msg.get("content") or []
                          if isinstance(b, dict) and b.get("type") == "text" and b.get("text", "").strip()]
                if ev.get("type") == "assistant" and textos:
                    rep = "\n".join(textos)
                    break
        out.add("**Informe final del subagent** (entero):\n", cita=True)
        out.add(bloque(rep.strip() if rep else "(sin informe)", "md") + "\n", cita=True)

    for ev in eventos:
        tipo = ev.get("type")
        pid = ev.get("parent_tool_use_id")
        if pid:
            sub_buf.setdefault(pid, []).append(ev)
            continue
        if tipo == "system":
            st = ev.get("subtype")
            if st == "init":
                inits += 1
                gcs = [f"`{s['name']}` ({s.get('status')})" for s in ev.get("mcp_servers") or []
                       if "gcs" in s.get("name", "")]
                tools_gcs = [t for t in ev.get("tools") or [] if "gcs" in t]
                cab = "Inicio de la sesión" if inits == 1 else f"`system/init` #{inits} (misma sesión, sigue)"
                out.add(f"- {cab}: sesión `{ev.get('session_id')}` · modelo `{ev.get('model')}` · "
                        f"Claude Code {ev.get('claude_code_version', '?')} · servers MCP de gcs: "
                        f"{', '.join(gcs) or 'ninguno'} · tools de gcs en la sesión: {len(tools_gcs)}\n")
            elif st == "permission_denied":
                out.add(f"**⊘ permiso denegado** (capa de aprobación de `-p`, no un hook): "
                        f"`{ev.get('tool_name')}` — {ev.get('message', '')}\n")
            elif st == "hook_response" and ev.get("hook_event") != "SessionStart" and (
                    ev.get("exit_code") not in (0, None) or (ev.get("stderr") or "").strip()):
                out.add(f"**hook `{ev.get('hook_name')}`** exit {ev.get('exit_code')}\n")
                out.add(bloque((ev.get("stderr") or ev.get("output") or "").strip()) + "\n")
            elif st == "task_notification":
                tid = ev.get("tool_use_id")
                if tid:
                    informe[tid] = ev.get("summary") or ""
                    emitir_subagent(tid)
            continue
        if tipo == "result":
            out.add(f"---\n**Resultado final** · turnos: {ev.get('num_turns')} · "
                    f"duración: {(ev.get('duration_ms') or 0) // 1000}s · "
                    f"is_error: {ev.get('is_error')}\n")
            out.add((ev.get("result") or "").strip() + "\n")
            continue
        msg = ev.get("message") if isinstance(ev.get("message"), dict) else {}
        for b in msg.get("content") if isinstance(msg.get("content"), list) else []:
            if not isinstance(b, dict):
                continue
            if tipo == "assistant" and b.get("type") == "text" and b["text"].strip():
                out.add(f"**Agente:** {corto(b['text'], MAX_MAIN)}\n")
            elif tipo == "assistant" and b.get("type") == "tool_use":
                if b.get("name") in ("Agent", "Task"):
                    agentes[b["id"]] = b.get("input") or {}
                out.add(f"**→ {b['name']}**\n")
                out.add(render_input(b.get("input"), None if b.get("name") in ("Agent", "Task") else MAX_MAIN) + "\n")
            elif tipo == "user" and b.get("type") == "tool_result":
                tid = b.get("tool_use_id")
                texto = contenido(b.get("content"))
                marca = " ⛔ (error / bloqueado)" if b.get("is_error") else ""
                if tid in agentes:
                    if texto.startswith(ASYNC):
                        out.add("**← resultado** (el `Agent` arrancó en segundo plano; el informe llega "
                                "por `system/task_notification`)\n")
                        continue
                    if tid in emitidos:  # ya salió con el summary de task_notification
                        out.add(f"**← resultado del Agent**{marca} (el informe de arriba, que la sesión "
                                f"recibe dentro del marco `[Subagent hand-back]`)\n")
                        continue
                    informe[tid] = texto
                    out.add(f"**← resultado del Agent**{marca}\n")
                    emitir_subagent(tid)
                    continue
                out.add(f"**← resultado**{marca}\n")
                out.add(render_resultado(texto, MAX_MAIN) + "\n")

    for pid in sub_buf:  # subagents que no cerraron con notificación ni tool_result
        if pid not in emitidos:
            emitir_subagent(pid)

    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stdout.write(out.dump())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
