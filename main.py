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
    titulo_baixar = "Baixado" if baixada else "Baixar música"
    classe_baixar = "icone pequeno ativo" if baixada else "icone pequeno"
    
    # Exibe apenas o ícone sem texto quebrado
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
      <div><h1>Favoritos</h1><p>{plural(n, 'música favorita', 'músicas favoritas')}</p></div>
    </div>"""
    if favoritos:
        corpo = '<ul class="lista">' + "".join(
            html_linha_favorito(m) for m in favoritos.values()
        ) + "</ul>"
    else:
        corpo = """
        <div class="vazio">
          <div class="vazio-icone">⭐</div>
          <h2>Nenhum favorito ainda</h2>
          <p>Busque uma música e toque em “Salvar nos Favoritos”.</p>
          <button class="primario" data-acao="ir-busca">Buscar músicas</button>
        </div>"""
    TELAS["favoritos"].innerHTML = cabecalho + corpo

def renderizar_downloads():
    n = len(downloads)
    cabecalho = f"""
    <div class="tela-topo">
      <div><h1>Downloads</h1><p>{plural(n, 'música baixada', 'músicas baixadas')}</p></div>
    </div>"""
    if downloads:
        corpo = '<ul class="lista">' + "".join(
            html_linha_download(m) for m in downloads.values()
        ) + "</ul>"
    else:
        corpo = """
        <div class="vazio">
          <div class="vazio-icone">⬇️</div>
          <h2>Nenhum download realizado</h2>
          <p>Vá em Favoritos ou na Busca e clique em “Baixar” nas músicas desejadas.</p>
          <button class="primario" data-acao="ir-busca">Buscar músicas</button>
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
      <div><h1>Dispositivo</h1><p>{plural(n, 'arquivo de áudio encontrado', 'arquivos de áudio encontrados')}</p></div>
      <button class="primario" data-acao="escolher-pasta-dispositivo">📂 Abrir Pasta</button>
    </div>"""
    if n > 0:
        corpo = '<ul class="lista">' + "".join(html_linha_local(m) for m in lista_local) + "</ul>"
    else:
        corpo = """
        <div class="vazio">
          <div class="vazio-icone">📂</div>
          <h2>Nenhuma pasta aberta</h2>
          <p>Clique no botão acima para selecionar uma pasta do seu dispositivo com músicas.</p>
          <button class="primario" data-acao="escolher-pasta-dispositivo">📂 Abrir Pasta</button>
        </div>"""
    TELAS["local"].innerHTML = cabecalho + corpo

def renderizar_albuns():
    albuns_sub.textContent = plural(len(albuns), "álbum", "álbuns")
    if albuns:
        grade_albuns.innerHTML = "".join(html_card_album(n, ids) for n, ids in albuns.items())
    else:
        grade_albuns.innerHTML = """
        <div class="vazio">
          <div class="vazio-icone">💿</div>
          <h2>Nenhum álbum ainda</h2>
          <p>Digite um nome acima e clique em “Criar álbum”.</p>
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
        corpo = """
        <div class="vazio">
          <div class="vazio-icone">🎶</div>
          <h2>Álbum vazio</h2>
          <p>Vá em Favoritos e use o menu “＋ Álbum” nas músicas para adicioná-las aqui.</p>
          <button class="primario" data-acao="ir-favoritos">Ir para Favoritos</button>
        </div>"""
    TELAS["album"].innerHTML = f"""
    <button class="voltar" data-acao="ir-albuns">← Álbuns</button>
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
            botao_fav.textContent = "✓ Salva nos Favoritos"
        else:
            botao_fav.className = "btn-salvar"
            botao_fav.textContent = "⭐ Salvar nos Favoritos"
    botao_down = document.querySelector(f'[data-acao="baixar-musica"][data-id="{id_}"]')
    if botao_down:
        if id_ in downloads:
            botao_down.className = "btn-salvar ativo"
            botao_down.textContent = "✓ Baixado"
        else:
            botao_down.className = "btn-salvar"
            botao_down.textContent = "⬇ Baixar"

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
        avisar("Removida dos favoritos")
    else:
        musica = obter_ou_criar_musica(alvo, id_)
        if musica:
            favoritos[id_] = musica
            avisar("Salva nos Favoritos")
    guardar("favoritos", favoritos)
    guardar("albuns", albuns)
    atualizar_botoes_card(id_)
    mostrar_tela()

def baixar_musica(id_, alvo):
    if id_ in downloads:
        del downloads[id_]
        guardar("downloads", downloads)
        avisar("Download removido")
    else:
        musica = obter_ou_criar_musica(alvo, id_)
        if musica:
            downloads[id_] = musica
            guardar("downloads", downloads)
            nome_arquivo = f"{musica['artista']} - {musica['nome']}"
            window.baixarArquivoNoAparelho(musica["audio"], nome_arquivo)
            avisar("Música baixada com sucesso!")
    atualizar_botoes_card(id_)
    mostrar_tela()

def escolher_pasta_dispositivo():
    window.selecionarPastaDispositivo()

def remover_download(id_):
    if id_ in downloads:
        del downloads[id_]
        guardar("downloads", downloads)
        avisar("Download removido")
        mostrar_tela()

def tocar_musica_obj(musica, sem_limite=False):
    if not musica:
        return
    player.src = musica.get("audio_completo") if sem_limite else musica["audio"]
    player.play()
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
        avisar(f"Já está em “{nome}”")
        return
    ids.append(id_)
    guardar("albuns", albuns)
    avisar(f"Adicionada a “{nome}”")
    mostrar_tela()

def criar_album(evento):
    evento.preventDefault()
    nome = campo_album.value.strip()
    if not nome:
        return
    if nome in albuns:
        avisar("Já existe um álbum com esse nome")
        return
    albuns[nome] = []
    guardar("albuns", albuns)
    campo_album.value = ""
    avisar(f"Álbum “{nome}” criado")
    mostrar_tela()

def excluir_album():
    if window.confirm(f"Excluir o álbum “{album_aberto}”? As músicas continuam nos favoritos."):
        albuns.pop(album_aberto, None)
        guardar("albuns", albuns)
        avisar("Álbum excluído")
        ir_para("albuns")

def ao_enviar_busca(evento):
    evento.preventDefault()
    asyncio.ensure_future(executar_busca())

async def executar_busca():
    global resultados_atuais
    termo = campo_busca.value.strip()
    if not termo:
        status.textContent = "Digite o nome de um artista ou música."
        return

    ir_para("busca")
    grade.innerHTML = ""
    status.textContent = "Buscando músicas…"

    try:
        resultados = await buscar_musicas(termo)
    except Exception:
        status.textContent = "Erro ao buscar. Verifique sua internet e tente de novo."
        return

    musicas = [simplificar(m) for m in resultados if m.get("previewUrl")]

    if not musicas:
        status.textContent = "Não encontramos resultados."
        return

    resultados_atuais = {m["id"]: m for m in musicas}
    status.textContent = f"{len(musicas)} resultados para “{termo}”"
    grade.innerHTML = "".join(html_card(m) for m in musicas)

def aplicar_tema(tema):
    document.documentElement.setAttribute("data-theme", tema)
    guardar("tema", tema)

def alternar_tema(evento):
    atual = document.documentElement.getAttribute("data-theme")
    aplicar_tema("light" if atual == "dark" else "dark")

def atualizar_tela_local_py():
    if tela == "local":
        renderizar_local()
    atualizar_contadores()

window.atualizarTelaLocalPy = create_proxy(atualizar_tela_local_py)

def ao_clicar(evento):
    if evento.target.closest(".menu-wrap") is None:
        fechar_menu()

    alvo = evento.target.closest("[data-acao]")
    if alvo is None:
        return
    acao = alvo.getAttribute("data-acao")
    id_ = alvo.getAttribute("data-id")

    if acao == "menu":
        abrir_menu_ou_fechar()
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
    elif acao == "escolher-pasta-dispositivo":
        escolher_pasta_dispositivo()
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
    elif acao == "tocar-favorito":
        tocar_favorito(id_)
    elif acao == "tocar-download":
        tocar_download(id_)
    elif acao == "tocar-local":
        tocar_local(id_)
    elif acao == "tocar-album-index":
        index = int(alvo.getAttribute("data-index"))
        tocar_album_por_indice(index)
    elif acao == "mover-cima":
        index = int(alvo.getAttribute("data-index"))
        mover_musica_album(index, -1)
    elif acao == "mover-baixo":
        index = int(alvo.getAttribute("data-index"))
        mover_musica_album(index, 1)
    elif acao == "tocar-album-sequencial":
        tocar_album_por_indice(0)
    elif acao == "tocar-album-aleatorio":
        if album_aberto in albuns and albuns[album_aberto]:
            ids = albuns[album_aberto]
            musicas = [favoritos[i] for i in ids if i in favoritos]
            if musicas:
                escolhida = random.choice(musicas)
                tocar_musica_obj(escolhida, sem_limite=True)
                avisar("Reproduzindo música aleatória do álbum")

def ao_mudar(evento):
    alvo = evento.target
    if alvo.getAttribute("data-acao") == "add-album" and alvo.value:
        adicionar_ao_album(alvo.value, alvo.getAttribute("data-id"))

def pausar_outros(evento):
    for a in document.querySelectorAll("audio"):
        if not a.isSameNode(evento.target):
            a.pause()

def ao_teclar(evento):
    if evento.key == "Escape":
        fechar_menu()

form_busca.addEventListener("submit", create_proxy(ao_enviar_busca))
form_album.addEventListener("submit", create_proxy(criar_album))
document.addEventListener("click", create_proxy(ao_clicar))
document.addEventListener("change", create_proxy(ao_mudar))
document.addEventListener("keydown", create_proxy(ao_teclar))
document.addEventListener("play", create_proxy(pausar_outros), True)
botao_tema.addEventListener("click", create_proxy(alternar_tema))

tema_salvo = carregar("tema", None)
if tema_salvo:
    document.documentElement.setAttribute("data-theme", tema_salvo)

mostrar_tela()
    
