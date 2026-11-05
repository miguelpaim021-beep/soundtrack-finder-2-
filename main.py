"""
SoundTrack Finder — lógica da aplicação
=======================================
Python rodando dentro do navegador (PyScript). Este arquivo:

  1. busca músicas na API gratuita do iTunes;
  2. mostra os resultados em cards com player de áudio;
  3. deixa o usuário SALVAR músicas em "Downloads";
  4. deixa o usuário criar "Álbuns" com as músicas salvas;
  5. guarda tudo no navegador (localStorage), então nada se perde ao recarregar.

COMO O CÓDIGO ESTÁ ORGANIZADO (de cima para baixo)
--------------------------------------------------
  1. Elementos da página     → pega do HTML os elementos que vamos usar
  2. Armazenamento           → ler/gravar no localStorage
  3. Estado da aplicação     → variáveis que guardam "o que está acontecendo"
  4. API do iTunes           → buscar_musicas() e simplificar()
  5. Montagem do HTML        → funções html_* que devolvem pedaços de tela
  6. Telas                   → renderizar_* e mostrar_tela()
  7. Ações                   → o que acontece em cada clique
  8. Eventos                 → ouvintes de clique, envio de formulário etc.
  9. Início                  → o que roda quando a página abre

MODELO DE DADOS
---------------
  Música (dict):  {"id", "nome", "artista", "capa", "audio"}
  downloads:      {id_da_musica: música}        ← músicas salvas
  albuns:         {nome_do_album: [id, id, ...]} ← só guarda os ids; os dados
                                                   da música vêm de `downloads`
"""

import asyncio
import json
from html import escape
from urllib.parse import urlencode

from pyscript import document, window
from pyodide.http import pyfetch
from pyodide.ffi import create_proxy


# =============================================================================
# 1. ELEMENTOS DA PÁGINA
# =============================================================================
API_URL = "https://itunes.apple.com/search"   # endereço da API (sem chave, grátis)
LIMITE = 12                                   # quantas músicas pedir por busca

# Topo
form_busca = document.querySelector("#search-form")
campo_busca = document.querySelector("#search-input")
botao_tema = document.querySelector("#theme-btn")
botao_menu = document.querySelector("#menu-btn")
menu_popup = document.querySelector("#menu-popup")
menu_qtd_albuns = document.querySelector("#menu-qtd-albuns")
menu_qtd_downloads = document.querySelector("#menu-qtd-downloads")

# As 4 telas. Só uma fica visível por vez (as outras recebem o atributo `hidden`).
TELAS = {
    "busca": document.querySelector("#tela-busca"),
    "downloads": document.querySelector("#tela-downloads"),
    "albuns": document.querySelector("#tela-albuns"),
    "album": document.querySelector("#tela-album"),
}
area_rolagem = document.querySelector("#scroll")

# Dentro da tela de busca
status = document.querySelector("#status")
grade = document.querySelector("#grid")

# Dentro da tela de álbuns
form_album = document.querySelector("#album-form")
campo_album = document.querySelector("#album-input")
grade_albuns = document.querySelector("#albuns-grid")
albuns_sub = document.querySelector("#albuns-sub")

# Player fixo e aviso rápido
player = document.querySelector("#player")
np_capa = document.querySelector("#np-capa")
np_nome = document.querySelector("#np-nome")
np_artista = document.querySelector("#np-artista")
toast = document.querySelector("#toast")


# =============================================================================
# 2. ARMAZENAMENTO (localStorage)
# =============================================================================
# O localStorage é uma "gavetinha" do navegador que guarda texto. Como ele só
# guarda texto, convertemos nossos dados para JSON ao gravar e de volta ao ler.

def carregar(chave, padrao):
    """Lê `chave` do localStorage e devolve o dado já convertido.

    Se a chave não existir (ou der erro), devolve `padrao`.
    """
    try:
        texto = window.localStorage.getItem(chave)
        return json.loads(texto) if texto else padrao
    except Exception:
        return padrao


def guardar(chave, valor):
    """Converte `valor` para JSON e grava no localStorage sob o nome `chave`."""
    try:
        window.localStorage.setItem(chave, json.dumps(valor))
    except Exception:
        pass  # ex.: navegador em modo privado — o app continua funcionando


