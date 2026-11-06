"""
SoundTrack Finder — lógica da aplicação
"""

import asyncio
import json
import random
from html import escape
from urllib.parse import urlencode

from pyscript import document, window
from pyodide.http import pyfetch
from pyodide.ffi import create_proxy

API_URL = "https://itunes.apple.com/search"
LIMITE = 12

# Dicionário de Traduções (PT, EN, ES)
TRADUCOES = {
    "pt": {
        "menu_albuns": "Álbuns",
        "menu_albuns_sub": "Suas playlists",
        "menu_favoritos": "Favoritos",
        "menu_favoritos_sub": "Músicas favoritas",
        "menu_downloads": "Downloads",
        "menu_downloads_sub": "Músicas baixadas",
        "menu_local": "Dispositivo",
        "menu_local_sub": "Músicas locais",
        "busca_placeholder": "Busque um artista ou música…",
        "album_placeholder": "Nome do novo álbum…",
        "btn_pesquisar": "Buscar",
        "btn_criar_album": "＋ Criar álbum",
        "status_inicio": "Digite algo para começar.",
        "player_nada": "Nada tocando",
        "player_sub": "Escolha uma música para ouvir",
        "salvar_fav": "⭐ Salvar nos Favoritos",
        "salvo_fav": "✓ Salva nos Favoritos",
        "baixar": "⬇ Baixar",
        "baixado": "✓ Baixado",
        "msg_salvo": "Salva nos Favoritos",
        "msg_remover_fav": "Removida dos favoritos",
        "msg_baixado": "Música baixada com sucesso!",
        "msg_down_rem": "Download removido",
        "msg_album_criado": "Álbum criado",
        "msg_ja_existe": "Já existe um álbum com esse nome",
        "msg_excluir_album": "Álbum excluído",
        "abrir_pasta": "📂 Abrir Pasta",
        "nenhuma_pasta": "Nenhuma pasta aberta",
        "nenhuma_pasta_desc": "Clique no botão acima para selecionar uma pasta do seu dispositivo com músicas.",
        "nenhum_fav_titulo": "Nenhum favorito ainda",
        "nenhum_fav_desc": "Busque uma música e toque em “Salvar nos Favoritos”.",
        "nenhum_down_titulo": "Nenhum download realizado",
        "nenhum_down_desc": "Vá em Favoritos ou na Busca e clique em “Baixar” nas músicas desejadas.",
    },
    "en": {
        "menu_albuns": "Albums",
        "menu_albuns_sub": "Your playlists",
        "menu_favoritos": "Favorites",
        "menu_favoritos_sub": "Favorite songs",
        "menu_downloads": "Downloads",
        "menu_downloads_sub": "Downloaded songs",
        "menu_local": "Device",
        "menu_local_sub": "Local songs",
        "busca_placeholder": "Search for an artist or song…",
        "album_placeholder": "New album name…",
        "btn_pesquisar": "Search",
        "btn_criar_album": "＋ Create album",
        "status_inicio": "Type something to start.",
        "player_nada": "Nothing playing",
        "player_sub": "Choose a song to listen to",
        "salvar_fav": "⭐ Save to Favorites",
        "salvo_fav": "✓ Saved to Favorites",
        "baixar": "⬇ Download",
        "baixado": "✓ Downloaded",
        "msg_salvo": "Saved to Favorites",
        "msg_remover_fav": "Removed from favorites",
        "msg_baixado": "Song downloaded successfully!",
        "msg_down_rem": "Download removed",
        "msg_album_criado": "Album created",
        "msg_ja_existe": "An album with this name already exists",
        "msg_excluir_album": "Album deleted",
        "abrir_pasta": "📂 Open Folder",
        "nenhuma_pasta": "No folder opened",
        "nenhuma_pasta_desc": "Click the button above to select a folder with songs from your device.",
        "nenhum_fav_titulo": "No favorites yet",
        "nenhum_fav_desc": "Search for a song and tap “Save to Favorites”.",
        "nenhum_down_titulo": "No downloads yet",
        "nenhum_down_desc": "Go to Favorites or Search and click “Download” on desired songs.",
    },
    "es": {
        "menu_albuns": "Álbumes",
        "menu_albuns_sub": "Tus listas",
        "menu_favoritos": "Favoritos",
        "menu_favoritos_sub": "Canciones favoritas",
        "menu_downloads": "Descargas",
        "menu_downloads_sub": "Canciones descargadas",
        "menu_local": "Dispositivo",
        "menu_local_sub": "Canciones locales",
        "busca_placeholder": "Busca un artista o canción…",
        "album_placeholder": "Nombre del nuevo álbum…",
        "btn_pesquisar": "Buscar",
        "btn_criar_album": "＋ Crear álbum",
        "status_inicio": "Escribe algo para empezar.",
        "player_nada": "Nada sonando",
        "player_sub": "Elige una canción para escuchar",
        "salvar_fav": "⭐ Guardar en Favoritos",
        "salvo_fav": "✓ Guardado en Favoritos",
        "baixar": "⬇ Descargar",
        "baixado": "✓ Descargado",
        "msg_salvo": "Guardado en Favoritos",
        "msg_remover_fav": "Eliminado de favoritos",
        "msg_baixado": "¡Canción descargada com éxito!",
        "msg_down_rem": "Descarga eliminada",
        "msg_album_criado": "Álbum creado",
        "msg_ja_existe": "Ya existe un álbum con este nombre",
        "msg_excluir_album": "Álbum eliminado",
        "abrir_pasta": "📂 Abrir Carpeta",
        "nenhuma_pasta": "Ninguna carpeta abierta",
        "nenhuma_pasta_desc": "Haz clic arriba para seleccionar una carpeta de tu dispositivo con música.",
        "nenhum_fav_titulo": "No hay favoritos todavía",
        "nenhum_fav_desc": "Busca una canción y toca “Guardar en Favoritos”.",
        "nenhum_down_titulo": "No hay descargas",
        "nenhum_down_desc": "Ve a Favoritos o Buscar y haz clic en “Descargar” en las canciones.",
    }
}

