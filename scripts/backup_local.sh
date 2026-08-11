#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
backup_root="${1:-$project_dir/backups}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="$backup_root/local-$timestamp"

mkdir -p "$target"
if [[ ! -f "$project_dir/backend/obd2sd.db" ]]; then
  echo "No existe la base local backend/obd2sd.db" >&2
  exit 1
fi

cp "$project_dir/backend/obd2sd.db" "$target/obd2sd.db"
if [[ -d "$project_dir/backend/uploads" ]]; then
  cp -a "$project_dir/backend/uploads" "$target/uploads"
fi

(cd "$target" && sha256sum obd2sd.db > SHA256SUMS && find uploads -type f -print0 2>/dev/null | sort -z | xargs -0 -r sha256sum >> SHA256SUMS)
printf 'created_at=%s\nsource=local-sqlite\n' "$timestamp" > "$target/MANIFEST"
echo "Respaldo local creado en: $target"