# =============================================================================
# 3. ESTADO DA APLICAÇÃO
# =============================================================================
downloads = carregar("biblioteca", {})   # músicas salvas  {id: música}
albuns = carregar("albuns", {})          # álbuns          {nome: [ids]}
resultados_atuais = {}                   # músicas da ÚLTIMA busca {id: música}

tela = "busca"          # tela visível: "busca" | "downloads" | "albuns" | "album"
album_aberto = None     # nome do álbum aberto (usado só quando tela == "album")
timer_aviso = None      # guarda o temporizador do aviso rápido


# =============================================================================
# 4. API DO iTUNES
# =============================================================================
async def buscar_musicas(termo):
    """Faz o pedido à API do iTunes e devolve a lista de resultados (JSON).

    É `async` porque a internet demora: o `await` pausa SÓ esta função até a
    resposta chegar, e a página continua responsiva enquanto isso.
    """
    params = urlencode({"term": termo, "entity": "song", "limit": LIMITE})
    resposta = await pyfetch(f"{API_URL}?{params}")
    if not resposta.ok:
        raise RuntimeError(f"Erro HTTP {resposta.status}")
    dados = await resposta.json()
    return dados["results"]


def simplificar(m):
    """Reduz a música da API aos campos que usamos.

    Campos da API usados: trackId, trackName, artistName, artworkUrl100, previewUrl.
    A capa vem em 100x100; trocamos por 300x300 para ficar nítida.
    """
    capa = m.get("artworkUrl100", "").replace("100x100", "300x300")
    return {
        "id": str(m.get("trackId", m.get("previewUrl", ""))),
        "nome": m.get("trackName", "Sem título"),
        "artista": m.get("artistName", "Artista desconhecido"),
        "capa": capa,
        "audio": m.get("previewUrl", ""),   # áudio .m4a de 30 s
    }


# =============================================================================
# 5. MONTAGEM DO HTML
# =============================================================================
# Estas funções só DEVOLVEM texto HTML. Usamos `escape()` em todo texto que veio
# de fora (nome da música, nome do álbum…) para evitar que caracteres especiais
# quebrem a página.

def plural(n, singular, plural_):
    """Devolve '1 música' ou '3 músicas', conforme o número."""
    return f"{n} {singular if n == 1 else plural_}"


def html_card(m):
    """Card de uma música nos resultados da busca (capa, nome, artista, player, botão salvar)."""
    salva = m["id"] in downloads
    classe = "btn-salvar ativo" if salva else "btn-salvar"
    texto = "✓ Salva em Downloads" if salva else "⬇ Salvar em Downloads"
    return f"""
    <article class="card">
      <div class="capa"><img src="{escape(m['capa'])}" alt="Capa do álbum" loading="lazy"></div>
      <h3 title="{escape(m['nome'])}">{escape(m['nome'])}</h3>
      <p>{escape(m['artista'])}</p>
      <audio controls preload="none" src="{escape(m['audio'])}"></audio>
      <button class="{classe}" data-acao="salvar" data-id="{escape(m['id'])}">{texto}</button>
    </article>"""


def html_linha(m, modo):
    """Linha de música usada nas telas Downloads e Álbum.

    modo="download": mostra o menu "＋ Álbum" e o botão de excluir download.
    modo="album":    mostra apenas o botão de tirar a música do álbum.
    """
    id_ = escape(m["id"])

    if modo == "download":
        if albuns:
            opcoes = "".join(
                f'<option value="{escape(nome)}">{escape(nome)}</option>' for nome in albuns
            )
            extra = (
                f'<select data-acao="add-album" data-id="{id_}" title="Adicionar a um álbum">'
                f'<option value="">＋ Álbum</option>{opcoes}</select>'
            )
        else:
            # Ainda não existe nenhum álbum: leva o usuário a criar um.
            extra = '<button class="link" data-acao="ir-albuns">Criar álbum</button>'
        botao_remover = (
            f'<button class="icone pequeno" data-acao="remover-download" data-id="{id_}" '
            f'title="Excluir dos downloads">✕</button>'
        )
    else:
        extra = ""
        botao_remover = (
            f'<button class="icone pequeno" data-acao="remover-do-album" data-id="{id_}" '
            f'title="Tirar do álbum">✕</button>'
        )

    return f"""
    <li class="linha">
      <button class="play" data-acao="tocar" data-id="{id_}" title="Tocar">▶</button>
      <img src="{escape(m['capa'])}" alt="">
      <div class="info"><strong>{escape(m['nome'])}</strong><span>{escape(m['artista'])}</span></div>
      {extra}
      {botao_remover}
    </li>"""


