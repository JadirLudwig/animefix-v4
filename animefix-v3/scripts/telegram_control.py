#!/usr/bin/env python3
"""
AnimeFix Telegram Control Bot (sem dependencias externas)
Usa HTTP direto para a API do Telegram.
"""

import os
import re
import sys
import json
import time
import subprocess
import logging
import urllib.request
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
ENV_PATH = SCRIPT_DIR / ".env"
load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = int(os.getenv("CHAT_ID", "0"))
PORT = int(os.getenv("PORT", "8000"))
UVICORN_CMD = os.getenv("UVICORN_CMD", "uvicorn app.main:app --host 0.0.0.0 --port 8000")
CLOUDFLARED_CMD = os.getenv("CLOUDFLARED_CMD", "cloudflared tunnel --url http://localhost:8000")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))

if not BOT_TOKEN:
    logger.error("BOT_TOKEN nao encontrado no .env")
    sys.exit(1)
if CHAT_ID == 0:
    logger.error("CHAT_ID nao encontrado no .env")
    sys.exit(1)

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

offset = 0


def api_call(method, data=None):
    url = f"{API_URL}/{method}"
    if data:
        encoded = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(url, data=encoded)
    else:
        req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.error(f"API call failed: {method} - {e}")
        return None


def send_message(text, parse_mode="Markdown"):
    return api_call("sendMessage", {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
    })


def tmux_exists(session):
    try:
        r = subprocess.run(
            ["tmux", "has-session", "-t", session],
            capture_output=True, timeout=5,
        )
        return r.returncode == 0
    except Exception:
        return False


def tmux_kill(session):
    try:
        subprocess.run(
            ["tmux", "kill-session", "-t", session],
            capture_output=True, timeout=5,
        )
    except Exception:
        pass


def tmux_create_and_send(session, cmd):
    try:
        subprocess.run(
            ["tmux", "new-session", "-d", "-s", session],
            capture_output=True, timeout=5,
        )
        subprocess.run(
            ["tmux", "send-keys", "-t", session, cmd, "Enter"],
            capture_output=True, timeout=5,
        )
    except Exception as e:
        logger.error(f"Erro ao criar sessao {session}: {e}")


def is_process_running(name):
    try:
        r = subprocess.run(
            ["pgrep", "-f", name],
            capture_output=True, timeout=5,
        )
        return r.returncode == 0
    except Exception:
        return False


