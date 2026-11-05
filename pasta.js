/*
  SoundTrack Finder — ACESSO À PASTA DE DOWNLOADS (pasta.js)
  ==========================================================
  Este arquivo é a "ponte" entre o site e o sistema de arquivos do dispositivo.
  O Python (main.py) chama as funções daqui por `window.pastaDownloads`.

  COMO A PASTA É CRIADA
  ---------------------
  Por segurança, nenhum site pode criar uma pasta num lugar qualquer do seu
  computador sem você autorizar. Por isso o fluxo é:

    1. Você escolhe um LOCAL (ex.: dentro de "Músicas") — uma única vez.
    2. O site cria automaticamente, dentro dele, a pasta "SoundTrack Downloads".
    3. Essa pasta passa a ser a ÚNICA usada: o botão ⬇ grava nela e a aba
       Downloads lê dela. Assim as duas coisas sempre apontam para o mesmo lugar.

  Se a pasta for apagada depois, ela é recriada no mesmo local ao baixar de novo.
  Se o botão ⬇ for usado sem nenhuma pasta escolhida, o navegador pergunta o
  local na hora (e cria a pasta) antes de baixar.

  COMPATIBILIDADE
  ---------------
    • Chrome/Edge no PC (e Chrome recente no Android): fluxo completo acima,
      com a pasta lembrada entre visitas (guardada no IndexedDB).
    • Firefox / Safari / iPhone: o navegador NÃO permite criar nem gravar em
      pastas. Nesse caso (a) o ⬇ usa o download normal do navegador, que cai na
      pasta de Downloads padrão dele, e (b) a aba Downloads usa um seletor de
      arquivos comum (só leitura, precisa ser refeito a cada visita).
    • Dica: o Chrome recusa algumas pastas "de sistema" (a própria pasta
      Downloads, Documentos, Área de Trabalho). Se recusar, escolha ou crie
      uma subpasta (ex.: "Músicas/Meus sons") e selecione essa.

  FUNÇÕES EXPOSTAS (window.pastaDownloads)
  ----------------------------------------
    NOME_PASTA        texto: nome da pasta que o site cria
    suporte()         true se o navegador sabe abrir/criar pastas de verdade
    restaurar()       reencontra a pasta da visita anterior → "nenhuma"|"pedir"|"ok"
    escolher()        abre o seletor, cria a pasta → nome da pasta ("" = cancelou)
    permitir()        pede ao navegador permissão para voltar a usar a pasta
    nome()            nome da pasta atual
    listar()          lê os áudios da pasta → JSON [{nome, url}]
    salvar(nome,url)  baixa `url` e grava na pasta → "pasta"|"download"|"cancelado"
*/
(function () {
  "use strict";

  const NOME_PASTA = "SoundTrack Downloads";

  // Extensões de áudio que a aba Downloads reconhece.
  const EXT = /\.(mp3|m4a|aac|wav|flac|ogg|opus|wma)$/i;

  // ---------- Estado interno ----------
  let paiHandle = null;      // pasta ESCOLHIDA pelo usuário (onde criamos a nossa)
  let dirHandle = null;      // pasta "SoundTrack Downloads" (a que realmente usamos)
  let arquivosSolto = [];    // arquivos escolhidos no modo alternativo (sem pasta)
  let urls = [];             // endereços temporários criados (liberados a cada listar)

  const temSuporte = () => "showDirectoryPicker" in window;

  // ==========================================================================
  // IndexedDB — guarda as "alças" das pastas entre visitas.
  // (localStorage só guarda texto; alças de pasta só cabem no IndexedDB.)
  // ==========================================================================
  function abrirBD() {
    return new Promise((ok, erro) => {
      const r = indexedDB.open("soundtrack", 1);
      r.onupgradeneeded = () => r.result.createObjectStore("kv");
      r.onsuccess = () => ok(r.result);
      r.onerror = () => erro(r.error);
    });
  }
  async function gravar(chave, valor) {
    const bd = await abrirBD();
    return new Promise((ok, erro) => {
      const t = bd.transaction("kv", "readwrite");
      t.objectStore("kv").put(valor, chave);
      t.oncomplete = ok;
      t.onerror = () => erro(t.error);
    });
  }
  async function ler(chave) {
    const bd = await abrirBD();
    return new Promise((ok, erro) => {
      const q = bd.transaction("kv").objectStore("kv").get(chave);
      q.onsuccess = () => ok(q.result);
      q.onerror = () => erro(q.error);
    });
  }

  // ==========================================================================
  // Permissões e verificação da pasta
  // ==========================================================================

  // O navegador já nos deu acesso de leitura+escrita a esta pasta nesta visita?
  async function temPermissao(h) {
    return !!h && (await h.queryPermission({ mode: "readwrite" })) === "granted";
  }

  // Pede a permissão (só funciona logo após um clique do usuário).
  async function pedirPermissao(h) {
    try {
      return !!h && (await h.requestPermission({ mode: "readwrite" })) === "granted";
    } catch (e) { return false; }
  }

  // A pasta ainda existe no disco? (o usuário pode tê-la apagado)
  async function pastaExiste() {
    try { await dirHandle.values().next(); return true; }
    catch (e) { return e.name !== "NotFoundError"; }
  }

  // Recria "SoundTrack Downloads" dentro da pasta que o usuário escolheu antes.
  async function recriar() {
    if (!paiHandle) return false;
    if (!(await temPermissao(paiHandle)) && !(await pedirPermissao(paiHandle))) return false;
    try {
      dirHandle = await paiHandle.getDirectoryHandle(NOME_PASTA, { create: true });
      await gravar("pasta", dirHandle);
      return true;
    } catch (e) { return false; }
  }

  // Garante uma pasta pronta para GRAVAR. Devolve:
  //   "ok"          pasta pronta
  //   "cancelado"   o usuário fechou o seletor / negou a permissão
  //   "sem-suporte" o navegador não consegue usar pastas
  async function garantir() {
    if (!temSuporte()) return "sem-suporte";

    if (dirHandle) {
      if (!(await temPermissao(dirHandle)) && !(await pedirPermissao(dirHandle))) return "cancelado";
      if (await pastaExiste()) return "ok";
      if (await recriar()) return "ok";     // foi apagada: recria no mesmo local
      dirHandle = null;                      // não deu: pede um local novo abaixo
    }
    const nome = await api.escolher();       // abre o seletor e cria a pasta
    return nome ? "ok" : "cancelado";
  }

  // Percorre a pasta (até 3 níveis de subpastas) coletando os arquivos de áudio.
  async function percorrer(pasta, nivel, saida) {
    for await (const item of pasta.values()) {
      if (item.kind === "file" && EXT.test(item.name)) {
        const arq = await item.getFile();
        const url = URL.createObjectURL(arq);   // endereço temporário p/ tocar no <audio>
        urls.push(url);
        saida.push({ nome: item.name.replace(EXT, ""), url });
      } else if (item.kind === "directory" && nivel < 3) {
        await percorrer(item, nivel + 1, saida);
      }
    }
  }

  // ==========================================================================
  // API pública
  // ==========================================================================
  const api = {
    NOME_PASTA,

    suporte: temSuporte,

    /** Reencontra a pasta usada antes. "nenhuma" | "pedir" (falta o clique) | "ok". */
    async restaurar() {
      if (!temSuporte()) return "nenhuma";
      try {
        const pasta = await ler("pasta");
        if (!pasta) return "nenhuma";
        dirHandle = pasta;
        paiHandle = (await ler("pai")) || null;
        return (await temPermissao(dirHandle)) ? "ok" : "pedir";
      } catch (e) { return "nenhuma"; }
    },

    /**
     * Precisa ser chamada a partir de um clique.
     * PC/Chrome: abre o seletor de LOCAL, cria "SoundTrack Downloads" nele e a
     * guarda. Devolve o nome da pasta, ou "" se o usuário cancelou.
     * Lança erro se o navegador recusar a pasta escolhida.
     */
    async escolher() {
      if (temSuporte()) {
        let pai;
        try {
          pai = await showDirectoryPicker({ id: "soundtrack", mode: "readwrite", startIn: "music" });
        } catch (e) {
          if (e.name === "AbortError") return "";   // cancelou
          throw e;                                   // recusou (pasta de sistema etc.)
        }
        paiHandle = pai;
        // Se o usuário já escolheu a própria pasta "SoundTrack Downloads", usa ela direto.
        dirHandle = pai.name === NOME_PASTA
          ? pai
          : await pai.getDirectoryHandle(NOME_PASTA, { create: true });   // CRIA a pasta
        await gravar("pai", paiHandle);
        await gravar("pasta", dirHandle);
        return dirHandle.name;
      }

      // Navegador sem suporte: seletor de arquivos comum (só leitura).
      return new Promise((ok) => {
        const inp = document.createElement("input");
        inp.type = "file";
        inp.multiple = true;
        inp.accept = "audio/*";
        inp.setAttribute("webkitdirectory", "");
        inp.onchange = () => {
          arquivosSolto = Array.from(inp.files).filter((f) => EXT.test(f.name));
          ok(arquivosSolto.length ? "Arquivos selecionados" : "");
        };
        inp.oncancel = () => ok("");
        inp.click();
      });
    },

    /** (Clique) Pede permissão para voltar a usar a pasta lembrada; recria se foi apagada. */
    async permitir() {
      if (!dirHandle) return false;
      if (!(await temPermissao(dirHandle)) && !(await pedirPermissao(dirHandle))) return false;
      if (await pastaExiste()) return true;
      return recriar();
    },

    nome() {
      return dirHandle ? dirHandle.name : (arquivosSolto.length ? "Arquivos selecionados" : "");
    },

    /** Lê os áudios da pasta. Devolve JSON: [{nome, url}], em ordem alfabética. */
    async listar() {
      urls.forEach((u) => URL.revokeObjectURL(u));   // libera os endereços antigos
      urls = [];
      const saida = [];
      if (dirHandle && (await temPermissao(dirHandle))) {
        await percorrer(dirHandle, 0, saida);
      } else {
        for (const f of arquivosSolto) {
          const url = URL.createObjectURL(f);
          urls.push(url);
          saida.push({ nome: f.name.replace(EXT, ""), url });
        }
      }
      saida.sort((a, b) => a.nome.localeCompare(b.nome));
      return JSON.stringify(saida);
    },

    /**
     * Baixa `url` e grava como `nome` DENTRO da pasta "SoundTrack Downloads"
     * (criando-a antes, se for preciso). Devolve:
     *   "pasta"      gravou na pasta
     *   "download"   navegador sem suporte: usou o download normal dele
     *   "cancelado"  o usuário não escolheu/permitiu a pasta
     * Lança erro se a rede ou o servidor de áudio recusar o pedido.
     */
    async salvar(nome, url) {
      const estado = await garantir();          // 1º a pasta (precisa do clique), depois o arquivo
      if (estado === "cancelado") return "cancelado";

      const r = await fetch(url);
      if (!r.ok) throw new Error("HTTP " + r.status);
      const blob = await r.blob();

      if (estado === "ok") {
        const fh = await dirHandle.getFileHandle(nome, { create: true });
        const w = await fh.createWritable();
        await w.write(blob);
        await w.close();
        return "pasta";
      }

      // "sem-suporte": dispara o download comum do navegador.
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = nome;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 10000);
      return "download";
    },
  };

  window.pastaDownloads = api;
})();