form_busca = document.querySelector("#search-form")
campo_busca = document.querySelector("#search-input")
botao_tema = document.querySelector("#theme-btn")
botao_menu = document.querySelector("#menu-btn")
menu_popup = document.querySelector("#menu-popup")
menu_qtd_albuns = document.querySelector("#menu-qtd-albuns")
menu_qtd_favoritos = document.querySelector("#menu-qtd-favoritos")
menu_qtd_downloads = document.querySelector("#menu-qtd-downloads")
menu_qtd_local = document.querySelector("#menu-qtd-local")
select_idioma = document.querySelector("#lang-select")

TELAS = {
    "busca": document.querySelector("#tela-busca"),
    "favoritos": document.querySelector("#tela-favoritos"),
    "downloads": document.querySelector("#tela-downloads"),
    "local": document.querySelector("#tela-local"),
    "albuns": document.querySelector("#tela-albuns"),
    "album": document.querySelector("#tela-album"),
}
area_rolagem = document.querySelector("#scroll")

status = document.querySelector("#status")
grade = document.querySelector("#grid")

form_album = document.querySelector("#album-form")
campo_album = document.querySelector("#album-input")
grade_albuns = document.querySelector("#albuns-grid")
albuns_sub = document.querySelector("#albuns-sub")

player = document.querySelector("#player")
np_capa = document.querySelector("#np-capa")
np_nome = document.querySelector("#np-nome")
np_artista = document.querySelector("#np-artista")
toast = document.querySelector("#toast")

def carregar(chave, padrao):
    try:
        texto = window.localStorage.getItem(chave)
        return json.loads(texto) if texto else padrao
    except Exception:
        return padrao

def guardar(chave,
