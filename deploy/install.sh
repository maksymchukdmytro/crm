#!/usr/bin/env bash
# Встановлення або оновлення CRM на Ubuntu без Docker — поруч з іншими сайтами під nginx.
# Можна запускати повторно: оновлює код і перезапускає CRM, база не зачіпається.
#
#   sudo bash deploy/install.sh <домен> [префікс] [файл сайту nginx]
#   sudo bash deploy/install.sh mdmy.me /crm /etc/nginx/sites-available/mdmy
#
# Що робить:
#   1) ставить PostgreSQL (якщо його ще немає), створює базу crm;
#   2) копіює код у /opt/crm, Python-середовище в /opt/crm/.venv, застосовує міграції;
#   3) служби systemd: crm-web (127.0.0.1:8020) і crm-worker (SMS, трекінг);
#   4) додає в наявний сайт nginx адресу <префікс>/ (окремий файл /etc/nginx/snippets/crm.conf);
#   5) щоденна копія бази о 03:45 у /var/backups/crm (14 останніх).
# Налаштування й секрети — /etc/crm/crm.env (створюється один раз).
set -euo pipefail

DOMAIN="${1:-}"
ROOT="${2:-/crm}"
SITE="${3:-}"
APP=/opt/crm
ETC=/etc/crm
ENVF=$ETC/crm.env
BACKUP_DIR=/var/backups/crm
APP_USER=crm
PORT="${CRM_PORT:-8020}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

