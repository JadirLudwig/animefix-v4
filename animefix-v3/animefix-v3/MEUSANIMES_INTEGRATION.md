# Integração com Meus Animes Blog

Este projeto agora suporta a integração com o site **Meus Animes Blog** (meusanimes.blog), permitindo adicionar conteúdo de anime diretamente do seu site ao seu AnimeFix.

## Funcionalidades Adicionadas

### 1. Novo Scraper Específico
- `app/scraper_meusanimes.py`: Scraper dedicado para o formato do site meusanimes.blog
- Suporte a estrutura de temporadas e episódios
- Extração de URLs de streaming (iframe, direto, etc.)

### 2. Suporte a Múltiplos Fontes
- Sistema de detecção automática do tipo de fonte (dooplay vs meusanimes)
- Banco de dados atualizado para armazenar o tipo de fonte
- Sincronização adaptativa baseada no tipo de fonte

### 3. Novos Endpoints API
- `/api/animes/meusanimes`: Endpoint dedicado para adicionar animes do meusanimes.blog
- Suporte a validação de URL automática

## Como Usar

### Adicionando Animes Manualmente

#### Método 1: Usando o endpoint dedicado
```bash
curl -X POST "http://localhost:8000/api/animes/meusanimes" \
  -H "Content-Type: application/json" \
  -d '{"anime_url": "https://meusanimes.blog/a/avatar-aang-the-last-airbender-2026/"}'
```

#### Método 2: Usando o endpoint genérico (detecção automática)
```bash
curl -X POST "http://localhost:8000/api/animes" \
  -H "Content-Type: application/json" \
  -d '{"base_url": "https://meusanimes.blog/a/avatar-aang-the-last-airbender-2026/"}'
```

#### Método 3: Via script Python
```bash
python add_meusanimes_animes.py
```

### Estrutura de URLs Suportadas

- **Páginas de Animes**: `https://meusanimes.blog/a/nome-do-anime/`
- **Páginas de Episódios**: `https://meusanimes.blog/e/nome-do-anime-episodio-numero/`

### Formato de Dados Extraídos

#### Anime
```json
{
  "id": 1,
  "name": "Avatar: Aang The Last Airbender (2026)",
  "base_url": "https://meusanimes.blog/a/avatar-aang-the-last-airbender-2026/",
  "source_type": "meusanimes",
  "poster_url": "https://meusanimes.blog/wp-content/uploads/2026/04/poster.jpg",
  "description": "Descrição do anime...",
  "last_sync_date": "2026-04-23T14:30:00Z"
}
```

#### Episódio
```json
{
  "id": 1,
  "anime_id": 1,
  "number": "1",
  "season": 1,
  "title": "Episódio 1",
  "page_url": "https://meusanimes.blog/e/avatar-aang-the-last-airbender-2026-episodio-1/",
  "stream_url": "https://serv01.meusdoramas.club/#/video/1669809/1/1/",
  "media_type": "iframe",
  "status": "Online",
  "thumb_url": "https://meusanimes.blog/wp-content/uploads/2026/04/episodio1.jpg"
}
```

## Detecção Automática

O sistema agora detecta automaticamente o tipo de fonte baseado na URL:
- URLs contendo `meusanimes.blog` → `source_type: "meusanimes"`
- Outras URLs → `source_type: "dooplay"` (padrão original)

## Streaming

O sistema suporta diferentes tipos de streaming:
- **Iframes**: URLs externas embutidas
- **Direto**: Links .mp4, .m3u8
- **YouTube**: Integração com vídeos do YouTube

## Sincronização Background

A sincronização é executada automaticamente:
- A cada 45 minutos: verificação de novos episódios e links expirados
- A cada 5 minutos: resolução de links quebrados
- Sincronização adaptativa baseada no tipo de fonte

## Testes

### Testando o Scraper
```bash
python test_meusanimes_scraper.py
```

### Testando a Integração
```bash
python add_meusanimes_animes.py
```

## Considerações

1. **Rate Limiting**: O scraper inclui delays para não sobrecarregar o servidor
2. **User Agents**: Rotativa de user agents para evitar bloqueio
3. **Tratamento de Erros**: Robustez contra mudanças na estrutura do site
4. **Cache**: URLs são validadas antes de serem armazenadas

## Próximos Passos

1. Adicionar suporte a mais fontes de anime
2. Implementar sistema de fila para sincronização massiva
3. Adicionar interface web para administração
4. Implementar sistema de recomendações

## Licença

Integração desenvolvida para o projeto AnimeFix - Sistema de IPTV de Anime.