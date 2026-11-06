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

form_busca = document.querySelector("#search-form")
campo_busca = document.querySelector("#search-input")
botao_tema = document.querySelector("#theme-btn")
botao_menu = document.querySelector("#menu-btn")
menu_popup = document.querySelector("#menu-popup")
menu_qtd_albuns = document.querySelector("#menu-qtd-albuns")
menu_qtd_favoritos = document.querySelector("#menu-qtd-favoritos")
menu_qtd_downloads = document.querySelector("#menu-qtd-downloads")
menu_qtd_local = document.querySelector("#menu-qtd-local")

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
lang_btn = document.querySelector("#lang-btn")
lang_popup = document.querySelector("#lang-popup")
lang_atual = document.querySelector("#lang-atual")

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
# IDIOMAS (Português / English / Español)
# =============================================================================
# Todo texto visível fica neste dicionário. Para traduzir algo novo, adicione a
# mesma chave nos 3 idiomas e use t("chave") no código (ou data-i18n="chave" no HTML).
TRADUCOES = {
    "pt": {
        "menu_aria": "Abrir menu",
        "menu_albuns": "Álbuns", "menu_albuns_sub": "Suas playlists",
        "menu_favoritos": "Favoritos", "menu_favoritos_sub": "Músicas favoritas",
        "menu_downloads": "Downloads", "menu_downloads_sub": "Músicas baixadas",
        "menu_local": "Dispositivo", "menu_local_sub": "Músicas locais",
        "buscar_placeholder": "Busque um artista ou música…", "buscar_btn": "Buscar",
        "tema_titulo": "Alternar tema", "idioma_titulo": "Idioma",
        "album_novo_placeholder": "Nome do novo álbum…", "criar_album_btn": "＋ Criar álbum",
        "np_nome_vazio": "Nada tocando", "np_artista_vazio": "Escolha uma música para ouvir",
        "status_inicial": "Digite algo para começar.",
        "status_digite": "Digite o nome de um artista ou música.",
        "status_buscando": "Buscando músicas…",
        "status_erro": "Erro ao buscar. Verifique sua internet e tente de novo.",
        "status_vazio": "Não encontramos resultados.",
        "status_resultados": "{n} resultados para “{termo}”",
        "capa": "Capa",
        "fav_on": "✓ Salva nos Favoritos", "fav_off": "⭐ Salvar nos Favoritos",
        "down_on": "✓ Baixado", "down_off": "⬇ Baixar",
        "down_title_on": "Baixado", "down_title_off": "Baixar música",
        "add_album": "＋ Álbum", "add_album_title": "Adicionar a um álbum",
        "criar_album_link": "Criar álbum",
        "remove_fav_title": "Remover dos favoritos", "remove_down_title": "Excluir download",
        "remove_album_title": "Tirar do álbum", "play_title": "Tocar",
        "move_up": "Mover para cima", "move_down": "Mover para baixo",
        "buscar_musicas": "Buscar músicas", "abrir_pasta": "📂 Abrir Pasta",
        "fav_vazio_titulo": "Nenhum favorito ainda",
        "fav_vazio_texto": "Busque uma música e toque em “Salvar nos Favoritos”.",
        "down_vazio_titulo": "Nenhum download realizado",
        "down_vazio_texto": "Vá em Favoritos ou na Busca e clique em “Baixar” nas músicas desejadas.",
        "local_vazio_titulo": "Nenhuma pasta aberta",
        "local_vazio_texto": "Clique no botão acima para selecionar uma pasta do seu dispositivo com músicas.",
        "albuns_vazio_titulo": "Nenhum álbum ainda",
        "albuns_vazio_texto": "Digite um nome acima e clique em “Criar álbum”.",
        "album_vazio_titulo": "Álbum vazio",
        "album_vazio_texto": "Vá em Favoritos e use o menu “＋ Álbum” nas músicas para adicioná-las aqui.",
        "ir_favoritos": "Ir para Favoritos", "voltar_albuns": "← Álbuns",
        "tocar_ordem": "▶ Tocar em Ordem", "tocar_aleatorio": "Tocar Aleatório",
        "excluir_album": "Excluir álbum",
        "toast_fav_off": "Removida dos favoritos", "toast_fav_on": "Salva nos Favoritos",
        "toast_down_off": "Download removido", "toast_down_on": "Música baixada com sucesso!",
        "toast_ja_no_album": "Já está em “{nome}”", "toast_add_album": "Adicionada a “{nome}”",
        "toast_album_existe": "Já existe um álbum com esse nome",
        "toast_album_criado": "Álbum “{nome}” criado", "toast_album_excluido": "Álbum excluído",
        "confirm_excluir": "Excluir o álbum “{nome}”? As músicas continuam nos favoritos.",
        "alerta_sem_suporte": "Seu navegador não suporta a abertura de pastas locais.",
        "alerta_encontradas": "{n} músicas de áudio encontradas na pasta!",
        "pasta_local": "Pasta Local",
    },
    "en": {
        "menu_aria": "Open menu",
        "menu_albuns": "Albums", "menu_albuns_sub": "Your playlists",
        "menu_favoritos": "Favorites", "menu_favoritos_sub": "Favorite songs",
        "menu_downloads": "Downloads", "menu_downloads_sub": "Downloaded songs",
        "menu_local": "Device", "menu_local_sub": "Local music",
        "buscar_placeholder": "Search for an artist or song…", "buscar_btn": "Search",
        "tema_titulo": "Toggle theme", "idioma_titulo": "Language",
        "album_novo_placeholder": "New album name…", "criar_album_btn": "＋ Create album",
        "np_nome_vazio": "Nothing playing", "np_artista_vazio": "Pick a song to listen to",
        "status_inicial": "Type something to get started.",
        "status_digite": "Type the name of an artist or song.",
        "status_buscando": "Searching for songs…",
        "status_erro": "Search failed. Check your internet connection and try again.",
        "status_vazio": "No results found.",
        "status_resultados": "{n} results for “{termo}”",
        "capa": "Cover",
        "fav_on": "✓ Saved to Favorites", "fav_off": "⭐ Save to Favorites",
        "down_on": "✓ Downloaded", "down_off": "⬇ Download",
        "down_title_on": "Downloaded", "down_title_off": "Download song",
        "add_album": "＋ Album", "add_album_title": "Add to an album",
        "criar_album_link": "Create album",
        "remove_fav_title": "Remove from favorites", "remove_down_title": "Delete download",
        "remove_album_title": "Remove from album", "play_title": "Play",
        "move_up": "Move up", "move_down": "Move down",
        "buscar_musicas": "Search songs", "abrir_pasta": "📂 Open Folder",
        "fav_vazio_titulo": "No favorites yet",
        "fav_vazio_texto": "Search for a song and tap “Save to Favorites”.",
        "down_vazio_titulo": "No downloads yet",
        "down_vazio_texto": "Go to Favorites or Search and click “Download” on the songs you want.",
        "local_vazio_titulo": "No folder open",
        "local_vazio_texto": "Click the button above to select a folder on your device with music.",
        "albuns_vazio_titulo": "No albums yet",
        "albuns_vazio_texto": "Type a name above and click “Create album”.",
        "album_vazio_titulo": "Empty album",
        "album_vazio_texto": "Go to Favorites and use the “＋ Album” menu on songs to add them here.",
        "ir_favoritos": "Go to Favorites", "voltar_albuns": "← Albums",
        "tocar_ordem": "▶ Play in Order", "tocar_aleatorio": "Shuffle",
        "excluir_album": "Delete album",
        "toast_fav_off": "Removed from favorites", "toast_fav_on": "Saved to Favorites",
        "toast_down_off": "Download removed", "toast_down_on": "Song downloaded successfully!",
        "toast_ja_no_album": "Already in “{nome}”", "toast_add_album": "Added to “{nome}”",
        "toast_album_existe": "An album with that name already exists",
        "toast_album_criado": "Album “{nome}” created", "toast_album_excluido": "Album deleted",
        "confirm_excluir": "Delete the album “{nome}”? The songs stay in your favorites.",
        "alerta_sem_suporte": "Your browser does not support opening local folders.",
        "alerta_encontradas": "{n} audio files found in the folder!",
        "pasta_local": "Local Folder",
    },
    "es": {
        "menu_aria": "Abrir menú",
        "menu_albuns": "Álbumes", "menu_albuns_sub": "Tus playlists",
        "menu_favoritos": "Favoritos", "menu_favoritos_sub": "Canciones favoritas",
        "menu_downloads": "Descargas", "menu_downloads_sub": "Canciones descargadas",
        "menu_local": "Dispositivo", "menu_local_sub": "Música local",
        "buscar_placeholder": "Busca un artista o canción…", "buscar_btn": "Buscar",
        "tema_titulo": "Cambiar tema", "idioma_titulo": "Idioma",
        "album_novo_placeholder": "Nombre del nuevo álbum…", "criar_album_btn": "＋ Crear álbum",
        "np_nome_vazio": "Nada en reproducción", "np_artista_vazio": "Elige una canción para escuchar",
        "status_inicial": "Escribe algo para empezar.",
        "status_digite": "Escribe el nombre de un artista o canción.",
        "status_buscando": "Buscando canciones…",
        "status_erro": "Error al buscar. Revisa tu conexión a internet e inténtalo de nuevo.",
        "status_vazio": "No encontramos resultados.",
        "status_resultados": "{n} resultados para “{termo}”",
        "capa": "Portada",
        "fav_on": "✓ Guardada en Favoritos", "fav_off": "⭐ Guardar en Favoritos",
        "down_on": "✓ Descargada", "down_off": "⬇ Descargar",
        "down_title_on": "Descargada", "down_title_off": "Descargar canción",
        "add_album": "＋ Álbum", "add_album_title": "Añadir a un álbum",
        "criar_album_link": "Crear álbum",
        "remove_fav_title": "Quitar de favoritos", "remove_down_title": "Eliminar descarga",
        "remove_album_title": "Quitar del álbum", "play_title": "Reproducir",
        "move_up": "Subir", "move_down": "Bajar",
        "buscar_musicas": "Buscar canciones", "abrir_pasta": "📂 Abrir carpeta",
        "fav_vazio_titulo": "Aún no hay favoritos",
        "fav_vazio_texto": "Busca una canción y pulsa “Guardar en Favoritos”.",
        "down_vazio_titulo": "Aún no hay descargas",
        "down_vazio_texto": "Ve a Favoritos o a Buscar y pulsa “Descargar” en las canciones que quieras.",
        "local_vazio_titulo": "Ninguna carpeta abierta",
        "local_vazio_texto": "Pulsa el botón de arriba para elegir una carpeta de tu dispositivo con música.",
        "albuns_vazio_titulo": "Aún no hay álbumes",
        "albuns_vazio_texto": "Escribe un nombre arriba y pulsa “Crear álbum”.",
        "album_vazio_titulo": "Álbum vacío",
        "album_vazio_texto": "Ve a Favoritos y usa el menú “＋ Álbum” en las canciones para añadirlas aquí.",
        "ir_favoritos": "Ir a Favoritos", "voltar_albuns": "← Álbumes",
        "tocar_ordem": "▶ Reproducir en orden", "tocar_aleatorio": "Aleatorio",
        "excluir_album": "Eliminar álbum",
        "toast_fav_off": "Quitada de favoritos", "toast_fav_on": "Guardada en Favoritos",
        "toast_down_off": "Descarga eliminada", "toast_down_on": "¡Canción descargada con éxito!",
        "toast_ja_no_album": "Ya está en “{nome}”", "toast_add_album": "Añadida a “{nome}”",
        "toast_album_existe": "Ya existe un álbum con ese nombre",
        "toast_album_criado": "Álbum “{nome}” creado", "toast_album_excluido": "Álbum eliminado",
        "confirm_excluir": "¿Eliminar el álbum “{nome}”? Las canciones siguen en favoritos.",
        "alerta_sem_suporte": "Tu navegador no permite abrir carpetas locales.",
        "alerta_encontradas": "¡{n} archivos de audio encontrados en la carpeta!",
        "pasta_local": "Carpeta local",
    },
}

