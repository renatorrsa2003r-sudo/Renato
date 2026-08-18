import os
import subprocess
import time
import threading
from pathlib import Path
from typing import List
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# --- Schemas para a IA ---
class FileChange(BaseModel):
    filepath: str = Field(description="Nome do arquivo relativo a pasta do projeto")
    content: str = Field(description="Conteudo completo do arquivo")

class AgentResponse(BaseModel):
    summary: str = Field(description="Resumo do que foi implementado")
    commit_message: str = Field(description="Mensagem de commit")
    files: List[FileChange] = Field(description="Lista de arquivos modificados ou criados")

IGNORE_DIRS = {".git", "__pycache__", "venv", ".venv", "node_modules", ".idea", ".vscode", "dist", "build"}
IGNORE_EXTS = {".png", ".jpg", ".jpeg", ".pdf", ".zip", ".exe", ".env", ".pyc"}

# --- Logica do Agente ---
def coletar_contexto(diretorio_base: Path) -> str:
    contexto = []
    for root, dirs, files in os.walk(diretorio_base):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            path_arquivo = Path(root) / file
            if path_arquivo.suffix in IGNORE_EXTS or file.startswith("."):
                continue
            caminho_relativo = path_arquivo.relative_to(diretorio_base)
            conteudo = ""
            for enc in ("utf-8", "utf-8-sig", "latin-1", "utf-16"):
                try:
                    with open(path_arquivo, "r", encoding=enc) as f:
                        conteudo = f.read()
                    break
                except Exception:
                    continue
            if conteudo:
                contexto.append(f"=== ARQUIVO: {caminho_relativo} ===\n{conteudo}\n")
    return "\n".join(contexto)

def gravar_arquivos(diretorio_base: Path, files: List[FileChange], log_func):
    for item in files:
        caminho_arquivo = diretorio_base / item.filepath
        caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write(item.content)
        log_func(f"  [+] Arquivo atualizado: {item.filepath}")

def sincronizar_git(diretorio_base: Path, commit_msg: str, log_func):
    log_func("\n4. Sincronizando com o Git e GitHub...")
    try:
        subprocess.run(["git", "add", "."], cwd=diretorio_base, check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=diretorio_base, check=True)
        log_func("  [+] Commit criado com sucesso no repositorio local.")
        
        resultado_push = subprocess.run(["git", "push"], cwd=diretorio_base, capture_output=True, text=True)
        if resultado_push.returncode == 0:
            log_func("  [+] Codigo enviado para o GitHub com sucesso (git push concluido)!")
        else:
            log_func(f"  [!] Aviso no Push: {resultado_push.stderr.strip() or 'Repositorio remoto pendente'}")
    except subprocess.CalledProcessError as e:
        log_func(f"  [!] Erro na execucao do Git: {e}")

