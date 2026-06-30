#!/bin/bash
# AnimeFix - Script de Inicializacao (v2)
# Inicia uvicorn, cloudflared e o bot de controle do Telegram

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== AnimeFix - Iniciando Servicos ===${NC}"
echo -e "${YELLOW}Projeto: $PROJECT_DIR${NC}"
echo ""

# Tornar scripts executaveis
chmod +x "$SCRIPT_DIR/run_uvicorn.sh"
chmod +x "$SCRIPT_DIR/run_cloudflared.sh"
chmod +x "$SCRIPT_DIR/run_bot.sh"

# Parar sessoes existentes
echo -e "${YELLOW}Parando sessoes anteriores...${NC}"
tmux kill-session -t animefix 2>/dev/null
tmux kill-session -t cloudflared 2>/dev/null
tmux kill-session -t control 2>/dev/null
sleep 1

# ===== INICIAR UVICORN =====
echo -e "${GREEN}[1/3] Iniciando AnimeFix...${NC}"
tmux new-session -d -s animefix "$SCRIPT_DIR/run_uvicorn.sh"
sleep 3

if ss -tlnp 2>/dev/null | grep -q ":8000"; then
    echo -e "${GREEN}✅ AnimeFix rodando na porta 8000${NC}"
else
    echo -e "${RED}❌ AnimeFix pode nao ter iniciado${NC}"
    echo -e "${YELLOW}Logs:${NC}"
    tmux capture-pane -p -t animefix 2>/dev/null | tail -10
fi

# ===== INICIAR CLOUDFLARED =====
echo -e "${GREEN}[2/3] Iniciando Cloudflared...${NC}"
tmux new-session -d -s cloudflared "$SCRIPT_DIR/run_cloudflared.sh"
sleep 8

URL=$(tmux capture-pane -p -t cloudflared 2>/dev/null | grep -oP 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' | tail -1)
if [ -n "$URL" ]; then
    echo -e "${GREEN}✅ URL: $URL${NC}"
else
    echo -e "${YELLOW}⏳ URL ainda nao disponivel...${NC}"
fi

# ===== INICIAR BOT =====
echo -e "${GREEN}[3/3] Iniciando Bot...${NC}"
tmux new-session -d -s control "$SCRIPT_DIR/run_bot.sh"
sleep 2

if tmux has-session -t control 2>/dev/null; then
    echo -e "${GREEN}✅ Bot iniciado${NC}"
else
    echo -e "${RED}❌ Bot nao iniciou${NC}"
fi

# ===== RESUMO =====
echo ""
echo -e "${GREEN}=== Status ===${NC}"
echo -e "  uvicorn:    $(ss -tlnp 2>/dev/null | grep -q ':8000' && echo '✅ Online' || echo '❌ Offline')"
echo -e "  cloudflared: $(tmux has-session -t cloudflared 2>/dev/null && echo '✅ Online' || echo '❌ Offline')"
echo -e "  bot:        $(tmux has-session -t control 2>/dev/null && echo '✅ Online' || echo '❌ Offline')"
[ -n "$URL" ] && echo -e "\n  🌐 URL: $URL"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  tmux attach -t animefix"
echo -e "  tmux attach -t cloudflared"
echo -e "  tmux attach -t control"
echo ""
