import os
import subprocess
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class FileChange(BaseModel):
    filepath: str = Field(description="Nome do arquivo relativo à pasta do projeto (ex: 'main.py' ou 'api/routes.py')")
    content: str = Field(description="Código completo do arquivo atualizado ou criado")

class AgentResponse(BaseModel):
    summary: str = Field(description="Resumo do que foi implementado")
    commit_message: str = Field(description="Mensagem semântica de commit (ex: 'feat: adiciona rota de pdf')")
    files: List[FileChange] = Field(description="Lista de arquivos modificados ou criados")

IGNORE_DIRS = {".git", "__pycache__", "venv", ".venv", "node_modules", ".idea", ".vscode", "dist", "build"}
IGNORE_EXTS = {".png", ".jpg", ".jpeg", ".pdf", ".zip", ".exe", ".env", ".pyc"}

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

def gravar_arquivos(diretorio_base: Path, files: List[FileChange]):
    for item in files:
        caminho_arquivo = diretorio_base / item.filepath
        caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write(item.content)
        print(f"  [✓] Arquivo atualizado: {item.filepath}")

def sincronizar_git(diretorio_base: Path, commit_msg: str):
    print("\n4. Sincronizando com o Git...")
    try:
        subprocess.run(["git", "add", "."], cwd=diretorio_base, check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=diretorio_base, check=True)
        print("  [✓] Commit criado com sucesso no repositório local.")
        
        resultado_push = subprocess.run(["git", "push"], cwd=diretorio_base, capture_output=True, text=True)
        if resultado_push.returncode == 0:
            print("  [✓] Código enviado para o GitHub remoto (git push concluído).")
        else:
            print("  [i] Alterações salvas localmente no Git (push pendente de repositório remoto configurado).")
    except subprocess.CalledProcessError as e:
        print(f"  [!] Erro na execução do Git: {e}")

def executar_assistente():
    pasta = input("Caminho da pasta do seu projeto: ").strip()
    pedido = input("O que deseja adicionar/modificar? ").strip()
    
    base_path = Path(pasta).resolve()
    if not base_path.exists():
        print("Erro: Pasta não encontrada.")
        return

    print("\n1. Lendo base de código atual...")
    contexto = coletar_contexto(base_path)

    prompt = f"""
    Você é um desenvolvedor de software sênior.
    
    CÓDIGO ATUAL DO PROJETO:
    {contexto}
    
    SOLICITAÇÃO:
    {pedido}
    
    INSTRUÇÕES:
    - Retorne os arquivos completos necessários para implementar o pedido.
    - Se modificar arquivos existentes, retorne o código completo atualizado deles.
    """

    print("2. Gerando nova funcionalidade com IA...")
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AgentResponse,
        ),
    )

    resultado: AgentResponse = response.parsed

    print(f"\nResumo: {resultado.summary}")
    print(f"Commit: {resultado.commit_message}")

    print("\n3. Gravando alterações no computador...")
    gravar_arquivos(base_path, resultado.files)

    sincronizar_git(base_path, resultado.commit_message)
    print("\n✓ Processo finalizado com sucesso!")

if __name__ == "__main__":
    executar_assistente()