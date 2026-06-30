#!/bin/bash
# AnimeFix - Iniciar cloudflared e salvar URL em arquivo
LOG_FILE="/tmp/animefix_cloudflared.log"
> "$LOG_FILE"
cloudflared tunnel --url http://localhost:8000 2>&1 | while IFS= read -r line; do
    echo "$line"
    echo "$line" >> "$LOG_FILE"
    if echo "$line" | grep -qoP 'https://[a-zA-Z0-9\-]+\.trycloudflare\.com'; then
        URL=$(echo "$line" | grep -oP 'https://[a-zA-Z0-9\-]+\.trycloudflare\.com')
        echo "$URL" > /tmp/animefix_url.txt
    fi
done
