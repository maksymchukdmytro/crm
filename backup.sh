#!/bin/sh
# Резервна копія бази. Запускайте з папки проєкту, наприклад щодня з cron:
#   15 3 * * * cd /opt/crm && ./backup.sh >> backups/backup.log 2>&1
set -e
mkdir -p backups
FILE="backups/crm-$(date +%Y%m%d-%H%M).sql.gz"
docker compose exec -T db pg_dump -U crm crm | gzip > "$FILE"
echo "$(date) збережено $FILE"
# зберігаємо копії за останні 30 днів
find backups -name 'crm-*.sql.gz' -mtime +30 -delete