# Palavras no singular/plural (usadas por plural()).
PLURAIS = {
    "pt": {"musica": ("música", "músicas"), "musica_favorita": ("música favorita", "músicas favoritas"),
           "musica_baixada": ("música baixada", "músicas baixadas"),
           "arquivo": ("arquivo de áudio encontrado", "arquivos de áudio encontrados"),
           "album": ("álbum", "álbuns")},
    "en": {"musica": ("song", "songs"), "musica_favorita": ("favorite song", "favorite songs"),
           "musica_baixada": ("downloaded song", "downloaded songs"),
           "arquivo": ("audio file found", "audio files found"),
           "album": ("album", "albums")},
    "es": {"musica": ("canción", "canciones"), "musica_favorita": ("canción favorita", "canciones favoritas"),
           "musica_baixada": ("canción descargada", "canciones descargadas"),
           "arquivo": ("archivo de audio encontrado", "archivos de audio encontrados"),
           "album": ("álbum", "álbumes")},
}

CODIGOS_HTML = {"pt": "pt-BR", "en": "en", "es": "es"}   # valor do atributo lang do <html>

idioma = "pt"                  # idioma atual
status_chave = "status_inicial"  # mensagem atual da busca (para retraduzir ao trocar de idioma)
status_kw = {}


def t(chave, **kw):
    """Devolve o texto `chave` no idioma atual (ou em português, se faltar)."""
    texto = TRADUCOES.get(idioma, {}).get(chave) or TRADUCOES["pt"][chave]
    return texto.format(**kw) if kw else texto