def html_card_album(nome, ids):
    """Card de um álbum na tela de álbuns (mosaico de capas, nome e quantidade)."""
    capas = [downloads[i]["capa"] for i in ids if i in downloads]
    if len(capas) >= 4:                       # 4+ músicas: mosaico 2x2
        arte = '<div class="mosaico">' + "".join(
            f'<img src="{escape(c)}" alt="">' for c in capas[:4]
        ) + "</div>"
    elif capas:                               # 1 a 3 músicas: capa da primeira
        arte = f'<img src="{escape(capas[0])}" alt="">'
    else:                                     # álbum vazio
        arte = '<span class="arte-vazia">♫</span>'
    return f"""
    <button class="album-card" data-acao="abrir-album" data-nome="{escape(nome)}">
      <div class="album-capa">{arte}</div>
      <strong>{escape(nome)}</strong>
      <span>{plural(len(ids), 'música', 'músicas')}</span>
    </button>"""


# =============================================================================
# 6. TELAS
# =============================================================================
def renderizar_downloads():
    """Escreve a tela 'Downloads' (todas as músicas salvas)."""
    n = len(downloads)
    cabecalho = f"""
    <div class="tela-topo">
      <div><h1>Downloads</h1><p>{plural(n, 'música salva', 'músicas salvas')}</p></div>
    </div>"""
    if downloads:
        corpo = '<ul class="lista">' + "".join(
            html_linha(m, "download") for m in downloads.values()
        ) + "</ul>"
    else:
        corpo = """
        <div class="vazio">
          <div class="vazio-icone">⬇️</div>
          <h2>Nenhum download ainda</h2>
          <p>Busque uma música e toque em “Salvar em Downloads”.</p>
          <button class="primario" data-acao="ir-busca">Buscar músicas</button>
        </div>"""
    TELAS["downloads"].innerHTML = cabecalho + corpo


def renderizar_albuns():
    """Escreve a tela 'Álbuns' (grade com todos os álbuns criados)."""
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
    """Escreve a tela de UM álbum aberto (cabeçalho + músicas dele)."""
    if album_aberto not in albuns:
        return
    ids = albuns[album_aberto]
    musicas = [downloads[i] for i in ids if i in downloads]
    if musicas:
        corpo = '<ul class="lista">' + "".join(html_linha(m, "album") for m in musicas) + "</ul>"
    else:
        corpo = """
        <div class="vazio">
          <div class="vazio-icone">🎶</div>
          <h2>Álbum vazio</h2>
          <p>Vá em Downloads e use o menu “＋ Álbum” nas músicas para adicioná-las aqui.</p>
          <button class="primario" data-acao="ir-downloads">Ir para Downloads</button>
        </div>"""
    TELAS["album"].innerHTML = f"""
    <button class="voltar" data-acao="ir-albuns">← Álbuns</button>
    <div class="tela-topo">
      <div><h1>{escape(album_aberto)}</h1><p>{plural(len(musicas), 'música', 'músicas')}</p></div>
      <button class="perigo" data-acao="excluir-album">Excluir álbum</button>
    </div>
    {corpo}"""


def atualizar_contadores():
    """Atualiza os números mostrados ao lado das opções do pop-up."""
    menu_qtd_albuns.textContent = str(len(albuns))
    menu_qtd_downloads.textContent = str(len(downloads))


def mostrar_tela():
    """Mostra só a tela atual (variável `tela`) e redesenha o conteúdo dela.

    A tela de busca NÃO é redesenhada aqui, para não interromper uma música que
    esteja tocando nos cards.
    """
    for nome, secao in TELAS.items():
        secao.hidden = nome != tela
    if tela == "downloads":
        renderizar_downloads()
    elif tela == "albuns":
        renderizar_albuns()
    elif tela == "album":
        renderizar_album()
    atualizar_contadores()


