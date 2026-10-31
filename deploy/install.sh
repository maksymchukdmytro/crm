#!/usr/bin/env bash
# Встановлення або оновлення CRM на Ubuntu без Docker — поруч з іншими сайтами під nginx.
# Можна запускати повторно: оновлює код і перезапускає CRM, база не зачіпається.
#
#   sudo bash deploy/install.sh <домен> [префікс] [файл сайту nginx]
#   sudo bash deploy/install.sh mdmy.me /crm /etc/nginx/sites-available/mdmy
#
# Що робить:
#   1) ставить PostgreSQL і Redis (якщо їх ще немає), створює базу crm;
#   2) копіює код у /opt/crm, Python-середовище в /opt/crm/.venv, збирає інтерфейс (Node.js), застосовує міграції;
#   3) служби systemd: crm-web (127.0.0.1:8020) і crm-worker (черга задач arq: SMS, ТТН, трекінг);
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

say "1/5 Пакети, PostgreSQL і Redis"
NEED=()
command -v pg_ctlcluster >/dev/null || NEED+=(postgresql)
command -v redis-server >/dev/null || NEED+=(redis-server)
python3 -c 'import ensurepip, venv' 2>/dev/null || NEED+=(python3-venv)
command -v rsync >/dev/null || NEED+=(rsync)
if [ ${#NEED[@]} -gt 0 ]; then
  apt-get update -qq
  apt-get install -y -qq "${NEED[@]}" >/dev/null
fi
systemctl enable --now postgresql >/dev/null 2>&1 || true
systemctl enable --now redis-server >/dev/null 2>&1 || true
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
# Токен для метрик Prometheus (/crm/api/metrics); Sentry вмикається вручну: SENTRY_DSN=... у цьому файлі
grep -q '^METRICS_TOKEN=' "$ENVF" || echo "METRICS_TOKEN=$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')" >> "$ENVF"
grep -q '^SENTRY_DSN=' "$ENVF" || printf '# SENTRY_DSN=https://...@sentry.io/...      (помилки сервера й воркера)\n# SENTRY_DSN_FRONTEND=https://...           (помилки в браузері)\nSENTRY_DSN=\n' >> "$ENVF"
# Черга задач і події в реальному часі: окрема база Redis №3 (щоб не перетинатися з іншими сайтами)
if ! grep -q '^REDIS_URL=' "$ENVF"; then
  if redis-cli -n 3 ping 2>/dev/null | grep -q PONG; then
    echo "REDIS_URL=redis://127.0.0.1:6379/3" >> "$ENVF"
  else
    warn "Redis недоступний — CRM працюватиме без черги (задачі виконуються одразу, інтерфейс оновлюється раз на 30 с)"
  fi
fi

# Фото товарів — поза $APP (там rsync --delete), щоб оновлення їх не стирало
grep -q '^MEDIA_DIR=' "$ENVF" || echo "MEDIA_DIR=/var/lib/crm/media" >> "$ENVF"
MEDIA_DIR="$(sed -n 's/^MEDIA_DIR=//p' "$ENVF" | tail -n 1)"
install -d -m 750 -o "$APP_USER" -g "$APP_USER" "$(dirname "$MEDIA_DIR")" "$MEDIA_DIR"

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
rsync -a --delete --exclude '.git' --exclude '.claude' --exclude '.venv' --exclude tests --exclude backups --exclude '__pycache__' \
  --exclude '.env' --exclude 'frontend/node_modules' --exclude 'frontend/dist' --exclude '.npm' "$SRC/" "$APP/"
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

# Інтерфейс (React): збирається лише коли змінився його код. Без Node.js лишається попередня збірка.
FE="$APP/frontend"
NODE_MAJOR=0; command -v node >/dev/null && NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
if [ -f "$FE/package.json" ] && [ "$NODE_MAJOR" -ge 18 ]; then
  FE_HASH="$(cd "$FE" && { cat package-lock.json index.html vite.config.ts tsconfig.json; find src -type f -print0 | sort -z | xargs -0 cat; } | sha256sum | cut -c1-16)"
  if [ "$(cat "$FE/dist/.build" 2>/dev/null)" != "$FE_HASH" ]; then
    say "Збірка інтерфейсу"
    LOCK_HASH="$(sha256sum "$FE/package-lock.json" | cut -c1-16)"
    npm_as() { sudo -u "$APP_USER" env HOME="$APP" npm --prefix "$FE" --cache "$APP/.npm" --no-audit --no-fund "$@"; }
    chown -R "$APP_USER:$APP_USER" "$FE"
    if [ "$(cat "$FE/node_modules/.lock" 2>/dev/null)" != "$LOCK_HASH" ]; then
      npm_as ci --loglevel=error && echo "$LOCK_HASH" > "$FE/node_modules/.lock"
    fi
    if npm_as run build --silent; then
      echo "$FE_HASH" > "$FE/dist/.build"
    else
      warn "Інтерфейс не зібрався — працює попередня збірка"
    fi
    chown -R "$APP_USER:$APP_USER" "$FE"
  fi
else
  warn "Node.js 18+ не знайдено — інтерфейс не зібрано, працює попередня збірка"
fi

say "3/5 Міграції бази і служби"
if sudo -u postgres psql -d crm -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='orders'" | grep -q 1; then
  sudo -u postgres pg_dump crm | gzip > "$BACKUP_DIR/pre-update-$(date +%F-%H%M%S).sql.gz"
  ls -1t "$BACKUP_DIR"/pre-update-*.sql.gz 2>/dev/null | tail -n +6 | xargs -r rm -f
fi
# shellcheck disable=SC1090
( cd "$APP" && set -a && . "$ENVF" && set +a && sudo -u "$APP_USER" --preserve-env=DATABASE_URL,SECRET_KEY \
  "$APP/.venv/bin/alembic" upgrade head )

unit() { # назва, опис, команда, [додаткові рядки секції Service]
  cat > "/etc/systemd/system/$1.service" <<EOF
[Unit]
Description=$2
After=network.target postgresql.service redis-server.service
Requires=postgresql.service
Wants=redis-server.service

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
${4:-}

[Install]
WantedBy=multi-user.target
EOF
}
# метрики кількох процесів uvicorn збираються в спільному каталозі (очищується при кожному перезапуску)
unit crm-web "CRM — веб ($DOMAIN$ROOT)" \
  "$APP/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port $PORT --workers 2 --proxy-headers --forwarded-allow-ips 127.0.0.1" \
  "RuntimeDirectory=crm-web
Environment=PROMETHEUS_MULTIPROC_DIR=/run/crm-web"
unit crm-worker "CRM — фонові задачі (SMS, трекінг)" "$APP/.venv/bin/python worker.py"
systemctl daemon-reload
systemctl enable crm-web crm-worker >/dev/null 2>&1
systemctl restart crm-web crm-worker
for _ in $(seq 1 30); do sleep 1; curl -fsS "http://127.0.0.1:$PORT/healthz" >/dev/null 2>&1 && break; done
curl -fsS "http://127.0.0.1:$PORT/healthz" >/dev/null || { journalctl -u crm-web -n 40 --no-pager; die "CRM не запустилася (журнал вище)"; }
echo "CRM працює на 127.0.0.1:$PORT"

# Разова заміна пароля admin (хеш PBKDF2, сам пароль не зберігається в репозиторії).
# Діє лише поки admin ще жодного разу не входив; після першого входу нічого не змінює.
ADMIN_RESET_HASH='pbkdf2_sha256$260000$e634822d0f0317f87ed5395de2f9155f$f04f9fca70bef501068dfba3418da195d56af9a18e16497ff5e5d0dd01187ad6'
if sudo -u postgres psql -d crm -tAc "SELECT 1 FROM users WHERE username='admin' AND last_login_at IS NULL" | grep -q 1 \
   && ! sudo -u postgres psql -d crm -tAc "SELECT 1 FROM users WHERE username='admin' AND password_hash='$ADMIN_RESET_HASH'" | grep -q 1; then
  sudo -u postgres psql -d crm -q -c "UPDATE users SET password_hash='$ADMIN_RESET_HASH' WHERE username='admin' AND last_login_at IS NULL"
  echo "admin / пароль, який Claude надіслав у чаті" > "$ETC/initial-admin.txt"
  echo "Пароль admin замінено на той, що надіслано в чаті"
fi

say "4/5 Nginx: $DOMAIN$ROOT/"
mkdir -p /etc/nginx/snippets
cat > /etc/nginx/snippets/crm.conf <<EOF
# CRM за адресою $ROOT/ (створено deploy/install.sh репозиторію crm)
location = $ROOT { return 301 $ROOT/; }
# події в реальному часі (SSE): без буферизації і з довгим таймаутом
location = $ROOT/api/events {
    proxy_pass http://127.0.0.1:$PORT/api/events;
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_set_header X-Forwarded-For \$remote_addr;
    proxy_set_header Connection "";
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 1h;
}
# файли збірки інтерфейсу мають хеш у назві — кешуємо надовго
location $ROOT/assets/ {
    proxy_pass http://127.0.0.1:$PORT/assets/;
    proxy_set_header Host \$host;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
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
# фото товарів — дзеркало поруч із копіями бази
50 3 * * * root rsync -a --delete $MEDIA_DIR/ $BACKUP_DIR/media/
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
echo "  Стан: $SCHEME://$DOMAIN$ROOT/system · для зовнішнього монітора: $SCHEME://$DOMAIN$ROOT/healthz/full"
echo "  Налаштування: $ENVF · копії бази: $BACKUP_DIR"
