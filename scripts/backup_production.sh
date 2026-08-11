#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
backup_root="${1:-$project_dir/backups}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="$backup_root/production-$timestamp"

mkdir -p "$target/uploads"
cd "$project_dir"
docker compose exec -T db pg_dump -U obd2sd -d obd2sd | gzip -9 > "$target/database.sql.gz"
docker compose cp backend:/data/uploads/. "$target/uploads/" >/dev/null
(cd "$target" && sha256sum database.sql.gz > SHA256SUMS && find uploads -type f -print0 | sort -z | xargs -0 -r sha256sum >> SHA256SUMS)
printf 'created_at=%s\nsource=production-postgresql\n' "$timestamp" > "$target/MANIFEST"
echo "Respaldo de producción creado en: $target"