def plural(n, chave):
    """Devolve '1 música' / '3 músicas' (ou 'song/songs', 'canción/canciones')."""
    singular, plural_ = PLURAIS[idioma][chave]
    return f"{n} {singular if n == 1 else plural_}"


def definir_status(chave, **kw):
    """Mostra uma mensagem de estado da busca e lembra qual é, para retraduzir depois."""
    global status_chave, status_kw
    status_chave, status_kw = chave, kw
    status.textContent = t(chave, **kw)


def traduzir_js(chave, n=None):
    """Permite ao JavaScript (index.html) pedir textos traduzidos."""
    return t(chave, n=n)


def abrir_idioma_ou_fechar():
    abrindo = lang_popup.hidden
    lang_popup.hidden = not abrindo
    lang_btn.setAttribute("aria-expanded", "true" if abrindo else "false")


def fechar_idioma():
    lang_popup.hidden = True
    lang_btn.setAttribute("aria-expanded", "false")


def aplicar_idioma(codigo):
    """Troca o idioma do site inteiro e lembra a escolha."""
    global idioma
    idioma = codigo if codigo in TRADUCOES else "pt"
    guardar("idioma", idioma)
    document.documentElement.setAttribute("lang", CODIGOS_HTML[idioma])

    # Textos fixos do HTML, marcados com data-i18n*
    for el in document.querySelectorAll("[data-i18n]"):
        el.textContent = t(el.getAttribute("data-i18n"))
    for el in document.querySelectorAll("[data-i18n-placeholder]"):
        el.setAttribute("placeholder", t(el.getAttribute("data-i18n-placeholder")))
    for el in document.querySelectorAll("[data-i18n-title]"):
        el.setAttribute("title", t(el.getAttribute("data-i18n-title")))
    for el in document.querySelectorAll("[data-i18n-aria]"):
        el.setAttribute("aria-label", t(el.getAttribute("data-i18n-aria")))

    # Botão do idioma e opção marcada no pop-up
    lang_atual.textContent = idioma.upper()
    for op in document.querySelectorAll("[data-idioma]"):
        if op.getAttribute("data-idioma") == idioma:
            op.classList.add("ativo")
        else:
            op.classList.remove("ativo")

    # Textos dinâmicos: mensagem da busca, botões dos cards e a tela aberta
    status.textContent = t(status_chave, **status_kw)
    for id_ in list(resultados_atuais):
        atualizar_botoes_card(id_)
    mostrar_tela()