def ir_para(nova_tela, album=None):
    """Navega para outra tela, fecha o pop-up e volta ao topo da página."""
    global tela, album_aberto
    tela = nova_tela
    album_aberto = album
    fechar_menu()
    mostrar_tela()
    area_rolagem.scrollTop = 0


# =============================================================================
# 7. AÇÕES
# =============================================================================
def avisar(texto):
    """Mostra uma mensagem rápida na parte de baixo da tela por 2 segundos."""
    global timer_aviso
    toast.textContent = texto
    toast.classList.add("mostra")
    if timer_aviso is not None:
        window.clearTimeout(timer_aviso)
    timer_aviso = window.setTimeout(PROXY_ESCONDER_AVISO, 2000)


def esconder_aviso():
    """Esconde o aviso rápido (chamada pelo temporizador de `avisar`)."""
    toast.classList.remove("mostra")


PROXY_ESCONDER_AVISO = create_proxy(esconder_aviso)


def abrir_menu_ou_fechar():
    """Abre o pop-up se estiver fechado; fecha se estiver aberto."""
    abrindo = menu_popup.hidden
    menu_popup.hidden = not abrindo
    botao_menu.setAttribute("aria-expanded", "true" if abrindo else "false")


def fechar_menu():
    """Fecha o pop-up de opções."""
    menu_popup.hidden = True
    botao_menu.setAttribute("aria-expanded", "false")


def atualizar_botao_card(id_):
    """Atualiza SÓ o botão 'Salvar' do card (sem refazer a grade, para não parar o áudio)."""
    botao = document.querySelector(f'[data-acao="salvar"][data-id="{id_}"]')
    if botao is None:
        return
    if id_ in downloads:
        botao.className = "btn-salvar ativo"
        botao.textContent = "✓ Salva em Downloads"
    else:
        botao.className = "btn-salvar"
        botao.textContent = "⬇ Salvar em Downloads"


def salvar_ou_remover_download(id_):
    """Se a música já está em Downloads, remove; se não está, salva.

    Ao remover, ela também sai de todos os álbuns.
    """
    if id_ in downloads:
        del downloads[id_]
        for ids in albuns.values():
            if id_ in ids:
                ids.remove(id_)
        avisar("Removida dos downloads")
    elif id_ in resultados_atuais:
        downloads[id_] = resultados_atuais[id_]
        avisar("Salva em Downloads")
    guardar("biblioteca", downloads)
    guardar("albuns", albuns)
    atualizar_botao_card(id_)
    mostrar_tela()


def tocar(id_):
    """Toca a prévia de uma música salva no player fixo e atualiza o 'tocando agora'."""
    musica = downloads.get(id_)
    if musica is None:
        return
    player.src = musica["audio"]
    player.play()
    np_capa.innerHTML = f'<img src="{escape(musica["capa"])}" alt="">'
    np_nome.textContent = musica["nome"]
    np_artista.textContent = musica["artista"]


def adicionar_ao_album(nome, id_):
    """Coloca a música (pelo id) dentro do álbum `nome`, sem repetir."""
    ids = albuns.setdefault(nome, [])
    if id_ in ids:
        avisar(f"Já está em “{nome}”")
        return
    ids.append(id_)
    guardar("albuns", albuns)
    avisar(f"Adicionada a “{nome}”")
    mostrar_tela()


def criar_album(evento):
    """Cria um álbum novo com o nome digitado no formulário da tela Álbuns."""
    evento.preventDefault()               # impede o formulário de recarregar a página
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
    """Exclui o álbum aberto (pede confirmação). As músicas continuam em Downloads."""
    if window.confirm(f"Excluir o álbum “{album_aberto}”? As músicas continuam em Downloads."):
        albuns.pop(album_aberto, None)
        guardar("albuns", albuns)
        avisar("Álbum excluído")
        ir_para("albuns")


# ---------- Busca ----------
def ao_enviar_busca(evento):
    """Disparada ao enviar o formulário de busca (Enter ou botão).

    Precisa ser uma função NORMAL: o preventDefault tem que rodar na hora, antes
    de o navegador recarregar a página. A busca em si (async) é agendada depois.
    """
    evento.preventDefault()
    asyncio.ensure_future(executar_busca())


