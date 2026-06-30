#!/bin/bash
# AnimeFix - Script de Parada
# Para todos os servicos do AnimeFix

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== AnimeFix - Parando Servicos ===${NC}"

# Parar sessoes tmux
for SESSION in animefix cloudflared control; do
    if tmux has-session -t "$SESSION" 2>/dev/null; then
        echo -e "${YELLOW}Parando sessao '$SESSION'...${NC}"
        tmux kill-session -t "$SESSION"
        echo -e "${GREEN}✅ Sessao '$SESSION' parada${NC}"
    else
        echo -e "${YELLOW}Sessao '$SESSION' nao encontrada${NC}"
    fi
done

# Matar processos uvicorn e cloudflared que possam ter escapado
echo -e "${YELLOW}Verificando processos restantes...${NC}"
pkill -f "uvicorn.*app.main:app" 2>/dev/null
pkill -f "cloudflared tunnel" 2>/dev/null

echo ""
echo -e "${GREEN}=== Todos os servicos parados! ===${NC}"
