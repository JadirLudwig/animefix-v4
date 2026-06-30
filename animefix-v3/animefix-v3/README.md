# AnimeFix - Sistema de IPTV de Anime

Um sistema completo para streaming de animes com suporte a múltiplas fontes e integração automática de conteúdo.

## 🎯 Funcionalidades

- **Multi-fonte**: Suporte a diferentes sites de anime (DooPlay, Meus Animes Blog)
- **Sincronização Automática**: Extração automática de episódios e links de streaming
- **Streaming Proxy**: Proxy para vídeos diretos (.mp4, .m3u8) e integração com YouTube
- **Sistema de Background**: Agendador de tarefas para verificação e atualização
- **PWA Support**: Aplicativo web progressivo para melhor experiência mobile
- **API REST**: Interface completa para gerenciamento de conteúdo

## 🏗️ Arquitetura

```
├── app/
│   ├── main.py          # FastAPI application
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── database.py      # Database configuration
│   ├── scraper.py       # Scraper para DooPlay
│   ├── scraper_meusanimes.py  # Scraper para Meus Animes Blog
│   ├── worker.py        # Background tasks
│   ├── validator.py     # Link validation
│   └── static/          # Frontend estático
├── requirements.txt     # Python dependencies
├── migrate_db.py       # Database migration
└── test_*.py          # Test scripts
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.8+
- SQLite (ou PostgreSQL/MySQL opcional)
- Acesso à internet para scraping

### Setup

1. Clone o repositório:
```bash
git clone <repository-url>
cd animefix-v2
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute a migração do banco de dados:
```bash
python migrate_db.py
```

4. Inicie o servidor:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Acesso

- Web interface: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Admin panel: `http://localhost:8000/admin`

## 📖 Integração com Meus Animes Blog

O sistema agora suporta integração total com o site **Meus Animes Blog**. Veja [MEUSANIMES_INTEGRATION.md](./MEUSANIMES_INTEGRATION.md) para detalhes completos.

### Formas de Adicionar Animes

#### Via API
```bash
# Endpoint dedicado
curl -X POST "http://localhost:8000/api/animes/meusanimes" \
  -H "Content-Type: application/json" \
  -d '{"anime_url": "https://meusanimes.blog/a/avatar-aang-the-last-airbender-2026/"}'

# Endpoint genérico (detecção automática)
curl -X POST "http://localhost:8000/api/animes" \
  -H "Content-Type: application/json" \
  -d '{"base_url": "https://meusanimes.blog/a/avatar-aang-the-last-airbender-2026/"}'
```

#### Via Script
```bash
python add_meusanimes_animes.py
```

## 🔧 Endpoints Principais

### Animes
- `POST /api/animes` - Adicionar novo anime
- `GET /api/animes` - Listar todos animes
- `POST /api/animes/{anime_id}/sync` - Sincronizar anime
- `DELETE /api/animes/{anime_id}` - Deletar anime

### Episódios
- `GET /api/episodes/recent` - Episódios recentes

### Streaming
- `GET /stream/{episode_id}` - Stream de episódio

## 🧪 Testes

### Testar Scraper
```bash
# Testar scraper DooPlay original
python test_scraper.py

# Testar scraper Meus Animes Blog
python test_meusanimes_scraper.py

# Testes de diagnóstico
python test_diagnostic.py
```

### Testar Integração
```bash
# Adicionar animes de exemplo
python add_meusanimes_animes.py
```

## 📊 Estrutura de Dados

### Anime
```sql
CREATE TABLE animes (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  base_url TEXT UNIQUE NOT NULL,
  source_type TEXT DEFAULT 'dooplay',
  last_sync_date DATETIME,
  poster_url TEXT,
  mal_url TEXT,
  description TEXT
);
```

### Episódio
```sql
CREATE TABLE episodes (
  id INTEGER PRIMARY KEY,
  anime_id INTEGER NOT NULL,
  number TEXT NOT NULL,
  season INTEGER DEFAULT 1,
  title TEXT,
  thumb_url TEXT,
  description TEXT,
  page_url TEXT UNIQUE NOT NULL,
  stream_url TEXT,
  media_type TEXT,
  status TEXT DEFAULT 'Pending',
  last_checked DATETIME
);
```

## ⚙️ Configuração

### Variáveis de Ambiente
```bash
# Porta do servidor
PORT=8000

# Database URL (SQLite padrão)
DATABASE_URL=sqlite:///./animefix.db

# Sincronização automática (em minutos)
SYNC_INTERVAL=45

# Verificação de links (em minutos)
CHECK_INTERVAL=5
```

### User Agents
O sistema usa rotativa de user agents para evitar bloqueio:
- Chrome, Firefox, Safari rotativos
- Delay aleatório entre requests
- Headers padrão de navegadores

## 🔒 Segurança

- Rate limiting implícito com delays
- Validação de URLs antes de scraping
- Tratamento de erros robusto
- Sanitização de inputs

## 🚧 Desenvolvimento

### Adicionar Nova Fonte

1. Criar novo scraper em `app/scraper_<nome>.py`
2. Atualizar `app/worker.py` para suportar nova fonte
3. Adicionar tipo de fonte em `app/models.py`
4. Criar endpoint dedicado (opcional)

### Estrutura de Scraper

```python
async def scrape_<nome>_episodes(anime_url):
    # Implementação de extração de animes
    pass

async def scrape_<nome>_episode_video(episode_url):
    # Implementação de extração de vídeos
    pass
```

## 📱 Mobile

O sistema é otimizado para mobile com:
- PWA support
- Interface responsiva
- Streaming adaptativo
- Cache offline

## 🤝 Contribuição

1. Fork o projeto
2. Crie feature branch
3. Faça commit das mudanças
4. Abra pull request

## 📄 Licença

MIT License - veja arquivo LICENSE para detalhes

## 🆘 Suporte

Para suporte e dúvidas:
- Verifique a documentação
- Execute testes de diagnóstico
- Check logs em `/tmp/animefix.log`

---

**AnimeFix** - Transformando a forma de assistir animes online 🎬✨