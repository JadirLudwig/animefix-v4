"""
Script para adicionar animes do meusanimes.blog ao banco de dados
"""
import asyncio
import sys
import os

# Adicionar o diretório app ao Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal, engine
from app.models import Anime, Base
from app.worker import sync_anime_updates

# Criar tabelas se não existirem
Base.metadata.create_all(bind=engine)

async def add_meusanimes_animes():
    """
    Adiciona alguns animes populares do meusanimes.blog ao banco de dados
    """
    db = SessionLocal()
    
    # Lista de animes populares do meusanimes.blog
    anime_urls = [
        "https://meusanimes.blog/a/avatar-aang-the-last-airbender-2026/",
        "https://meusanimes.blog/a/haibara-kun-no-tsuyokute-seishun-new-game/",
        "https://meusanimes.blog/a/one-piece/",
        "https://meusanimes.blog/a/shingeki-no-kyojin/",
        "https://meusanimes.blog/a/solo-leveling/"
    ]
    
    try:
        for url in anime_urls:
            # Verificar se anime já existe
            existing_anime = db.query(Anime).filter(Anime.base_url == url).first()
            if existing_anime:
                print(f"Anime já existe: {existing_anime.name}")
                continue
            
            # Criar novo anime
            new_anime = Anime(
                name="Pending Anime...",
                base_url=url,
                source_type="meusanimes"
            )
            db.add(new_anime)
            db.commit()
            db.refresh(new_anime)
            
            print(f"Adicionado anime: {new_anime.name} (ID: {new_anime.id})")
            
            # Iniciar sincronização em background
            asyncio.create_task(sync_anime_updates(new_anime.id))
            
        print(f"\n{len(anime_urls)} animes adicionados com sucesso!")
        print("A sincronização de episódios começará em background...")
        
    except Exception as e:
        print(f"Erro: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(add_meusanimes_animes())