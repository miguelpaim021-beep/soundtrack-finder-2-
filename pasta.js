/*
  SoundTrack Finder — ACESSO À PASTA DE DOWNLOADS
  ------------------------------------------------
  O Python (PyScript) chama estas funções por window.pastaDownloads.

  Como funciona:
    • Chrome/Edge (PC) e Chrome recente (Android): showDirectoryPicker().
      A pasta escolhida fica lembrada (IndexedDB). Na próxima visita basta
      clicar em "Permitir acesso" — o navegador exige esse clique por segurança.
      Com esse modo o site também consegue GRAVAR arquivos na pasta.
    • Outros navegadores (Firefox, Safari/iPhone): usa um seletor de arquivos
      comum. Só lê, e precisa ser escolhido de novo a cada visita.
*/
(function () {
  const EXT = /\.(mp3|m4a|aac|wav|flac|ogg|opus|wma)$/i;
  let dirHandle = null;     // pasta (modo moderno)
  let arquivosSolto = [];   // arquivos (modo alternativo)
  let urls = [];            // endereços temporários criados, para liberar depois

  // ---------- IndexedDB simples (guarda a pasta escolhida) ----------
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

  async function temPermissao() {
    return !!dirHandle &&
      (await dirHandle.queryPermission({ mode: "readwrite" })) === "granted";
  }

  async function percorrer(pasta, nivel, saida) {
    for await (const item of pasta.values()) {
      if (item.kind === "file" && EXT.test(item.name)) {
        const arq = await item.getFile();
        const url = URL.createObjectURL(arq);
        urls.push(url);
        saida.push({ nome: item.name.replace(EXT, ""), url });
      } else if (item.kind === "directory" && nivel < 3) {
        await percorrer(item, nivel + 1, saida);
      }
    }
  }

  window.pastaDownloads = {
    // true se o navegador sabe abrir pastas de verdade
    suporte() { return "showDirectoryPicker" in window; },

    // Tenta lembrar a pasta da visita anterior: "nenhuma" | "pedir" | "ok"
    async restaurar() {
      if (!this.suporte()) return "nenhuma";
      try {
        const h = await ler("pasta");
        if (!h) return "nenhuma";
        dirHandle = h;
        return (await temPermissao()) ? "ok" : "pedir";
      } catch (e) { return "nenhuma"; }
    },

    // Precisa ser chamada a partir de um clique. Devolve o nome da pasta ("" = cancelou).
    async escolher() {
      if (this.suporte()) {
        try {
          dirHandle = await showDirectoryPicker({ mode: "readwrite" });
          await gravar("pasta", dirHandle);
          return dirHandle.name;
        } catch (e) { return ""; }   // usuário cancelou
      }
      // Alternativa: seletor de arquivos comum
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

    // Chamada a partir de um clique: pede ao navegador acesso à pasta lembrada.
    async permitir() {
      if (!dirHandle) return false;
      try {
        return (await dirHandle.requestPermission({ mode: "readwrite" })) === "granted";
      } catch (e) { return false; }
    },

    nome() { return dirHandle ? dirHandle.name : (arquivosSolto.length ? "Arquivos selecionados" : ""); },

    // Devolve (em JSON) a lista [{nome, url}] de áudios encontrados.
    async listar() {
      urls.forEach((u) => URL.revokeObjectURL(u));
      urls = [];
      const saida = [];
      if (dirHandle && (await temPermissao())) {
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

    // Baixa `url` e grava como `nome` na pasta (ou, sem pasta, usa o download do navegador).
    // Devolve "pasta" ou "download".
    async salvar(nome, url) {
      const r = await fetch(url);
      if (!r.ok) throw new Error("HTTP " + r.status);
      const blob = await r.blob();
      if (await temPermissao()) {
        const fh = await dirHandle.getFileHandle(nome, { create: true });
        const w = await fh.createWritable();
        await w.write(blob);
        await w.close();
        return "pasta";
      }
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
})();