say()  { printf '\n\033[1;34m▶ CRM: %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m⚠ CRM: %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m✖ CRM: %s\033[0m\n' "$*"; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Запустіть від root"
[[ "$DOMAIN" =~ ^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]] || die "Вкажіть домен: sudo bash deploy/install.sh mdmy.me /crm"
[[ "$ROOT" =~ ^/[A-Za-z0-9_-]+$ ]] || die "Префікс має виглядати як /crm"
[ -f "$SRC/app/main.py" ] || die "Не знайдено app/main.py — запускайте з репозиторію CRM"
export DEBIAN_FRONTEND=noninteractive

say "1/5 Пакети і PostgreSQL"
NEED=()
command -v pg_ctlcluster >/dev/null || NEED+=(postgresql)
python3 -c 'import ensurepip, venv' 2>/dev/null || NEED+=(python3-venv)
command -v rsync >/dev/null || NEED+=(rsync)
if [ ${#NEED[@]} -gt 0 ]; then
  apt-get update -qq
  apt-get install -y -qq "${NEED[@]}" >/dev/null
fi
systemctl enable --now postgresql >/dev/null 2>&1 || true
PYV="$(python3 -c 'import sys; print("%d%02d" % sys.version_info[:2])')"
[ "$PYV" -ge 310 ] || die "Потрібен Python 3.10+, на сервері $(python3 -V)"

id "$APP_USER" >/dev/null 2>&1 || useradd --system --home "$APP" --shell /usr/sbin/nologin "$APP_USER"
install -d -m 750 -o root -g "$APP_USER" "$ETC"

if [ ! -s "$ENVF" ]; then

  DB_PASS="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
  ADMIN_PASS="$(head -c 9 /dev/urandom | od -An -tx1 | tr -d ' \n')"
  ( umask 027
    cat > "$ENVF" <<EOF
# Налаштування CRM (створено $(date +%F)). Після змін: systemctl restart crm-web crm-worker
DATABASE_URL=postgresql+psycopg://crm:${DB_PASS}@127.0.0.1:5432/crm
SECRET_KEY=$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')
ADMIN_USERNAME=admin
ADMIN_PASSWORD=${ADMIN_PASS}
ROOT_PATH=${ROOT}
DISPLAY_TZ=Europe/Kyiv
WORKER_TICK=30
EOF
  )
  echo "admin / ${ADMIN_PASS}" > "$ETC/initial-admin.txt"
  chmod 600 "$ETC/initial-admin.txt"
fi
chown root:"$APP_USER" "$ENVF"; chmod 640 "$ENVF"
# HTTPS є — cookie лише через https
HTTPS_ONLY=0; [ -d "/etc/letsencrypt/live/$DOMAIN" ] && HTTPS_ONLY=1
sed -i '/^HTTPS_ONLY=/d;/^ROOT_PATH=/d' "$ENVF"
printf 'HTTPS_ONLY=%s\nROOT_PATH=%s\n' "$HTTPS_ONLY" "$ROOT" >> "$ENVF"

DB_PASS="$(sed -n 's#^DATABASE_URL=postgresql+psycopg://crm:\([^@]*\)@.*#\1#p' "$ENVF")"
[ -n "$DB_PASS" ] || die "Не вдалося прочитати пароль бази з $ENVF"
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='crm'" | grep -q 1; then
  sudo -u postgres psql -q -c "CREATE ROLE crm LOGIN PASSWORD '${DB_PASS}'"
fi
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='crm'" | grep -q 1; then
  sudo -u postgres psql -q -c "CREATE DATABASE crm OWNER crm ENCODING 'UTF8' TEMPLATE template0"
fi

say "2/5 Код і Python-середовище"
mkdir -p "$APP" "$BACKUP_DIR"
rsync -a --delete --exclude '.git' --exclude '.venv' --exclude tests --exclude backups --exclude '__pycache__' \
  --exclude '.env' "$SRC/" "$APP/"
git -C "$SRC" log -1 --format='%h · %cd' --date=format:'%Y-%m-%d %H:%M' > "$APP/VERSION" 2>/dev/null || true
chown -R "$APP_USER:$APP_USER" "$APP" "$BACKUP_DIR"
chmod 750 "$BACKUP_DIR"
[ -x "$APP/.venv/bin/python" ] || sudo -u "$APP_USER" python3 -m venv "$APP/.venv"
REQ_HASH="$(sha256sum "$APP/requirements.txt" | cut -c1-16)"
if [ "$(cat "$APP/.venv/.req" 2>/dev/null)" != "$REQ_HASH" ]; then
  sudo -u "$APP_USER" env HOME="$APP" "$APP/.venv/bin/pip" install -q --upgrade pip
  sudo -u "$APP_USER" env HOME="$APP" "$APP/.venv/bin/pip" install -q -r "$APP/requirements.txt"
  echo "$REQ_HASH" > "$APP/.venv/.req"; chown "$APP_USER:$APP_USER" "$APP/.venv/.req"
fi

say "3/5 Міграції бази і служби"
if sudo -u postgres psql -d crm -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='orders'" | grep -q 1; then
  sudo -u postgres pg_dump crm | gzip > "$BACKUP_DIR/pre-update-$(date +%F-%H%M%S).sql.gz"
  ls -1t "$BACKUP_DIR"/pre-update-*.sql.gz 2>/dev/null | tail -n +6 | xargs -r rm -f
fi
# shellcheck disable=SC1090
( cd "$APP" && set -a && . "$ENVF" && set +a && sudo -u "$APP_USER" --preserve-env=DATABASE_URL,SECRET_KEY \
  "$APP/.venv/bin/alembic" upgrade head )

unit() { # назва, опис, команда
  cat > "/etc/systemd/system/$1.service" <<EOF
[Unit]
Description=$2
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP
EnvironmentFile=$ENVF
ExecStart=$3
Restart=always
RestartSec=3
NoNewPrivileges=true
ProtectSystem=full
ProtectHome=true
PrivateTmp=true
MemoryMax=600M

[Install]
WantedBy=multi-user.target
EOF
}
unit crm-web "CRM — веб ($DOMAIN$ROOT)" \
  "$APP/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port $PORT --workers 2 --proxy-headers --forwarded-allow-ips 127.0.0.1"
unit crm-worker "CRM — фонові задачі (SMS, трекінг)" "$APP/.venv/bin/python worker.py"
systemctl daemon-reload
systemctl enable crm-web crm-worker >/dev/null 2>&1
systemctl restart crm-web crm-worker
for _ in $(seq 1 30); do sleep 1; curl -fsS "http://127.0.0.1:$PORT/healthz" >/dev/null 2>&1 && break; done
curl -fsS "http://127.0.0.1:$PORT/healthz" >/dev/null || { journalctl -u crm-web -n 40 --no-pager; die "CRM не запустилася (журнал вище)"; }
echo "CRM працює на 127.0.0.1:$PORT"

say "4/5 Nginx: $DOMAIN$ROOT/"
mkdir -p /etc/nginx/snippets
cat > /etc/nginx/snippets/crm.conf <<EOF
# CRM за адресою $ROOT/ (створено deploy/install.sh репозиторію crm)
location = $ROOT { return 301 $ROOT/; }
location $ROOT/ {
    proxy_pass http://127.0.0.1:$PORT/;
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$remote_addr;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_read_timeout 120s;
    client_max_body_size 10m;
}
EOF
if [ -n "$SITE" ] && [ -f "$SITE" ]; then
  if ! grep -q 'snippets/crm.conf' "$SITE"; then
    cp "$SITE" "/root/$(basename "$SITE").before-crm"
    # перед кожним «location / {» (і в блоці 80, і в блоці 443 від certbot)
    sed -i 's#^\(\s*\)location / {#\1include snippets/crm.conf;\n\1location / {#' "$SITE"
  fi
  if nginx -t 2>/dev/null; then
    systemctl reload nginx
  else
    warn "nginx не прийняв налаштування — повертаю попередній файл сайту"
    [ -f "/root/$(basename "$SITE").before-crm" ] && cp "/root/$(basename "$SITE").before-crm" "$SITE"
    nginx -t && systemctl reload nginx
  fi
else
  warn "Файл сайту nginx не вказано — додайте вручну в server { … }:  include snippets/crm.conf;"
fi

say "5/5 Щоденна резервна копія"
cat > /etc/cron.d/crm-backup <<EOF
# CRM: копія бази щодня о 03:45, зберігаються 14 останніх
45 3 * * * postgres pg_dump crm | gzip > $BACKUP_DIR/crm-\$(date +\%F).sql.gz; ls -1t $BACKUP_DIR/crm-*.sql.gz | tail -n +15 | xargs -r rm -f
EOF
chmod 644 /etc/cron.d/crm-backup
chown postgres:"$APP_USER" "$BACKUP_DIR"; chmod 770 "$BACKUP_DIR"

SCHEME=http; [ "$HTTPS_ONLY" = 1 ] && SCHEME=https
say "Готово: $SCHEME://$DOMAIN$ROOT/"
# пароль першого входу показуємо, доки в CRM ще ніхто не входив (навіть якщо перша спроба встановлення обірвалась)
if [ -f "$ETC/initial-admin.txt" ] && ! sudo -u postgres psql -d crm -tAc \
     "SELECT 1 FROM users WHERE last_login_at IS NOT NULL LIMIT 1" 2>/dev/null | grep -q 1; then
  echo "  Перший вхід: $(cat "$ETC/initial-admin.txt")  — змініть пароль у профілі CRM."
  echo "  (той самий пароль збережено у $ETC/initial-admin.txt)"
fi
echo "  Журнали: journalctl -u crm-web -u crm-worker -f"
echo "  Налаштування: $ENVF · копії бази: $BACKUP_DIR"
