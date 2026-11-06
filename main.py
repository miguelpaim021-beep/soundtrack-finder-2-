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

def guardar(chave, valor):
    try:
        window.localStorage.setItem(chave, json.dumps(valor))
    except Exception:
        pass

favoritos = carregar("favoritos", {})
downloads = carregar("downloads", {})
albuns = carregar("albuns", {})
idioma_atual = carregar("idioma", "pt")
select_idioma.value = idioma_atual

resultados_atuais = {}
tela = "busca"
album_aberto = None
timer_aviso = None

def t(chave):
    return TRADUCOES.get(idioma_atual, TRADUCOES["pt"]).get(chave, chave)

def atualizar_textos_estaticos():
    for el in document.querySelectorAll("[data-i18n]"):
        chave = el.getAttribute("data-i18n")
        el.textContent = t(chave)
    for el in document.querySelectorAll("[data-i18n-placeholder]"):
        chave = el.getAttribute("data-i18n-placeholder")
        el.setAttribute("placeholder", t(chave))

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
    texto_fav = t("salvo_fav") if salva else t("salvar_fav")

    baixada = id_ in downloads
    classe_down = "btn-salvar ativo" if baixada else "btn-salvar"
    texto_down = t("baixado") if baixada else t("baixar")

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
        extra = f'<button class="link" data-acao="ir-albuns">{t("btn_criar_album")}</button>'

    baixada = id_ in downloads
    titulo_baixar = "Baixado" if baixada else "Baixar música"
    classe_baixar = "icone pequeno ativo" if baixada else "icone pequeno"
    
    # Apenas o ícone compacto
    icone_texto = "✓" if baixada else "⬇"
    btn_baixar = f'<button class="{classe_baixar}" data-acao="baixar-musica" data-id="{id_}" data-nome="{escape(m["nome"])}" data-artista="{escape(m["artista"])}" data-capa="{escape(m["capa"])}" data-audio="{escape(m["audio"])}" title="{titulo_baixar}">{icone_texto}</button>'

    botao_remover = (
        f'<button class="icone pequeno" data-acao="remover-favorito" data-id="{id_}" '
        f'title="Remover dos favoritos">✕</button>'
    )

    return f"""
    <li class="linha">
      <button class="play" data-acao="tocar-favorito" data-id="{id_}" title="Tocar">▶</button>
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
        f'title="Excluir download">✕</button>'
    )
    return f"""
    <li class="linha">
      <button class="play" data-acao="tocar-download" data-id="{id_}" title="Tocar">▶</button>
      <img src="{escape(m['capa'])}" alt="">
      <div class="info"><strong>{escape(m['nome'])}</strong><span>{escape(m['artista'])}</span></div>
      {botao_remover}
    </li>"""

def html_linha_local(m):
    id_ = escape(m["id"])
    return f"""
    <li class="linha">
      <button class="play" data-acao="tocar-local" data-id="{id_}" title="Tocar">▶</button>
      <div class="tocando-capa" style="width:48px;height:48px;border-radius:9px;font-size:1.2rem;">📂</div>
      <div class="info"><strong>{escape(m['nome'])}</strong><span>{escape(m['artista'])}</span></div>
    </li>"""

def html_linha_album(m, index, total):
    id_ = escape(m["id"])
    desativar_cima = "disabled style='opacity: 0.3; cursor: not-allowed;'" if index == 0 else ""
    desativar_baixo = "disabled style='opacity: 0.3; cursor: not-allowed;'" if index == total - 1 else ""

    return f"""
    <li class="linha" data-id="{id_}">
      <button class="play" data-acao="tocar-album-index" data-index="{index}" title="Tocar">▶</button>
      <img src="{escape(m['capa'])}" alt="">
      <div class="info"><strong>{escape(m['nome'])}</strong><span>{escape(m['artista'])}</span></div>
      <div class="linha-acoes">
        <button class="icone pequeno" data-acao="mover-cima" data-index="{index}" title="Mover para cima" {desativar_cima}>▲</button>
        <button class="icone pequeno" data-acao="mover-baixo" data-index="{index}" title="Mover para baixo" {desativar_baixo}>▼</button>
        <button class="icone pequeno" data-acao="remover-do-album" data-id="{id_}" title="Tirar do álbum">✕</button>
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
      <span>{plural(len(ids), 'música', 'músicas')}</span>
    </button>"""

def renderizar_favoritos():
    n = len(favoritos)
    cabecalho = f"""
    <div class="tela-topo">
      <div><h1>{t("menu_favoritos")}</h1><p>{plural(n, 'música favorita', 'músicas favoritas')}</p></div>
    </div>"""
    if favoritos:
        corpo = '<ul class="lista">' + "".join(
            html_linha_favorito(m) for m in favoritos.values()
        ) + "</ul>"
    else:
        corpo = f"""
        <div class="vazio">
          <div class="vazio-icone">⭐</div>
          <h2>{t("nenhum_fav_titulo")}</h2>
          <p>{t("nenhum_fav_desc")}</p>
          <button class="primario" data-acao="ir-busca">{t("btn_pesquisar")}</button>
        </div>"""
    TELAS["favoritos"].innerHTML = cabecalho + corpo

def renderizar_downloads():
    n = len(downloads)
    cabecalho = f"""
    <div class="tela-topo">
      <div><h1>{t("menu_downloads")}</h1><p>{plural(n, 'música baixada', 'músicas baixadas')}</p></div>
    </div>"""
    if downloads:
        corpo = '<ul class="lista">' + "".join(
            html_linha_download(m) for m in downloads.values()
        ) + "</ul>"
    else:
        corpo = f"""
        <div class="vazio">
          <div class="vazio-icone">⬇️</div>
          <h2>{t("nenhum_down_titulo")}</h2>
          <p>{t("nenhum_down_desc")}</p>
          <button class="primario" data-acao="ir-busca">{t("btn_pesquisar")}</button>
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
      <div><h1>{t("menu_local")}</h1><p>{plural(n, 'arquivo de áudio encontrado', 'arquivos de áudio encontrados')}</p></div>
      <button class="primario" data-acao="escolher-pasta-dispositivo">{t("abrir_pasta")}</button>
    </div>"""
    if n > 0:
        corpo = '<ul class="lista">' + "".join(html_linha_local(m) for m in lista_local) + "</ul>"
    else:
        corpo = f"""
        <div class="vazio">
          <div class="vazio-icone">📂</div>
          <h2>{t("nenhuma_pasta")}</h2>
          <p>{t("nenhuma_pasta_desc")}</p>
          <button class="primario" data-acao="escolher-pasta-dispositivo">{t("abrir_pasta")}</button>
        </div>"""
    TELAS["local"].innerHTML = cabecalho + corpo

def renderizar_albuns():
    albuns_sub.textContent = plural(len(albuns), "álbum", "álbuns")
    if albuns:
        grade_albuns.innerHTML = "".join(html_card_album(n, ids) for n, ids in albuns.items())
    else:
        grade_albuns.innerHTML = f"""
        <div class="vazio">
          <div class="vazio-icone">💿</div>
          <h2>{t("menu_albuns")}</h2>
          <p>{t("album_placeholder")}</p>
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
          <button class="primario" data-acao="tocar-album-sequencial">▶ Tocar em Ordem</button>
          <button class="icone" data-acao="tocar-album-aleatorio" title="Tocar Aleatório">🔀</button>
        </div>"""
        lista_html = "".join(html_linha_album(m, i, total) for i, m in enumerate(musicas))
        corpo = controles_topo + '<ul class="lista">' + lista_html + "</ul>"
    else:
        corpo = f"""
        <div class="vazio">
          <div class="vazio-icone">🎶</div>
          <h2>Álbum vazio</h2>
          <p>{t("menu_favoritos")}</p>
          <button class="primario" data-acao="ir-favoritos">Ir para Favoritos</button>
        </div>"""
    TELAS["album"].innerHTML = f"""
    <button class="voltar" data-acao="ir-albuns">← {t("menu_albuns")}</button>
    <div class="tela-topo">
      <div><h1>{escape(album_aberto)}</h1><p>{plural(total, 'música', 'músicas')}</p></div>
      <button class="perigo" data-acao="excluir-album">Excluir álbum</button>
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
    atualizar_textos_estaticos()
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
            botao_fav.textContent = t("salvo_fav")
        else:
   