favoritos = carregar("favoritos", {})
downloads = carregar("downloads", {})
albuns = carregar("albuns", {})
resultados_atuais = {}

tela = "busca"
album_aberto = None
timer_aviso = None

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


def html_card(m):
    id_ = escape(m["id"])
    nome = escape(m["nome"])
    artista = escape(m["artista"])
    capa = escape(m["capa"])
    audio = escape(m["audio"])

    salva = id_ in favoritos
    classe_fav = "btn-salvar ativo" if salva else "btn-salvar"
    texto_fav = t("fav_on") if salva else t("fav_off")

    baixada = id_ in downloads
    classe_down = "btn-salvar ativo" if baixada else "btn-salvar"
    texto_down = t("down_on") if baixada else t("down_off")

    return f"""
    <article class="card">
      <div class="capa"><img src="{capa}" alt="{t('capa')}" loading="lazy"></div>
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
            f'<select data-acao="add-album" data-id="{id_}" title="{t("add_album_title")}">'
            f'<option value="">{t("add_album")}</option>{opcoes}</select>'
        )
    else:
        extra = f'<button class="link" data-acao="ir-albuns">{t("criar_album_link")}</button>'

    baixada = id_ in downloads
    titulo_baixar = t("down_title_on") if baixada else t("down_title_off")
    classe_baixar = "icone pequeno ativo" if baixada else "icone pequeno"
    
    # Apenas o ícone compacto, sem texto ao lado
    icone_texto = "✓" if baixada else "⬇"
    btn_baixar = f'<button class="{classe_baixar}" data-acao="baixar-musica" data-id="{id_}" data-nome="{escape(m["nome"])}" data-artista="{escape(m["artista"])}" data-capa="{escape(m["capa"])}" data-audio="{escape(m["audio"])}" title="{titulo_baixar}">{icone_texto}</button>'

    botao_remover = (
        f'<button class="icone pequeno" data-acao="remover-favorito" data-id="{id_}" '
        f'title="{t("remove_fav_title")}">✕</button>'
    )

    return f"""
    <li class="linha">
      <button class="play" data-acao="tocar-favorito" data-id="{id_}" title="{t('play_title')}">▶</button>
      <img src="{escape(m['capa'])}" alt="">
      <div class="info"><strong>{escape(m['nome'])}</strong><span>{escape(m['artista'])}</span></div>
      {extra}
      {btn_baixar}
      {botao_remover}
    </li>"""

def html_linha_download(m):
    id_ = escape(m["id"])
    botao_remover = (
        f'<button class="icone pequeno" data-acao="remover-download" data-id="{id_}" '
        f'title="{t("remove_down_title")}">✕</button>'
    )
    return f"""
    <li class="linha">
      <button class="play" data-acao="tocar-download" data-id="{id_}" title="{t('play_title')}">▶</button>
      <img src="{escape(m['capa'])}" alt="">
      <div class="info"><strong>{escape(m['nome'])}</strong><span>{escape(m['artista'])}</span></div>
      {botao_remover}
    </li>"""

def html_linha_local(m):
    id_ = escape(m["id"])
    return f"""
    <li class="linha">
      <button class="play" data-acao="tocar-local" data-id="{id_}" title="{t('play_title')}">▶</button>
      <div class="tocando-capa" style="width:48px;height:48px;border-radius:9px;font-size:1.2rem;">📂</div>
      <div class="info"><strong>{escape(m['nome'])}</strong><span>{escape(m['artista'])}</span></div>
    </li>"""

def html_linha_album(m, index, total):
    id_ = escape(m["id"])
    desativar_cima = "disabled style='opacity: 0.3; cursor: not-allowed;'" if index == 0 else ""
    desativar_baixo = "disabled style='opacity: 0.3; cursor: not-allowed;'" if index == total - 1 else ""

    return f"""
    <li class="linha" data-id="{id_}">
      <button class="play" data-acao="tocar-album-index" data-index="{index}" title="{t('play_title')}">▶</button>
      <img src="{escape(m['capa'])}" alt="">
      <div class="info"><strong>{escape(m['nome'])}</strong><span>{escape(m['artista'])}</span></div>
      <div class="linha-acoes">
        <button class="icone pequeno" data-acao="mover-cima" data-index="{index}" title="{t('move_up')}" {desativar_cima}>▲</button>
        <button class="icone pequeno" data-acao="mover-baixo" data-index="{index}" title="{t('move_down')}" {desativar_baixo}>▼</button>
        <button class="icone pequeno" data-acao="remover-do-album" data-id="{id_}" title="{t('remove_album_title')}">✕</button>
      </div>
    </li>"""

def html_card_album(nome, ids):
    capas = [favoritos[i]["capa"] for i in ids if i in favoritos]
    if len(capas) >= 4:
        arte = '<div class="mosaico">' + "".join(
            f'<img src="{escape(c)}" alt="">' for c in capas[:4]
        ) + "</div>"
    elif capas:
        arte = f'<img src="{escape(capas[0])}" alt="">'
    else:
        arte = '<span class="arte-vazia">♫</span>'
    return f"""
    <button class="album-card" data-acao="abrir-album" data-nome="{escape(nome)}">
      <div class="album-capa">{arte}</div>
      <strong>{escape(nome)}</strong>
      <span>{plural(len(ids), 'musica')}</span>
    </button>"""

def renderizar_favoritos():
    n = len(favoritos)
    cabecalho = f"""
    <div class="tela-topo">
      <div><h1>{t('menu_favoritos')}</h1><p>{plural(n, 'musica_favorita')}</p></div>
    </div>"""
    if favoritos:
        corpo = '<ul class="lista">' + "".join(
            html_linha_favorito(m) for m in favoritos.values()
        ) + "</ul>"
    else:
        corpo = f"""
        <div class="vazio">
          <div class="vazio-icone">⭐</div>
          <h2>{t('fav_vazio_titulo')}</h2>
          <p>{t('fav_vazio_texto')}</p>
          <button class="primario" data-acao="ir-busca">{t('buscar_musicas')}</button>
        </div>"""
    TELAS["favoritos"].innerHTML = cabecalho + corpo

def renderizar_downloads():
    n = len(downloads)
    cabecalho = f"""
    <div class="tela-topo">
      <div><h1>{t('menu_downloads')}</h1><p>{plural(n, 'musica_baixada')}</p></div>
    </div>"""
    if downloads:
        corpo = '<ul class="lista">' + "".join(
            html_linha_download(m) for m in downloads.values()
        ) + "</ul>"
    else:
        corpo = f"""
        <div class="vazio">
          <div class="vazio-icone">⬇️</div>
          <h2>{t('down_vazio_titulo')}</h2>
          <p>{t('down_vazio_texto')}</p>
          <button class="primario" data-acao="ir-busca">{t('buscar_musicas')}</button>
        </div>"""
    TELAS["downloads"].innerHTML = cabecalho + corpo

def renderizar_local():
    try:
        lista_local = window.localMusicas.to_py() if hasattr(window.localMusicas, "to_py") else []
    except Exception:
        lista_local = []
    n = len(lista_local)
    cabecalho = f"""
    <div class="tela-topo">
      <div><h1>{t('menu_local')}</h1><p>{plural(n, 'arquivo')}</p></div>
      <button class="primario" data-acao="escolher-pasta-dispositivo">{t('abrir_pasta')}</button>
    </div>"""
    if n > 0:
        corpo = '<ul class="lista">' + "".join(html_linha_local(m) for m in lista_local) + "</ul>"
    else:
        corpo = f"""
        <div class="vazio">
          <div class="vazio-icone">📂</div>
          <h2>{t('local_vazio_titulo')}</h2>
          <p>{t('local_vazio_texto')}</p>
          <button class="primario" data-acao="escolher-pasta-dispositivo">{t('abrir_pasta')}</button>
        </div>"""
    TELAS["local"].innerHTML = cabecalho + corpo

def renderizar_albuns():
    albuns_sub.textContent = plural(len(albuns), "album")
    if albuns:
        grade_albuns.innerHTML = "".join(html_card_album(n, ids) for n, ids in albuns.items())
    else:
        grade_albuns.innerHTML = f"""
        <div class="vazio">
          <div class="vazio-icone">💿</div>
          <h2>{t('albuns_vazio_titulo')}</h2>
          <p>{t('albuns_vazio_texto')}</p>
        </div>"""

def renderizar_album():
    if album_aberto not in albuns:
        return
    ids = albuns[album_aberto]
    musicas = [favoritos[i] for i in ids if i in favoritos]
    total = len(musicas)
    if musicas:
        controles_topo = f"""
        <div class="album-controles">
          <button class="primario" data-acao="tocar-album-sequencial">{t('tocar_ordem')}</button>
          <button class="icone" data-acao="tocar-album-aleatorio" title="{t('tocar_aleatorio')}">🔀</button>
        </div>"""
        lista_html = "".join(html_linha_album(m, i, total) for i, m in enumerate(musicas))
        corpo = controles_topo + '<ul class="lista">' + lista_html + "</ul>"
    else:
        corpo = f"""
        <div class="vazio">
          <div class="vazio-icone">🎶</div>
          <h2>{t('album_vazio_titulo')}</h2>
          <p>{t('album_vazio_texto')}</p>
          <button class="primario" data-acao="ir-favoritos">{t('ir_favoritos')}</button>
        </div>"""
    TELAS["album"].innerHTML = f"""
    <button class="voltar" data-acao="ir-albuns">{t('voltar_albuns')}</button>
    <div class="tela-topo">
      <div><h1>{escape(album_aberto)}</h1><p>{plural(total, 'musica')}</p></div>
      <button class="perigo" data-acao="excluir-album">{t('excluir_album')}</button>
    </div>
    {corpo}"""

def atualizar_contadores():
    menu_qtd_albuns.textContent = str(len(albuns))
    menu_qtd_favoritos.textContent = str(len(favoritos))
    menu_qtd_downloads.textContent = str(len(downloads))
    try:
        lista_local = window.localMusicas.to_py() if hasattr(window.localMusicas, "to_py") else []
        menu_qtd_local.textContent = str(len(lista_local))
    except Exception:
        menu_qtd_local.textContent = "0"

def mostrar_tela():
    for nome, secao in TELAS.items():
        secao.hidden = nome != tela
    if tela == "favoritos":
        renderizar_favoritos()
    elif tela == "downloads":
        renderizar_downloads()
    elif tela == "local":
        renderizar_local()
    elif tela == "albuns":
        renderizar_albuns()
    elif tela == "album":
        renderizar_album()
    atualizar_contadores()

def ir_para(nova_tela, album=None):
    global tela, album_aberto
    tela = nova_tela
    album_aberto = album
    fechar_menu()
    mostrar_tela()
    area_rolagem.scrollTop = 0

def avisar(texto):
    global timer_aviso
    toast.textContent = texto
    toast.classList.add("mostra")
    if timer_aviso is not None:
        window.clearTimeout(timer_aviso)
    timer_aviso = window.setTimeout(PROXY_ESCONDER_AVISO, 2000)

def esconder_aviso():
    toast.classList.remove("mostra")

PROXY_ESCONDER_AVISO = create_proxy(esconder_aviso)

def abrir_menu_ou_fechar():
    abrindo = menu_popup.hidden
    menu_popup.hidden = not abrindo
    botao_menu.setAttribute("aria-expanded", "true" if abrindo else "false")

def fechar_menu():
    menu_popup.hidden = True
    botao_menu.setAttribute("aria-expanded", "false")

def atualizar_botoes_card(id_):
    botao_fav = document.querySelector(f'[data-acao="favoritar"][data-id="{id_}"]')
    if botao_fav:
        if id_ in favoritos:
            botao_fav.className = "btn-salvar ativo"
            botao_fav.textContent = t("fav_on")
        else:
            botao_fav.className = "btn-salvar"
            botao_fav.textContent = t("fav_off")
    botao_down = document.querySelector(f'[data-acao="baixar-musica"][data-id="{id_}"]')
    if botao_down:
        if id_ in downloads:
            botao_down.className = "btn-salvar ativo"
            botao_down.textContent = t("down_on")
        else:
            botao_down.className = "btn-salvar"
            botao_down.textContent = t("down_off")

def obter_ou_criar_musica(alvo, id_):
    if id_ in downloads:
        return downloads[id_]
    if id_ in favoritos:
        return favoritos[id_]
    if id_ in resultados_atuais:
        return resultados_atuais[id_]
    nome = alvo.getAttribute("data-nome")
    artista = alvo.getAttribute("data-artista")
    capa = alvo.getAttribute("data-capa")
    audio = alvo.getAttribute("data-audio")
    if nome and audio:
        return {
            "id": id_,
            "nome": nome,
            "artista": artista or "Artista desconhecido",
            "capa": capa or "",
            "audio": audio,
            "audio_completo": audio,
        }
    return None

def favoritar_ou_remover(id_, alvo):
    if id_ in favoritos:
        del favoritos[id_]
        for ids in albuns.values():
            if id_ in ids:
                ids.remove(id_)
        avisar(t("toast_fav_off"))
    else:
        musica = obter_ou_criar_musica(alvo, id_)
        if musica:
            favoritos[id_] = musica
            avisar(t("toast_fav_on"))
    guardar("favoritos", favoritos)
    guardar("albuns", albuns)
    atualizar_botoes_card(id_)
    mostrar_tela()

def baixar_musica(id_, alvo):
    if id_ in downloads:
        del downloads[id_]
        guardar("downloads", downloads)
        avisar(t("toast_down_off"))
    else:
        musica = obter_ou_criar_musica(alvo, id_)
        if musica:
            downloads[id_] = musica
            guardar("downloads", downloads)
            nome_arquivo = f"{musica['artista']} - {musica['nome']}"
            window.baixarArquivoNoAparelho(musica["audio"], nome_arquivo)
            avisar(t("toast_down_on"))
    atualizar_botoes_card(id_)
    mostrar_tela()

def escolher_pasta_dispositivo():
    window.selecionarPastaDispositivo()

def remover_download(id_):
    if id_ in downloads:
        del downloads[id_]
        guardar("downloads", downloads)
        avisar(t("toast_down_off"))
        mostrar_tela()

def tocar_musica_obj(musica, sem_limite=False):
    if not musica:
        return
    player.src = musica.get("audio_completo") if sem_limite else musica["audio"]
    player.play()
    np_nome.removeAttribute("data-i18n")      # agora mostra o nome da música
    np_artista.removeAttribute("data-i18n")
    np_capa.innerHTML = f'<img src="{escape(musica["capa"])}" alt="">' if musica.get("capa") else "📂"
    np_nome.textContent = musica["nome"]
    np_artista.textContent = musica["artista"]

def tocar_favorito(id_):
    musica = favoritos.get(id_)
    tocar_musica_obj(musica, sem_limite=True)

def tocar_download(id_):
    musica = downloads.get(id_)
    tocar_musica_obj(musica, sem_limite=True)

def tocar_local(id_):
    try:
        lista_local = window.localMusicas.to_py() if hasattr(window.localMusicas, "to_py") else []
    except Exception:
        lista_local = []
    for m in lista_local:
        if m["id"] == id_:
            tocar_musica_obj(m, sem_limite=True)
            break

def tocar_album_por_indice(index):
    if album_aberto not in albuns:
        return
    ids = albuns[album_aberto]
    musicas = [favoritos[i] for i in ids if i in favoritos]
    if 0 <= index < len(musicas):
        tocar_musica_obj(musicas[index], sem_limite=True)

def mover_musica_album(index, direcao):
    if album_aberto not in albuns:
        return
    ids = albuns[album_aberto]
    novo_index = index + direcao
    if 0 <= novo_index < len(ids):
        ids[index], ids[novo_index] = ids[novo_index], ids[index]
        guardar("albuns", albuns)
        renderizar_album()

def adicionar_ao_album(nome, id_):
    ids = albuns.setdefault(nome, [])
    if id_ in ids:
        avisar(t("toast_ja_no_album", nome=nome))
        return
    ids.append(id_)
    guardar("albuns", albuns)
    avisar(t("toast_add_album", nome=nome))
    mostrar_tela()

def criar_album(evento):
    evento.preventDefault()
    nome = campo_album.value.strip()
    if not nome:
        return
    if nome in albuns:
        avisar(t("toast_album_existe"))
        return
    albuns[nome] = []
    guardar("albuns", albuns)
    campo_album.value = ""
    avisar(t("toast_album_criado", nome=nome))
    mostrar_tela()

def excluir_album():
    if window.confirm(t("confirm_excluir", nome=album_aberto)):
        albuns.pop(album_aberto, None)
        guardar("albuns", albuns)
        avisar(t("toast_album_excluido"))
        ir_para("albuns")

def ao_enviar_busca(evento):
    evento.preventDefault()
    asyncio.ensure_future(executar_busca())

async def executar_busca():
    global resultados_atuais
    termo = campo_busca.value.strip()
    if not termo:
        definir_status("status_digite")
        return

    ir_para("busca")
    grade.innerHTML = ""
    definir_status("status_buscando")

    try:
        resultados = await buscar_musicas(termo)
    except Exception:
        definir_status("status_erro")
        return

    musicas = [simplificar(m) for m in resultados if m.get("previewUrl")]

    if not musicas:
        definir_status("status_vazio")
        return

    resultados_atuais = {m["id"]: m for m in musicas}
    definir_status("status_resultados", n=len(musicas), termo=termo)
    grade.innerHTML = "".join(html_card(m) for m in musicas)


# ---------- Fila de reprodução do álbum ----------
fila_album = []   # músicas que serão tocadas em sequência
pos_album = -1    # posição atual na fila


def limpar_fila():
    """Cancela a fila (usado quando o utilizador toca uma música avulsa)."""
    global fila_album, pos_album
    fila_album = []
    pos_album = -1


def tocar_da_fila(pos):
    """Toca a música da posição `pos` da fila."""
    global pos_album
    if 0 <= pos < len(fila_album):
        pos_album = pos
        tocar_musica_obj(fila_album[pos], sem_limite=True)


def musicas_do_album():
    """Lista as músicas do álbum aberto (na ordem guardada)."""
    if album_aberto not in albuns:
        return []
    return [favoritos[i] for i in albuns[album_aberto] if i in favoritos]


def tocar_album(aleatorio=False):
    """Inicia o álbum aberto, em ordem ou aleatório."""
    global fila_album
    musicas = musicas_do_album()
    if not musicas:
        return
    fila_album = list(musicas)
    if aleatorio:
        random.shuffle(fila_album)
    tocar_da_fila(0)


def ao_terminar_musica(evento):
    """Quando a música do player termina, passa à seguinte da fila."""
    if fila_album and evento.target.isSameNode(player):
        tocar_da_fila(pos_album + 1)


# ---------- Tema ----------
def aplicar_tema(tema):
    document.documentElement.setAttribute("data-theme", tema)
    guardar("tema", tema)


def alternar_tema(evento):
    atual = document.documentElement.getAttribute("data-theme")
    aplicar_tema("light" if atual == "dark" else "dark")


# ---------- Eventos ----------
def ao_clicar(evento):
    """Ouvinte ÚNICO de cliques (delegação de eventos): lê o data-acao do botão."""
    global fila_album, pos_album

    # Clique fora do pop-up fecha o pop-up
    if evento.target.closest(".menu-wrap") is None:
        fechar_menu()
    if evento.target.closest(".idioma-wrap") is None:
        fechar_idioma()

    alvo = evento.target.closest("[data-acao]")
    if alvo is None:
        return
    acao = alvo.getAttribute("data-acao")
    id_ = alvo.getAttribute("data-id")

    if acao == "menu":
        abrir_menu_ou_fechar()
    elif acao == "idioma":
        abrir_idioma_ou_fechar()
    elif acao == "escolher-idioma":
        aplicar_idioma(alvo.getAttribute("data-idioma"))
        fechar_idioma()
    elif acao == "ir-albuns":
        ir_para("albuns")
    elif acao == "ir-favoritos":
        ir_para("favoritos")
    elif acao == "ir-downloads":
        ir_para("downloads")
    elif acao == "ir-local":
        ir_para("local")
    elif acao == "ir-busca":
        ir_para("busca")
    elif acao == "abrir-album":
        ir_para("album", alvo.getAttribute("data-nome"))
    elif acao == "excluir-album":
        excluir_album()
    elif acao in ("favoritar", "remover-favorito"):
        favoritar_ou_remover(id_, alvo)
    elif acao == "baixar-musica":
        baixar_musica(id_, alvo)
    elif acao == "remover-download":
        remover_download(id_)
    elif acao == "remover-do-album":
        if id_ in albuns.get(album_aberto, []):
            albuns[album_aberto].remove(id_)
            guardar("albuns", albuns)
            mostrar_tela()
    elif acao == "mover-cima":
        mover_musica_album(int(alvo.getAttribute("data-index")), -1)
    elif acao == "mover-baixo":
        mover_musica_album(int(alvo.getAttribute("data-index")), 1)
    elif acao == "tocar-favorito":
        limpar_fila()
        tocar_favorito(id_)
    elif acao == "tocar-download":
        limpar_fila()
        tocar_download(id_)
    elif acao == "tocar-local":
        limpar_fila()
        tocar_local(id_)
    elif acao == "tocar-album-index":
        # Toca a partir desta música e continua pelas seguintes do álbum.
        fila_album = musicas_do_album()
        tocar_da_fila(int(alvo.getAttribute("data-index")))
    elif acao == "tocar-album-sequencial":
        tocar_album(aleatorio=False)
    elif acao == "tocar-album-aleatorio":
        tocar_album(aleatorio=True)
    elif acao == "escolher-pasta-dispositivo":
        escolher_pasta_dispositivo()


def ao_mudar(evento):
    """Menu '＋ Álbum' das músicas favoritas."""
    alvo = evento.target
    if alvo.getAttribute("data-acao") == "add-album" and alvo.value:
        adicionar_ao_album(alvo.value, alvo.getAttribute("data-id"))


def pausar_outros(evento):
    """Um áudio de cada vez: quando um começa, pausa os outros."""
    for a in document.querySelectorAll("audio"):
        if not a.isSameNode(evento.target):
            a.pause()


def ao_teclar(evento):
    if evento.key == "Escape":
        fechar_menu()
        fechar_idioma()


def atualizar_tela_local():
    """Chamada pelo JavaScript depois de escolher a pasta do dispositivo."""
    if tela == "local":
        mostrar_tela()
    else:
        atualizar_contadores()


form_busca.addEventListener("submit", create_proxy(ao_enviar_busca))
form_album.addEventListener("submit", create_proxy(criar_album))
document.addEventListener("click", create_proxy(ao_clicar))
document.addEventListener("change", create_proxy(ao_mudar))
document.addEventListener("keydown", create_proxy(ao_teclar))
# 'play' e 'ended' não "borbulham", por isso usamos a fase de captura (True).
document.addEventListener("play", create_proxy(pausar_outros), True)
document.addEventListener("ended", create_proxy(ao_terminar_musica), True)
botao_tema.addEventListener("click", create_proxy(alternar_tema))

# Deixa o JavaScript avisar o Python quando a pasta do dispositivo for lida.
window.atualizarTelaLocalPy = create_proxy(atualizar_tela_local)


# ---------- Início ----------
tema_salvo = carregar("tema", None)
if tema_salvo:
    document.documentElement.setAttribute("data-theme", tema_salvo)

# Deixa o JavaScript pedir textos traduzidos (usado nos alertas do index.html)
window.traduzir = create_proxy(traduzir_js)

# Idioma inicial: o que o utilizador escolheu da última vez; senão, o do navegador.
idioma_salvo = carregar("idioma", None)
if idioma_salvo not in TRADUCOES:
    try:
        idioma_salvo = str(window.navigator.language)[:2].lower()
    except Exception:
        idioma_salvo = "pt"
aplicar_idioma(idioma_salvo)   # também desenha a tela inicial