async def executar_busca():
    """Lê o termo, chama a API e desenha os cards (ou uma mensagem de estado)."""
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

    # Só mantém músicas que têm prévia de áudio
    musicas = [simplificar(m) for m in resultados if m.get("previewUrl")]

    if not musicas:
        status.textContent = "Não encontramos resultados."
        return

    resultados_atuais = {m["id"]: m for m in musicas}
    status.textContent = f"{len(musicas)} resultados para “{termo}”"
    grade.innerHTML = "".join(html_card(m) for m in musicas)


# ---------- Tema ----------
def aplicar_tema(tema):
    """Troca o tema ("dark" ou "light") e lembra a escolha."""
    document.documentElement.setAttribute("data-theme", tema)
    guardar("tema", tema)


def alternar_tema(evento):
    """Alterna entre escuro e claro ao clicar no botão 🌓."""
    atual = document.documentElement.getAttribute("data-theme")
    aplicar_tema("light" if atual == "dark" else "dark")


# =============================================================================
# 8. EVENTOS
# =============================================================================
def ao_clicar(evento):
    """Ouvinte ÚNICO de cliques da página inteira ("delegação de eventos").

    Em vez de ligar um ouvinte em cada botão (que seriam recriados a cada
    desenho de tela), escutamos o documento todo e olhamos o atributo
    data-acao do elemento clicado.

      data-acao       o que faz
      --------------  ---------------------------------------------
      menu            abre/fecha o pop-up ☰
      ir-albuns       vai para a tela Álbuns
      ir-downloads    vai para a tela Downloads
      ir-busca        vai para a tela de busca
      abrir-album     abre um álbum (nome em data-nome)
      excluir-album   exclui o álbum aberto
      salvar          salva/remove a música do card em Downloads
      remover-download exclui a música dos Downloads
      remover-do-album tira a música do álbum aberto
      tocar           toca a música no player fixo (id em data-id)
    """
    # Clique fora do pop-up fecha o pop-up
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
    elif acao == "ir-downloads":
        ir_para("downloads")
    elif acao == "ir-busca":
        ir_para("busca")
    elif acao == "abrir-album":
        ir_para("album", alvo.getAttribute("data-nome"))
    elif acao == "excluir-album":
        excluir_album()
    elif acao in ("salvar", "remover-download"):
        salvar_ou_remover_download(id_)
    elif acao == "remover-do-album":
        if id_ in albuns.get(album_aberto, []):
            albuns[album_aberto].remove(id_)
            guardar("albuns", albuns)
            mostrar_tela()
    elif acao == "tocar":
        tocar(id_)


def ao_mudar(evento):
    """Ouvinte de mudanças: trata o menu '＋ Álbum' das músicas em Downloads."""
    alvo = evento.target
    if alvo.getAttribute("data-acao") == "add-album" and alvo.value:
        adicionar_ao_album(alvo.value, alvo.getAttribute("data-id"))


def pausar_outros(evento):
    """Garante UM áudio por vez: quando um começa, pausa todos os outros."""
    for a in document.querySelectorAll("audio"):
        if not a.isSameNode(evento.target):
            a.pause()


def ao_teclar(evento):
    """Tecla Esc fecha o pop-up."""
    if evento.key == "Escape":
        fechar_menu()


# Ligando os ouvintes aos eventos. `create_proxy` permite que o JavaScript do
# navegador chame nossas funções Python.
form_busca.addEventListener("submit", create_proxy(ao_enviar_busca))
form_album.addEventListener("submit", create_proxy(criar_album))
document.addEventListener("click", create_proxy(ao_clicar))
document.addEventListener("change", create_proxy(ao_mudar))
document.addEventListener("keydown", create_proxy(ao_teclar))
# O evento 'play' não "borbulha" até o documento, então usamos a fase de
# captura (o True no final) para ouvi-lo.
document.addEventListener("play", create_proxy(pausar_outros), True)
botao_tema.addEventListener("click", create_proxy(alternar_tema))


# =============================================================================
# 9. INÍCIO
# =============================================================================
tema_salvo = carregar("tema", None)
if tema_salvo:
    document.documentElement.setAttribute("data-theme", tema_salvo)

mostrar_tela()   # desenha a tela inicial (busca) e os contadores do menu
