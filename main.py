from urllib.parse import urlencode

from pyscript import document, window
from pyodide.http import pyfetch
from pyodide.ffi import create_proxy

API_URL = "https://itunes.apple.com/search"
LIMITE = 12

form = document.querySelector("#search-form")
campo = document.querySelector("#search-input")
status = document.querySelector("#status")
grade = document.querySelector("#grid")
botao_tema = document.querySelector("#theme-btn")


# ---------- Chamada à API ----------
async def buscar_musicas(termo):
    """Faz o pedido à API do iTunes e devolve a lista de resultados.

    `await` pausa ESTA função até a resposta chegar, sem travar a página.
    """
    params = urlencode({"term": termo, "entity": "song", "limit": LIMITE})
    resposta = await pyfetch(f"{API_URL}?{params}")
    if not resposta.ok:
        raise RuntimeError(f"Erro HTTP {resposta.status}")
    dados = await resposta.json()
    return dados["results"]


# ---------- Montagem dos cards ----------
def criar_card(musica):
    card = document.createElement("article")
    card.className = "card"

    capa = document.createElement("img")
    capa.src = musica.get("artworkUrl100", "")
    capa.alt = "Capa do álbum"

    titulo = document.createElement("h3")
    titulo.textContent = musica.get("trackName", "Sem título")

    artista = document.createElement("p")
    artista.textContent = musica.get("artistName", "Artista desconhecido")

    # O player sabe qual música tocar pelo atributo src = previewUrl
    audio = document.createElement("audio")
    audio.controls = True
    audio.preload = "none"
    audio.src = musica.get("previewUrl", "")

    for item in (capa, titulo, artista, audio):
        card.appendChild(item)
    return card


def pausar_outros(evento):
    """Quando um áudio começa a tocar, pausa todos os outros."""
    for a in grade.querySelectorAll("audio"):
        if not a.isSameNode(evento.target):
            a.pause()


# 'play' não "borbulha", então escutamos na fase de captura (True)
grade.addEventListener("play", create_proxy(pausar_outros), True)


# ---------- Fluxo principal ----------
async def ao_buscar(evento):
    evento.preventDefault()  # impede o form de recarregar a página
    termo = campo.value.strip()
    if not termo:
        status.textContent = "Digite o nome de um artista ou música."
        return

    grade.innerHTML = ""
    status.textContent = "Buscando músicas…"

    try:
        resultados = await buscar_musicas(termo)
    except Exception:
        status.textContent = "Erro ao buscar. Verifique sua internet e tente de novo."
        return

    # Só mantém músicas que têm prévia de áudio
    resultados = [m for m in resultados if m.get("previewUrl")]

    if not resultados:
        status.textContent = "Não encontramos resultados."
        return

    status.textContent = f"{len(resultados)} resultados para “{termo}”"
    for musica in resultados:
        grade.appendChild(criar_card(musica))


form.addEventListener("submit", create_proxy(ao_buscar))


# ---------- Modo escuro / claro ----------
def aplicar_tema(tema):
    document.documentElement.setAttribute("data-theme", tema)
    try:
        window.localStorage.setItem("tema", tema)
    except Exception:
        pass


def alternar_tema(evento):
    atual = document.documentElement.getAttribute("data-theme")
    aplicar_tema("light" if atual == "dark" else "dark")


try:
    salvo = window.localStorage.getItem("tema")
    if salvo:
        aplicar_tema(salvo)
except Exception:
    pass

botao_tema.addEventListener("click", create_proxy(alternar_tema))
