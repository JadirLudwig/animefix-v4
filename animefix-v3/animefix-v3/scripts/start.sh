#!/bin/bash
# AnimeFix - Script de Inicializacao
# Inicia uvicorn, cloudflared e o bot de controle do Telegram

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== AnimeFix - Iniciando Servicos ===${NC}"
echo -e "${YELLOW}Diretorio do projeto: $PROJECT_DIR${NC}"
echo ""

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

# Verificar se uvicorn esta disponivel
if ! command -v uvicorn &> /dev/null; then
    echo -e "${RED}uvicorn nao encontrado! Instale com: pip install uvicorn${NC}"
    exit 1
fi

# Verificar se cloudflared esta disponivel
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}cloudflared nao encontrado!${NC}"
    echo -e "${YELLOW}Instale com: pkg install cloudflared${NC}"
    exit 1
fi

# Parar sessoes existentes (se houver)
echo -e "${YELLOW}Parando sessoes anteriores...${NC}"
tmux kill-session -t animefix 2>/dev/null
tmux kill-session -t cloudflared 2>/dev/null
tmux kill-session -t control 2>/dev/null
sleep 1

# ===== INICIAR UVICORN =====
echo -e "${GREEN}[1/3] Iniciando AnimeFix (uvicorn)...${NC}"
tmux new-session -d -s animefix -c "$PROJECT_DIR"
sleep 0.5
tmux send-keys -t animefix "$UVICORN_CMD" Enter
sleep 4

# Verificar se uvicorn realmente iniciou (porta em uso)
if ss -tlnp 2>/dev/null | grep -q ":${PORT}"; then
    echo -e "${GREEN}✅ AnimeFix rodando na porta $PORT${NC}"
else
    echo -e "${RED}❌ AnimeFix pode nao ter iniciado. Verificando logs...${NC}"
    tmux capture-pane -p -t animefix 2>/dev/null | tail -5
    echo ""
fi

# ===== INICIAR CLOUDFLARED =====
echo -e "${GREEN}[2/3] Iniciando Cloudflared...${NC}"
tmux new-session -d -s cloudflared -c "$PROJECT_DIR"
sleep 0.5
tmux send-keys -t cloudflared "$CLOUDFLARED_CMD" Enter
sleep 5

# Capturar URL do Cloudflare
echo -e "${YELLOW}Aguardando URL do Cloudflare...${NC}"
for i in 1 2 3 4 5 6; do
    URL=$(tmux capture-pane -p -t cloudflared 2>/dev/null | grep -oP 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' | tail -1)
    if [ -n "$URL" ]; then
        break
    fi
    sleep 2
done

if [ -n "$URL" ]; then
    echo -e "${GREEN}✅ URL do Cloudflare: $URL${NC}"
else
    echo -e "${YELLOW}⏳ URL ainda nao disponivel (pode demorar)...${NC}"
fi

# ===== INICIAR BOT =====
echo -e "${GREEN}[3/3] Iniciando Bot de Controle...${NC}"
tmux new-session -d -s control -c "$SCRIPT_DIR"
sleep 0.5
tmux send-keys -t control "python3 telegram_control.py" Enter
sleep 2

if tmux has-session -t control 2>/dev/null; then
    echo -e "${GREEN}✅ Bot de Controle iniciado${NC}"
else
    echo -e "${RED}❌ Erro ao iniciar Bot de Controle${NC}"
fi

echo ""
echo -e "${GREEN}=== Verificacao Final ===${NC}"

# Status final
if ss -tlnp 2>/dev/null | grep -q ":${PORT}"; then
    echo -e "  AnimeFix:   ✅ Online (porta $PORT)"
else
    echo -e "  AnimeFix:   ❌ Offline"
fi

if tmux has-session -t cloudflared 2>/dev/null; then
    echo -e "  Cloudflared: ✅ Online"
else
    echo -e "  Cloudflared: ❌ Offline"
fi

if tmux has-session -t control 2>/dev/null; then
    echo -e "  Bot:        ✅ Online"
else
    echo -e "  Bot:        ❌ Offline"
fi

if [ -n "$URL" ]; then
    echo ""
    echo -e "${GREEN}🌐 URL: $URL${NC}"
fi

echo ""
echo -e "${YELLOW}Comandos uteis:${NC}"
echo -e "  tmux attach -t animefix    # Ver logs uvicorn"
echo -e "  tmux attach -t cloudflared # Ver logs cloudflared"
echo -e "  tmux attach -t control     # Ver logs bot"
echo -e "  ./scripts/stop.sh          # Parar tudo"
echo ""