def get_cloudflared_url():
    try:
        r = subprocess.run(
            ["tmux", "capture-pane", "-t", "cloudflared", "-p"],
            capture_output=True, text=True, timeout=10,
        )
        urls = re.findall(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com[^\s]*", r.stdout)
        if urls:
            return urls[-1]
        urls = re.findall(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", r.stdout)
        if urls:
            return urls[-1]
        return ""
    except Exception:
        return ""


def start_animefix():
    if tmux_exists("animefix"):
        return
    project_dir = SCRIPT_DIR.parent
    tmux_create_and_send("animefix", f"cd {project_dir} && {UVICORN_CMD}")
    logger.info("AnimeFix iniciado")


def start_cloudflared():
    if tmux_exists("cloudflared"):
        return
    tmux_create_and_send("cloudflared", CLOUDFLARED_CMD)
    logger.info("Cloudflared iniciado")


def get_status():
    af = tmux_exists("animefix") and is_process_running("uvicorn")
    cf = tmux_exists("cloudflared") and is_process_running("cloudflared")
    return af, cf


def handle_start():
    send_message(
        "🎮 *AnimeFix Control Bot*\n\n"
        "Comandos:\n"
        "/status - Verificar saude\n"
        "/startapp - Iniciar servicos\n"
        "/stopapp - Parar servicos\n"
        "/restartapp - Reiniciar\n"
        "/geturl - URL do Cloudflare"
    )


def handle_status():
    af, cf = get_status()
    url = get_cloudflared_url() if (af and cf) else ""
    msg = (
        f"📊 *Status*\n\n"
        f"AnimeFix: {'✅ Online' if af else '❌ Offline'}\n"
        f"Cloudflared: {'✅ Online' if cf else '❌ Offline'}"
    )
    if url:
        msg += f"\n\n🌐 URL: {url}"
    send_message(msg)


def handle_startapp():
    send_message("🚀 Iniciando servicos...")
    start_animefix()
    time.sleep(2)
    start_cloudflared()
    time.sleep(8)
    af, cf = get_status()
    if af and cf:
        url = get_cloudflared_url()
        if url:
            send_message(f"✅ Servicos iniciados!\n\n🌐 URL: {url}")
        else:
            send_message("✅ Servicos iniciados! URL sera disponibilizada em breve.")
    else:
        send_message("⚠️ Alguns servicos podem nao ter iniciado. Use /status")


def handle_stopapp():
    send_message("⏹️ Parando servicos...")
    tmux_kill("animefix")
    tmux_kill("cloudflared")
    send_message("✅ Servicos parados.")


def handle_restartapp():
    send_message("🔄 Reiniciando...")
    tmux_kill("animefix")
    tmux_kill("cloudflared")
    time.sleep(2)
    start_animefix()
    time.sleep(2)
    start_cloudflared()
    time.sleep(8)
    af, cf = get_status()
    if af and cf:
        url = get_cloudflared_url()
        if url:
            send_message(f"✅ Reiniciado!\n\n🌐 URL: {url}")
        else:
            send_message("✅ Reiniciado! URL sera disponibilizada em breve.")
    else:
        send_message("⚠️ Problemas ao reiniciar. Use /status")


def handle_geturl():
    url = get_cloudflared_url()
    if url:
        send_message(f"🌐 URL:\n{url}")
    else:
        send_message("❌ URL nao encontrada. Verifique com /status")


def main():
    global offset
    logger.info("Iniciando AnimeFix Control Bot...")

    resp = api_call("getMe")
    if not resp or not resp.get("ok"):
        logger.error("Falha ao conectar com a API do Telegram. Verifique o BOT_TOKEN.")
        sys.exit(1)
    bot_name = resp["result"].get("username", "desconhecido")
    logger.info(f"Bot conectado: @{bot_name}")

    try:
        send_message(
            "🎮 *AnimeFix Control Bot Iniciado!*\n\n"
            "Envie /start para ver os comandos."
        )
    except Exception as e:
        logger.error(f"Erro ao enviar msg inicial: {e}")

    logger.info(f"Monitoramento a cada {CHECK_INTERVAL}s. Polling mensagens...")

    last_check = time.time()

    while True:
        try:
            resp = api_call("getUpdates", {
                "offset": offset,
                "timeout": 30,
            })

            if resp and resp.get("ok") and resp.get("result"):
                for update in resp["result"]:
                    offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    chat_id = msg.get("chat", {}).get("id", 0)
                    text = msg.get("text", "")

                    if chat_id != CHAT_ID:
                        continue

                    logger.info(f"Comando recebido: {text}")

                    if text == "/start":
                        handle_start()
                    elif text == "/status":
                        handle_status()
                    elif text == "/startapp":
                        handle_startapp()
                    elif text == "/stopapp":
                        handle_stopapp()
                    elif text == "/restartapp":
                        handle_restartapp()
                    elif text == "/geturl":
                        handle_geturl()

            now = time.time()
            if now - last_check >= CHECK_INTERVAL:
                last_check = now
                af, cf = get_status()
                if not af or not cf:
                    alerts = []
                    if not af:
                        alerts.append("❌ AnimeFix (uvicorn) OFFLINE!")
                    if not cf:
                        alerts.append("❌ Cloudflared OFFLINE!")
                    send_message("⚠️ ALERTA:\n\n" + "\n".join(alerts))

        except KeyboardInterrupt:
            logger.info("Bot encerrado pelo usuario.")
            break
        except Exception as e:
            logger.error(f"Erro no loop: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