# --- Interface Grafica ---
class SaaSBuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Assistente SaaS AI")
        self.root.geometry("750x650")
        self.root.minsize(650, 550)

        self.style = ttk.Style()
        self.style.theme_use("clam")

        main_frame = ttk.Frame(root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Selecao de Pasta
        lbl_pasta = ttk.Label(main_frame, text="Pasta do Projeto SaaS:", font=("Segoe UI", 10, "bold"))
        lbl_pasta.pack(anchor=tk.W, pady=(0, 2))

        pasta_frame = ttk.Frame(main_frame)
        pasta_frame.pack(fill=tk.X, pady=(0, 10))

        self.txt_pasta = ttk.Entry(pasta_frame, font=("Segoe UI", 10))
        self.txt_pasta.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.txt_pasta.insert(0, os.getcwd())

        btn_procurar = ttk.Button(pasta_frame, text="Selecionar Pasta...", command=self.selecionar_pasta)
        btn_procurar.pack(side=tk.RIGHT)

        # 2. Instrucao / Pedido
        lbl_pedido = ttk.Label(main_frame, text="O que deseja adicionar ou modificar?", font=("Segoe UI", 10, "bold"))
        lbl_pedido.pack(anchor=tk.W, pady=(0, 2))

        self.txt_pedido = tk.Text(main_frame, height=4, font=("Segoe UI", 10), wrap=tk.WORD)
        self.txt_pedido.pack(fill=tk.X, pady=(0, 10))

        # 3. Botao de Acao
        self.btn_executar = tk.Button(
            main_frame,
            text="Executar e Enviar ao GitHub",
            font=("Segoe UI", 11, "bold"),
            bg="#0066cc",
            fg="white",
            activebackground="#004d99",
            activeforeground="white",
            relief=tk.FLAT,
            pady=8,
            command=self.iniciar_processamento
        )
        self.btn_executar.pack(fill=tk.X, pady=(0, 15))

        # 4. Painel de Logs
        lbl_log = ttk.Label(main_frame, text="Historico de Execucao:", font=("Segoe UI", 10, "bold"))
        lbl_log.pack(anchor=tk.W, pady=(0, 2))

        self.log_area = scrolledtext.ScrolledText(main_frame, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4", wrap=tk.WORD)
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta do seu SaaS")
        if pasta:
            self.txt_pasta.delete(0, tk.END)
            self.txt_pasta.insert(0, pasta)

    def log(self, mensagem):
        self.log_area.insert(tk.END, mensagem + "\n")
        self.log_area.see(tk.END)

    def iniciar_processamento(self):
        pasta = self.txt_pasta.get().strip()
        pedido = self.txt_pedido.get("1.0", tk.END).strip()

        if not pasta or not os.path.exists(pasta):
            messagebox.showerror("Erro", "Por favor, selecione uma pasta valida para o projeto.")
            return

        if not pedido:
            messagebox.showwarning("Aviso", "Por favor, digite o que deseja adicionar ou modificar.")
            return

        self.btn_executar.config(state=tk.DISABLED, bg="#888888", text="Processando...")
        self.log_area.delete("1.0", tk.END)

        threading.Thread(target=self.executar_tarefa, args=(pasta, pedido), daemon=True).start()

    def executar_tarefa(self, pasta: str, pedido: str):
        base_path = Path(pasta).resolve()

        try:
            self.log("1. Lendo base de codigo atual do projeto...")
            contexto = coletar_contexto(base_path)

            prompt = f"""
            Voce e um desenvolvedor de software senior.
            
            CODIGO ATUAL DO PROJETO:
            {contexto}
            
            SOLICITACAO:
            {pedido}
            
            INSTRUCOES:
            - Retorne os arquivos completos necessarios para implementar o pedido.
            - Se modificar arquivos existentes, retorne o codigo completo atualizado deles.
            """

            self.log("2. Enviando solicitacao para a API do Gemini...")
            client = genai.Client()

            max_tentativas = 3
            resultado = None

            for tentativa in range(1, max_tentativas + 1):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=AgentResponse,
                        ),
                    )
                    resultado = response.parsed
                    break
                except Exception as e:
                    if tentativa < max_tentativas:
                        self.log(f"  [!] Servidor ocupado. Aguardando 3s ({tentativa}/{max_tentativas})...")
                        time.sleep(3)
                    else:
                        raise e

            self.log(f"\nResumo: {resultado.summary}")
            self.log(f"Commit: {resultado.commit_message}\n")

            self.log("3. Gravando alteracoes no computador...")
            gravar_arquivos(base_path, resultado.files, self.log)

            sincronizar_git(base_path, resultado.commit_message, self.log)
            self.log("\nProcesso concluido com sucesso!")
            messagebox.showinfo("Sucesso", "Alteracoes aplicadas e sincronizadas com sucesso!")

        except Exception as err:
            self.log(f"\n[ERRO CRITICO]: {err}")
            messagebox.showerror("Erro na Execucao", f"Ocorreu um erro: {err}")

        finally:
            self.btn_executar.config(state=tk.NORMAL, bg="#0066cc", text="Executar e Enviar ao GitHub")

if __name__ == "__main__":
    root = tk.Tk()
    app = SaaSBuilderApp(root)
    root.mainloop()