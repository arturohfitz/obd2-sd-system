#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 || "$2" != "--confirm-restore" ]]; then
  echo "Uso: $0 /ruta/production-AAAAMMDDTHHMMSSZ --confirm-restore" >&2
  exit 2
fi

source_dir="$(realpath "$1")"
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -f "$source_dir/database.sql.gz" || ! -f "$source_dir/SHA256SUMS" ]]; then
  echo "El directorio no contiene un respaldo de producción válido" >&2
  exit 1
fi

cd "$source_dir"
sha256sum -c SHA256SUMS
cd "$project_dir"
docker compose exec -T db psql -U obd2sd -d obd2sd -v ON_ERROR_STOP=1 -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'
gzip -dc "$source_dir/database.sql.gz" | docker compose exec -T db psql -U obd2sd -d obd2sd -v ON_ERROR_STOP=1
if [[ -d "$source_dir/uploads" ]]; then
  docker compose exec -T backend sh -c 'find /data/uploads -mindepth 1 -maxdepth 1 -delete'
  docker compose cp "$source_dir/uploads/." backend:/data/uploads/ >/dev/null
fi
echo "Restauración terminada. Reinicia los servicios y ejecuta las verificaciones de salud."
