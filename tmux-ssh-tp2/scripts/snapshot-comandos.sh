#!/bin/sh
#
# Foto de la resolución de nombres de comando de un binario de tmux.
#
# Para cada nombre y alias de la tabla de comandos, y para cada prefijo de cada
# uno, imprime a qué comando resuelve `cmd_find()` (vía `list-commands`), o
# "ERR" si es ambiguo o desconocido. Sirve para INV-3 de la spec: agregar un
# comando nuevo no puede cambiar a qué resuelve ningún prefijo existente
# (`tmux split` tiene que seguir siendo `split-window`).
#
#   TEST_TMUX=./tmux sh snapshot-comandos.sh > antes.txt
#   (después del cambio)
#   TEST_TMUX=./tmux sh snapshot-comandos.sh | grep -v '^ssh-pane' > despues.txt
#   diff antes.txt despues.txt          # tiene que salir vacío
#
# Lo único que se espera que cambie son las líneas del comando nuevo; por eso el
# grep -v. Los prefijos "s", "ss", ... de otros comandos sí se comparan.
#
set -eu

TMUX_BIN="${TEST_TMUX:-tmux}"
SOCK="snapshot$$"
T="$TMUX_BIN -L$SOCK -f/dev/null"

$T new-session -d 'exec sleep 300'
trap '$T kill-server 2>/dev/null || true' EXIT

# Dos pasadas: un formato con salto de línea se imprime con "_" en su lugar.
nombres=$( ($T list-commands -F '#{command_list_name}'
	$T list-commands -F '#{command_list_alias}') | grep -v '^$' | sort -u)

for n in $nombres; do
	i=1
	while [ "$i" -le "${#n}" ]; do
		p=$(printf '%s' "$n" | cut -c1-"$i")
		r=$($T list-commands -F '#{command_list_name}' "$p" 2>/dev/null) || r=ERR
		printf '%s\t%s\t%s\n' "$n" "$p" "$r"
		i=$((i + 1))
	done
done
