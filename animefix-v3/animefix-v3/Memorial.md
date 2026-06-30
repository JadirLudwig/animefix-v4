# Memorial do Projeto AnimeFix v2

**Data de Início/Última Atualização:** 2026-04-25
**Objetivo do Projeto:** Sistema de IPTV de animes que realiza web scraping de sites como `animesonlinecc.to` (Dooplay) e `meusanimes.blog` para extrair links de streaming (.mp4, .m3u8, iframe) e mantê-los sincronizados e atualizados em um banco de dados local SQLite.

## Componentes Principais
- **FastAPI / SQLAlchemy:** Backend API para expor os animes e episódios.
- **worker.py:** Tarefas assíncronas (background jobs) para sincronizar episódios pendentes e validar links expirados usando APScheduler e loops assíncronos.
- **scraper.py:** Scraper original para sites baseados no tema Dooplay (`animesonlinecc.to`).
- **scraper_meusanimes.py:** Scraper integrado recentemente para o site `meusanimes.blog`.

## Histórico de Problemas e Soluções
- **Problema de Performance (Resolvido):** Ocorria uso excessivo de CPU e lentidão extrema porque o `worker.py` tentava resolver continuamente episódios falhos em um loop infinito sem limites de tentativas. Além disso, estava usando o scraper incorreto (`dooplay`) para os links de `meusanimes.blog`. **Solução:** Adicionada a coluna `retry_count` para limitar as falhas em até 3 tentativas, remoção dos itens "Failed" do loop agressivo, e condicionamento dinâmico do uso do scraper (`dooplay` vs `meusanimes`).
- **Problema de Reprodução Meus Animes (Resolvido):** Episódios do `meusanimes.blog` não reproduziam no player nativo, sendo baixados pelo navegador ou ficando com tela preta. O site usa uma arquitetura complexa de iframes aninhados e uma aplicação React para esconder os vídeos. **Solução:** Implementada extração profunda ("Deep Scrape") no `scraper_meusanimes.py` que realiza engenharia reversa na API deles (`get-video.php`), atravessa camadas de redirecionamento e extrai o link direto `.mp4` (Rumble/CDN) ou o embed do Blogger (classificado como `youtube` para compatibilidade). O backend foi ajustado para redirecionar iframes corretamente em vez de tentar realizar proxy de HTML.

## Cancelamento de Funcionalidades
- **Configuração de Rede (Cloudflare/Duck DNS):** A tentativa de configurar um endereço fixo via Cloudflare Tunnel e Duck DNS foi descontinuada e todos os arquivos relacionados (`update_duckdns.sh` e `cloudflared`) foram removidos do projeto a pedido do usuário.
- **Migração para v3 (Concluída):** O projeto foi migrado para um novo repositório GitHub (`animefix-v3`), consolidando todas as melhorias de scraping e removendo dependências externas desnecessárias.
