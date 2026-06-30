#!/bin/bash
# Diagnostico do AnimeFix

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Diagnostico AnimeFix ===${NC}"
echo ""

echo -e "${YELLOW}[1] Verificando diretorio do projeto...${NC}"
echo "  PROJECT_DIR: $PROJECT_DIR"
ls -la "$PROJECT_DIR/app/main.py" 2>/dev/null && echo -e "  ${GREEN}main.py encontrado${NC}" || echo -e "  ${RED}main.py NAO encontrado!${NC}"
echo ""

echo -e "${YELLOW}[2] Verificando uvicorn...${NC}"
which uvicorn && uvicorn --version 2>&1 || echo -e "  ${RED}uvicorn nao encontrado no PATH${NC}"
echo ""

echo -e "${YELLOW}[3] Verificando cloudflared...${NC}"
which cloudflared && cloudflared --version 2>&1 || echo -e "  ${RED}cloudflared nao encontrado no PATH${NC}"
echo ""

echo -e "${YELLOW}[4] Verificando python...${NC}"
which python3 && python3 --version 2>&1 || echo -e "  ${RED}python3 nao encontrado${NC}"
echo ""

echo -e "${YELLOW}[5] Verificando .env...${NC}"
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo -e "  ${GREEN}.env encontrado${NC}"
    cat "$SCRIPT_DIR/.env" | grep -v "^#" | sed 's/\(TOKEN=\).*/\1***HIDDEN***/' | sed 's/\(CHAT_ID=\).*/\1***HIDDEN***/'
else
    echo -e "  ${RED}.env NAO encontrado!${NC}"
fi
echo ""

echo -e "${YELLOW}[6] Testando uvicorn direto (5 segundos)...${NC}"
cd "$PROJECT_DIR"
timeout 5 python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 || echo -e "  ${YELLOW}Uvicorn encerrado (timeout normal)${NC}"
echo ""

echo -e "${YELLOW}[7] Verificando portas em uso...${NC}"
ss -tlnp 2>/dev/null | grep ":8000" && echo -e "  ${GREEN}Porta 8000 em uso${NC}" || echo -e "  ${YELLOW}Porta 8000 livre${NC}"
echo ""

echo -e "${YELLOW}[8] Verificando sessoes tmux...${NC}"
tmux ls 2>/dev/null || echo -e "  ${YELLOW}Nenhuma sessao tmux ativa${NC}"
echo ""

echo -e "${YELLOW}=== Fim do Diagnostico ===${NC}"
