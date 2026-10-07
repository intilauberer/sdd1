---
name: write-spec-brownfield
description: Usar cuando el usuario pide especificar un cambio o feature sobre código que ya existe — "especificá X en tmux", "escribí la spec para agregar Y a este repo", "spec brownfield". Exige notas con archivo:línea, alcance Dentro/Fuera por path, invariantes con chequeo, línea de base de regresión y un VC por requerimiento. No sirve para un sistema nuevo desde cero.
---

# write-spec-brownfield

Convierte un pedido de cambio sobre un repo existente en una spec que un agente
pueda implementar **sin romper lo que ya anda**.

**La regla que este skill hace imposible saltear:** no hay requerimiento sin VC, ni
invariante sin chequeo ejecutable. Lo verifica un script, no la buena voluntad.

## Cuándo NO usarlo

- Sistema nuevo, sin código previo: eso es una spec greenfield (TP1).
- Cambia una decisión ya registrada: eso es un ADR nuevo que supersede al viejo.

## Pasos

1. **Explorá antes de escribir** (higiene de contexto). Si ya hay un
   `notas-exploracion.md` para el commit fijado, usalo. Si no, lanzá un subagent de
   solo lectura (el built-in `Explore`; el toolkit no trae uno propio) que devuelva
   módulos, interfaces y riesgos **con `archivo:línea`** contra ese commit, y guardalo
   en `notas-exploracion.md`; la spec lo enlaza.
2. **Medí la línea de base** antes de tocar nada: los comandos reales del repo
   (build, tests) y su resultado, en la spec.
3. **Alcance por path.** Tabla *Dentro*: cada archivo que cambia y qué cambia.
   *Fuera*: paths concretos que el implementador no abre. Nunca "no se toca el resto".
4. **Invariantes con chequeo.** Lo que tiene que seguir siendo verdad (comandos
   existentes, plataformas, formato) y el comando que lo comprueba.
5. **Requerimientos** `FR-n`/`BR-n`/`NFR-n` en Dado / Cuando / Entonces, uno por
   situación, cada uno con su `VC-n` observable: texto literal, exit code, magnitud.
6. **Decisiones** con lo descartado y por qué, *dentro* de la spec.
7. **Verificá la cobertura:** `python3 .claude/skills/write-spec-brownfield/scripts/vc-huerfanos.py <spec>`.
   Exit ≠ 0 ⇒ hay huérfanos: completalos antes de seguir.
8. **Pedí revisión independiente** al subagent `revisor-spec`. No la cierres vos.

## Plantilla

```md
# Spec — <cambio> sobre <repo>@<commit>
## 1 · Propósito          (por qué existe el cambio)
## 2 · Actores            (incluidos los no humanos)
## 3 · Alcance
### Dentro                | path | qué cambia |
### Fuera (por path)      | path | por qué no se toca |
## 4 · Invariantes        | INV-n | qué sigue siendo verdad | comando que lo chequea |
## 5 · Requerimientos
**FR-1 · <título>.** **Dado** … **cuando** … **entonces** …
> **VC-1** — <comando> → <stdout/stderr literal>, exit <n>
## 6 · Decisiones         | D-n | elegido | descartado | por qué |
## 7 · Línea de base      (comando + resultado, medido antes del cambio)
```

## Anti-patrones

- **"No se toca el resto."** No es alcance: nombrá los paths.
- **Invariante sin comando.** Es un deseo, no un invariante.
- **VC que "verifica que funciona correctamente".** Sin texto literal ni exit code no
  se puede fallar.
- **Citar el repo de memoria.** Sin `archivo:línea` en el commit fijado, la nota no
  es verificable.
- **Implementar en la spec.** Código nuevo en el diff de una spec es alcance que se
  coló.
