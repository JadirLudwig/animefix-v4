#!/bin/bash
# AnimeFix - Script de Inicializacao
# Inicia uvicorn, cloudflared e o bot de controle do Telegram

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== AnimeFix - Iniciando Servicos ===${NC}"

# Verificar se tmux esta instalado
if ! command -v tmux &> /dev/null; then
    echo -e "${RED}tmux nao encontrado! Instale com: pkg install tmux${NC}"
    exit 1
fi

# Verificar se o .env existe
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${RED}Arquivo .env nao encontrado!${NC}"
    echo -e "${YELLOW}Execute: ./scripts/install.sh${NC}"
    exit 1
fi

# Carregar variaveis do .env
source "$SCRIPT_DIR/.env"

# Parar sessoes existentes (se houver)
echo -e "${YELLOW}Parando sessoes anteriores...${NC}"
tmux kill-session -t animefix 2>/dev/null
tmux kill-session -t cloudflared 2>/dev/null
tmux kill-session -t control 2>/dev/null
sleep 1

# Iniciar uvicorn (AnimeFix)
echo -e "${GREEN}Iniciando AnimeFix (uvicorn)...${NC}"
cd "$PROJECT_DIR"
tmux new-session -d -s animefix
tmux send-keys -t animefix "$UVICORN_CMD" Enter
sleep 3

# Verificar se uvicorn iniciou
if tmux has-session -t animefix 2>/dev/null; then
    echo -e "${GREEN}✅ AnimeFix iniciado na sessao 'animefix'${NC}"
else
    echo -e "${RED}❌ Erro ao iniciar AnimeFix${NC}"
fi

# Iniciar cloudflared
echo -e "${GREEN}Iniciando Cloudflared...${NC}"
tmux new-session -d -s cloudflared
tmux send-keys -t cloudflared "$CLOUDFLARED_CMD" Enter
sleep 5

# Capturar URL do Cloudflare
echo -e "${YELLOW}Aguardando URL do Cloudflare...${NC}"
sleep 3
URL=$(tmux capture-pane -p -t cloudflared 2>/dev/null | grep -oP 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' | tail -1)

if [ -n "$URL" ]; then
    echo -e "${GREEN}✅ URL do Cloudflare: $URL${NC}"
else
    echo -e "${YELLOW}⏳ URL ainda nao disponivel, sera capturada pelo bot...${NC}"
fi

# Iniciar bot de controle
echo -e "${GREEN}Iniciando Bot de Controle...${NC}"
tmux new-session -d -s control
tmux send-keys -t control "cd $SCRIPT_DIR && python telegram_control.py" Enter
sleep 2

# Verificar se o bot iniciou
if tmux has-session -t control 2>/dev/null; then
    echo -e "${GREEN}✅ Bot de Controle iniciado na sessao 'control'${NC}"
else
    echo -e "${RED}❌ Erro ao iniciar Bot de Controle${NC}"
fi

echo ""
echo -e "${GREEN}=== Todos os servicos iniciados! ===${NC}"
echo -e "${GREEN}Sessoes tmux:${NC}"
echo -e "  - animefix: uvicorn"
echo -e "  - cloudflared: tunel"
echo -e "  - control: bot telegram"
echo ""
echo -e "${YELLOW}Comandos uteis:${NC}"
echo -e "  tmux attach -t animefix    # Ver logs do uvicorn"
echo -e "  tmux attach -t cloudflared # Ver logs do cloudflared"
echo -e "  tmux attach -t control     # Ver logs do bot"
echo ""
echo -e "${GREEN}Use o Telegram para controlar os servicos!${NC}"
