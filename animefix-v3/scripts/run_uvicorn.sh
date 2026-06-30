#!/bin/bash
# AnimeFix - Iniciar uvicorn
cd /data/data/com.termux/files/home/animefix-v3
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
