#!/bin/bash
# перезапуск локальних серверів CRM (окремий файл, щоб не вбити власну оболонку)
for p in $(pgrep -f "app.main:app --port 80"); do kill $p; done
sleep 1
cd /home/claude/crm
SECRET_KEY=localtestsecretkey1234567890abcdef DATABASE_URL=postgresql+psycopg://crm:crm@localhost:5432/crm_ui nohup python3 -m uvicorn app.main:app --port 8077 > /tmp/claude-0/u77.log 2>&1 &
SECRET_KEY=localtestsecretkey1234567890abcdef DATABASE_URL=postgresql+psycopg://crm:crm@localhost:5432/crm_stress nohup python3 -m uvicorn app.main:app --port 8078 > /tmp/claude-0/u78.log 2>&1 &
