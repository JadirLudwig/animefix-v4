#!/usr/bin/env python3
"""
AnimeFix Telegram Control Bot
Bot de controle e monitoramento para o sistema AnimeFix v3.
Gerencia uvicorn, cloudflared e envia URL efemera via Telegram.
"""

import os
import re
import sys
import time
import signal
import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/tmp/animefix-bot.log"),
    ],
)
logger = logging.getLogger(__name__)

# Carregar variaveis de ambiente
SCRIPT_DIR = Path(__file__).parent
ENV_PATH = SCRIPT_DIR / ".env"
load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = int(os.getenv("CHAT_ID", "0"))
PORT = int(os.getenv("PORT", "8000"))
UVICORN_CMD = os.getenv("UVICORN_CMD", "uvicorn app.main:app --host 0.0.0.0 --port 8000")
CLOUDFLARED_CMD = os.getenv("CLOUDFLARED_CMD", "cloudflared tunnel --url http://localhost:8000")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))

# Validar config
if not BOT_TOKEN:
    logger.error("BOT_TOKEN nao encontrado no .env")
    sys.exit(1)
if CHAT_ID == 0:
    logger.error("CHAT_ID nao encontrado no .env")
    sys.exit(1)

# Identificadores das sessoes tmux
TMUX_SESSIONS = {
    "animefix": UVICORN_CMD,
    "cloudflared": CLOUDFLARED_CMD,
}


def is_authorized(update: Update) -> bool:
    """Verifica se o usuario e o CHAT_ID autorizado."""
    return update.effective_user.id == CHAT_ID


def run_tmux_cmd(session: str, cmd: str) -> bool:
    """Executa um comando dentro de uma sessao tmux existente."""
    try:
        subprocess.run(
            ["tmux", "send-keys", "-t", session, cmd, "Enter"],
            capture_output=True,
            timeout=5,
        )
        return True
    except Exception as e:
        logger.error(f"Erro ao executar comando na sessao {session}: {e}")
        return False


