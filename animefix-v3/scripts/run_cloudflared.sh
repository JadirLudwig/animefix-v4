#!/bin/bash
# AnimeFix - Iniciar cloudflared
exec cloudflared tunnel --url http://localhost:8000
