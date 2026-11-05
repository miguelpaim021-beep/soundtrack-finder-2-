"""
SoundTrack Finder — lógica da aplicação
=======================================
Python rodando dentro do navegador (PyScript).
"""

import asyncio
import json
import random
from html import escape
from urllib.parse import urlencode

from pyscript import document, window
from pyodide.http import pyfetch
from pyodide.ffi import create_proxy


# =============================================================================
# 1. ELEMENTOS DA PÁGINA
# =============================================================================
API_URL = "https://itunes.apple.com/search"
LIMITE = 12

form_busca = document.querySelector("#search-form")
campo_busca = document.querySelector("#search-input")
botao_tema = document.querySelector("#theme-btn")
botao_menu = document.querySelector("#menu-btn")
menu_popup = document.querySelector("#menu-popup")
menu_qtd_albuns = document.querySelector("#menu-qtd-albuns")
menu_qtd_favoritos = document.querySelector("#menu-qtd-favoritos")
menu_qtd_downloads = document.querySelector("#menu-qtd-downloads")

TELAS = {
    "busca": document.querySelector("#tela-busca"),
    "favoritos": document.querySelector("#tela-favoritos"),
    "downloads": document.querySelector("#tela-downloads"),
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


# =============================================================================
# 2. ARMAZENAMENTO (localStorage)
# =============================================================================
def carregar(chave, padrao):
    try:
        texto = window.localStorage.getItem(chave)
        return json.loads(texto) if texto else padrao
    except Exception:
        return padrao


def guardar(chave, valor):
    try:
        window.localStorage.setItem(chave, json.dumps(valor))
    except Exception:
        pass


# =============================================================================
# 3. ESTADO DA APLICAÇÃO
# =============================================================================
favoritos = carregar("favoritos", {})
downloads = carregar("downloads", {})
albuns = carregar("albuns", {})
resultados_atuais = {}

tela = "busca"
album_aberto = None
timer_aviso = None


# =============================================================================
# 4. API DO iTUNES
# =============================================================================
async def buscar_musicas(termo):
    params = urlencode({"term": termo, "entity": "song", "limit": LIMITE})
    resposta = await pyfetch(f"{API_URL}?{params}")
    if not resposta.ok:
        raise RuntimeError(f"Erro HTTP {resposta.status}")
    dados = await resposta.json()
    return dados["results"]


def simplificar(m):
    capa = m.get("artworkUrl100", "").replace("100x100", "300x300")
    preview = m.get("previewUrl", "")
    return {
        "id": str(m.get("trackId", preview)),
        "nome": m.get("trackName", "Sem título"),
        "artista": m.get("artistName", "Artista desconhecido"),
        "capa": capa,
        "audio": preview,
        "audio_completo": preview,
    }


# =============================================================================
# 5. MONTAGEM DO HTML
# =============================================================================
def plural(n, singular, plural_):
    return f"{n} {singular if n == 1 else plural_}"


def html_card(m):
    id_ = escape(m["id"])
    nome = escape(m["nome"])
    artista = escape(m["artista"])
    capa = escape(m["capa"])
    audio = escape(m["audio"])

    salva = id_ in favoritos
    classe_fav = "btn-salvar ativo" if salva else "btn-salvar"
    texto_fav = "✓ Salva nos Favoritos" if salva else "⭐ Salvar nos Favoritos"

    baixada = id_ in downloads
    classe_down = "btn-salvar ativo" if baixada else "btn-salvar"
    texto_down = "✓ Baixado" if baixada else "⬇ Baixar"

    return f"""
    <article class="card">
      <div class="capa"><img src="{capa}" alt="Capa" loading="lazy"></div>
      <h3 title="{nome}">{nome}</h3>
      <p>{artista}</p>
      <audio controls preload="none" src="{audio}"></audio>
      <button class="{classe_fav}" data-acao="favoritar" data-id="{id_}" data-nome="{nome}" data-artista="{artista}" data-capa="{capa}" data-audio="{audio}">{texto_fav}</button>
      <button class="{classe_down}" data-acao="baixar-musica" data-id="{id_}" data-nome="{nome}" data-artista="{artista}" data-capa="{capa}" data-audio="{audio}">{texto_down}</button>
    </article>"""


def html_linha_favorito(m):
    id_ = escape(m["id"])
    if albuns:
        opcoes = "".join(
            f'<option value="{escape(nome)}">{escape(nome)}</option>' for nome in albuns
        )
        extra = (
            f'<select data-acao="add-album" data-id="{id_}" title="Adicionar a um álbum">'
            f'<option value="">＋ Álbum</option>{opcoes}</select>'
        )
    else:
        extra = '<button class="link" data-acao="ir-albuns">Criar álbum</button>'

    baixada = id_ in downloads
    texto_baixar = "⬇ Baixado" if baixada else "⬇ Baixar"
    classe_baixar = "icone pequeno ativo" if baixada else "icone pequeno"
    btn_