def tmux_session_exists(session: str) -> bool:
    """Verifica se uma sessao tmux existe."""
    try:
        result = subprocess.run(
            ["tmux", "has-session", "-t", session],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def kill_tmux_session(session: str) -> bool:
    """Mata uma sessao tmux."""
    try:
        subprocess.run(
            ["tmux", "kill-session", "-t", session],
            capture_output=True,
            timeout=5,
        )
        return True
    except Exception as e:
        logger.error(f"Erro ao matar sessao {session}: {e}")
        return False


def is_port_in_use(port: int) -> bool:
    """Verifica se a porta esta em uso."""
    try:
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return f":{port}" in result.stdout
    except Exception:
        return False


def get_cloudflared_url() -> str:
    """Captura a URL efemera do Cloudflare a partir dos logs do tmux."""
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", "cloudflared", "-p"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout
        # Procurar padrao de URL do trycloudflare
        urls = re.findall(
            r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com[^\s]*",
            output,
        )
        if urls:
            return urls[-1]
        # Fallback: procurar https:// generico
        urls = re.findall(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", output)
        if urls:
            return urls[-1]
        return ""
    except Exception as e:
        logger.error(f"Erro ao capturar URL do Cloudflare: {e}")
        return ""


def start_animefix(context: CallbackContext) -> None:
    """Inicia a sessao tmux do animefix (uvicorn)."""
    if tmux_session_exists("animefix"):
        logger.info("Sessao animefix ja existe")
        return

    try:
        subprocess.run(
            ["tmux", "new-session", "-d", "-s", "animefix"],
            capture_output=True,
            timeout=5,
        )
        # Navegar para o diretorio do projeto e iniciar uvicorn
        project_dir = SCRIPT_DIR.parent
        run_tmux_cmd("animefix", f"cd {project_dir} && {UVICORN_CMD}")
        logger.info("Sessao animefix iniciada")
    except Exception as e:
        logger.error(f"Erro ao iniciar animefix: {e}")


def start_cloudflared(context: CallbackContext) -> None:
    """Inicia a sessao tmux do cloudflared."""
    if tmux_session_exists("cloudflared"):
        logger.info("Sessao cloudflared ja existe")
        return

    try:
        subprocess.run(
            ["tmux", "new-session", "-d", "-s", "cloudflared"],
            capture_output=True,
            timeout=5,
        )
        run_tmux_cmd("cloudflared", CLOUDFLARED_CMD)
        logger.info("Sessao cloudflared iniciada")
    except Exception as e:
        logger.error(f"Erro ao iniciar cloudflared: {e}")


def monitor_services(context: CallbackContext) -> None:
    """Verifica a saude dos servicos e envia alertas."""
    if not context.job_queue:
        return

    animefix_ok = tmux_session_exists("animefix")
    cloudflared_ok = tmux_session_exists("cloudflared")
    port_ok = is_port_in_use(PORT)

    # Verificar se o processo uvicorn ainda esta rodando
    uvicorn_running = False
    if animefix_ok:
        try:
            result = subprocess.run(
                ["pgrep", "-f", "uvicorn"],
                capture_output=True,
                timeout=5,
            )
            uvicorn_running = result.returncode == 0
        except Exception:
            pass

    # Verificar se cloudflared ainda esta rodando
    cloudflared_running = False
    if cloudflared_ok:
        try:
            result = subprocess.run(
                ["pgrep", "-f", "cloudflared"],
                capture_output=True,
                timeout=5,
            )
            cloudflared_running = result.returncode == 0
        except Exception:
            pass

    alerts = []
    if not animefix_ok or not uvicorn_running:
        alerts.append("❌ AnimeFix (uvicorn) esta OFFLINE!")
    if not cloudflared_ok or not cloudflared_running:
        alerts.append("❌ Cloudflared esta OFFLINE!")
    elif animefix_ok and cloudflared_ok and uvicorn_running and cloudflared_running:
        # Tudo OK, enviar URL se disponivel
        url = get_cloudflared_url()
        if url:
            context.bot.send_message(
                chat_id=CHAT_ID,
                text=f"✅ Sistema online!\n\n🌐 URL: {url}",
            )
            return

    if alerts:
        alert_text = "⚠️ ALERTA DE SAUDE:\n\n" + "\n".join(alerts)
        context.bot.send_message(chat_id=CHAT_ID, text=alert_text)
        logger.warning(alert_text)


def cmd_start(update: Update, context: CallbackContext) -> None:
    """Comando /start - Lista de comandos."""
    if not is_authorized(update):
        update.message.reply_text("Acesso negado.")
        return

    msg = (
        "🎮 *AnimeFix Control Bot*\n\n"
        "Comandos disponiveis:\n"
        "/status - Verificar saude dos servicos\n"
        "/startapp - Iniciar todos os servicos\n"
        "/stopapp - Parar todos os servicos\n"
        "/restartapp - Reiniciar servicos\n"
        "/geturl - Obter URL efemera do Cloudflare\n"
    )
    update.message.reply_text(msg, parse_mode="Markdown")


def cmd_status(update: Update, context: CallbackContext) -> None:
    """Comando /status - Verifica saude."""
    if not is_authorized(update):
        update.message.reply_text("Acesso negado.")
        return

    animefix_ok = tmux_session_exists("animefix")
    cloudflared_ok = tmux_session_exists("cloudflared")
    port_ok = is_port_in_use(PORT)

    uvicorn_running = False
    if animefix_ok:
        try:
            result = subprocess.run(
                ["pgrep", "-f", "uvicorn"],
                capture_output=True,
                timeout=5,
            )
            uvicorn_running = result.returncode == 0
        except Exception:
            pass

    cloudflared_running = False
    if cloudflared_ok:
        try:
            result = subprocess.run(
                ["pgrep", "-f", "cloudflared"],
                capture_output=True,
                timeout=5,
            )
            cloudflared_running = result.returncode == 0
        except Exception:
            pass

    status_animefix = "✅ Online" if (animefix_ok and uvicorn_running) else "❌ Offline"
    status_cloudflared = "✅ Online" if (cloudflared_ok and cloudflared_running) else "❌ Offline"
    status_port = "✅ Em uso" if port_ok else "❌ Livre"

    msg = (
        f"📊 *Status do Sistema*\n\n"
        f"AnimeFix (uvicorn): {status_animefix}\n"
        f"Cloudflared: {status_cloudflared}\n"
        f"Porta {PORT}: {status_port}\n"
    )

    if animefix_ok and cloudflared_ok and uvicorn_running and cloudflared_running:
        url = get_cloudflared_url()
        if url:
            msg += f"\n🌐 URL: {url}"

    update.message.reply_text(msg, parse_mode="Markdown")


def cmd_startapp(update: Update, context: CallbackContext) -> None:
    """Comando /startapp - Inicia todos os servicos."""
    if not is_authorized(update):
        update.message.reply_text("Acesso negado.")
        return

    update.message.reply_text("🚀 Iniciando servicos...")

    # Iniciar uvicorn
    start_animefix(context)
    time.sleep(2)

    # Iniciar cloudflared
    start_cloudflared(context)
    time.sleep(5)

    # Verificar se tudo subiu
    animefix_ok = tmux_session_exists("animefix")
    cloudflared_ok = tmux_session_exists("cloudflared")
    uvicorn_running = False
    if animefix_ok:
        try:
            result = subprocess.run(
                ["pgrep", "-f", "uvicorn"],
                capture_output=True,
                timeout=5,
            )
            uvicorn_running = result.returncode == 0
        except Exception:
            pass

    cloudflared_running = False
    if cloudflared_ok:
        try:
            result = subprocess.run(
                ["pgrep", "-f", "cloudflared"],
                capture_output=True,
                timeout=5,
            )
            cloudflared_running = result.returncode == 0
        except Exception:
            pass

    if animefix_ok and cloudflared_ok and uvicorn_running and cloudflared_running:
        url = get_cloudflared_url()
        if url:
            update.message.reply_text(
                f"✅ Todos os servicos iniciados!\n\n🌐 URL: {url}"
            )
        else:
            update.message.reply_text(
                "✅ Servicos iniciados! URL do Cloudflare sera disponibilizada em breve."
            )
    else:
        update.message.reply_text(
            "⚠️ Alguns servicos podem nao ter iniciado corretamente. Use /status para verificar."
        )


def cmd_stopapp(update: Update, context: CallbackContext) -> None:
    """Comando /stopapp - Para todos os servicos."""
    if not is_authorized(update):
        update.message.reply_text("Acesso negado.")
        return

    update.message.reply_text("⏹️ Parando servicos...")

    kill_tmux_session("animefix")
    kill_tmux_session("cloudflared")

    update.message.reply_text("✅ Todos os servicos foram parados.")


def cmd_restartapp(update: Update, context: CallbackContext) -> None:
    """Comando /restartapp - Reinicia servicos."""
    if not is_authorized(update):
        update.message.reply_text("Acesso negado.")
        return

    update.message.reply_text("🔄 Reiniciando servicos...")

    # Parar
    kill_tmux_session("animefix")
    kill_tmux_session("cloudflared")
    time.sleep(2)

    # Iniciar
    start_animefix(context)
    time.sleep(2)
    start_cloudflared(context)
    time.sleep(5)

    # Verificar
    animefix_ok = tmux_session_exists("animefix")
    cloudflared_ok = tmux_session_exists("cloudflared")
    uvicorn_running = False
    if animefix_ok:
        try:
            result = subprocess.run(
                ["pgrep", "-f", "uvicorn"],
                capture_output=True,
                timeout=5,
            )
            uvicorn_running = result.returncode == 0
        except Exception:
            pass

    cloudflared_running = False
    if cloudflared_ok:
        try:
            result = subprocess.run(
                ["pgrep", "-f", "cloudflared"],
                capture_output=True,
                timeout=5,
            )
            cloudflared_running = result.returncode == 0
        except Exception:
            pass

    if animefix_ok and cloudflared_ok and uvicorn_running and cloudflared_running:
        url = get_cloudflared_url()
        if url:
            update.message.reply_text(
                f"✅ Servicos reiniciados!\n\n🌐 URL: {url}"
            )
        else:
            update.message.reply_text(
                "✅ Servicos reiniciados! URL do Cloudflare sera disponibilizada em breve."
            )
    else:
        update.message.reply_text(
            "⚠️ Alguns servicos podem nao ter reiniciado corretamente. Use /status."
        )


def cmd_geturl(update: Update, context: CallbackContext) -> None:
    """Comando /geturl - Envia a URL efemera."""
    if not is_authorized(update):
        update.message.reply_text("Acesso negado.")
        return

    url = get_cloudflared_url()
    if url:
        update.message.reply_text(f"🌐 URL efemera:\n{url}")
    else:
        update.message.reply_text(
            "❌ URL nao encontrada. Verifique se o Cloudflared esta rodando com /status"
        )


def handle_unknown(update: Update, context: CallbackContext) -> None:
    """Trata mensagens desconhecidas."""
    if not is_authorized(update):
        return
    update.message.reply_text("Comando nao reconhecido. Use /start para ver os comandos disponiveis.")


def main() -> None:
    """Funcao principal do bot."""
    logger.info("Iniciando AnimeFix Control Bot...")

    # Criar updater
    updater = Updater(token=BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Registrar comandos
    dispatcher.add_handler(CommandHandler("start", cmd_start))
    dispatcher.add_handler(CommandHandler("status", cmd_status))
    dispatcher.add_handler(CommandHandler("startapp", cmd_startapp))
    dispatcher.add_handler(CommandHandler("stopapp", cmd_stopapp))
    dispatcher.add_handler(CommandHandler("restartapp", cmd_restartapp))
    dispatcher.add_handler(CommandHandler("geturl", cmd_geturl))

    # Mensagens desconhecidas
    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, handle_unknown)
    )

    # Iniciar monitoramento periodico
    job_queue = updater.job_queue
    if job_queue:
        job_queue.run_repeating(
            monitor_services,
            interval=CHECK_INTERVAL,
            first=10,
            name="health_check",
        )
        logger.info(f"Monitoramento configurado: a cada {CHECK_INTERVAL}s")

    # Iniciar bot
    updater.start_polling()
    logger.info("Bot rodando! Envie /start no Telegram.")

    # Enviar mensagem de inicializacao
    try:
        updater.bot.send_message(
            chat_id=CHAT_ID,
            text=(
                "🎮 *AnimeFix Control Bot Iniciado!*\n\n"
                "Envie /start para ver os comandos disponiveis."
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem de inicio: {e}")

    # Manter rodando
    updater.idle()
    logger.info("Bot encerrado.")


if __name__ == "__main__":
    main()
