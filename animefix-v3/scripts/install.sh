#!/bin/bash
# AnimeFix - Script de Instalacao
# Instala dependencias e configura o sistema de controle

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=== AnimeFix - Instalacao do Sistema de Controle ===${NC}"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 nao encontrado!${NC}"
    echo -e "${YELLOW}Instale com: pkg install python${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo -e "${GREEN}Python encontrado: $PYTHON_VERSION${NC}"

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}pip3 nao encontrado. Tentando instalar...${NC}"
    python3 -m ensurepip --upgrade 2>/dev/null || {
        echo -e "${RED}Erro ao instalar pip. Execute manualmente:${NC}"
        echo -e "${YELLOW}pkg install python-pip${NC}"
        exit 1
    }
fi

# Instalar dependencias Python
echo -e "${GREEN}Instalando dependencias Python...${NC}"
pip3 install python-telegram-bot==13.15 python-dotenv --quiet
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencias Python instaladas${NC}"
else
    echo -e "${RED}❌ Erro ao instalar dependencias Python${NC}"
    exit 1
fi

# Verificar tmux
if ! command -v tmux &> /dev/null; then
    echo -e "${YELLOW}tmux nao encontrado. Instalando...${NC}"
    if command -v pkg &> /dev/null; then
        pkg install tmux -y
    elif command -v apt &> /dev/null; then
        apt update && apt install tmux -y
    else
        echo -e "${RED}Nao foi possivel instalar tmux automaticamente.${NC}"
        echo -e "${YELLOW}Execute manualmente: pkg install tmux${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ tmux encontrado${NC}"

# Verificar cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}cloudflared nao encontrado!${NC}"
    echo -e "${YELLOW}Instale manualmente seguindo:${NC}"
    echo -e "${CYAN}https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/${NC}"
    echo -e "${YELLOW}No Termux, voce pode precisar:${NC}"
    echo -e "${CYAN}pkg install cloudflared${NC}"
    echo -e "${YELLOW}Ou baixar o binario manualmente para\$PREFIX/bin/${NC}"
fi
echo -e "${GREEN}✅ cloudflared verificado${NC}"

# Criar .env a partir do template (se nao existir)
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${YELLOW}Criando arquivo .env...${NC}"
    cp "$SCRIPT_DIR/.env.template" "$SCRIPT_DIR/.env"
    echo -e "${GREEN}✅ Arquivo .env criado${NC}"
    echo -e "${YELLOW}IMPORTANTE: Edite o .env com seus tokens:${NC}"
    echo -e "${CYAN}nano $SCRIPT_DIR/.env${NC}"
else
    echo -e "${GREEN}✅ Arquivo .env ja existe${NC}"
fi

# Tornar scripts executaveis
chmod +x "$SCRIPT_DIR/start.sh"
chmod +x "$SCRIPT_DIR/stop.sh"
chmod +x "$SCRIPT_DIR/install.sh"
echo -e "${GREEN}✅ Scripts tornados executaveis${NC}"

echo ""
echo -e "${CYAN}=== Instalacao concluida! ===${NC}"
echo ""
echo -e "${YELLOW}Proximos passos:${NC}"
echo -e "1. Edite o arquivo .env com seus tokens:"
echo -e "   ${CYAN}nano $SCRIPT_DIR/.env${NC}"
echo ""
echo -e "2. Inicie o sistema:"
echo -e "   ${CYAN}./scripts/start.sh${NC}"
echo ""
echo -e "3. Pare o sistema:"
echo -e "   ${CYAN}./scripts/stop.sh${NC}"
echo ""
echo -e "${GREEN}Use o Telegram para controlar seus servicos!${NC}"
