from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn
from google import genai
from google.genai import types

app = FastAPI(title="SaaS API - Gerador de Currículos Profissionais", version="1.0.0")

# --- Modelos Pydantic ---
class ExperienciaBruta(BaseModel):
    empresa: str
    cargo: str
    descricao_bruta: str
    periodo: str

class FormacaoAcademica(BaseModel):
    instituicao: str
    curso: str
    ano_conclusao: str

class DadosEntradaCurriculo(BaseModel):
    nome_completo: str
    email: str
    telefone: str
    linkedin: Optional[str] = None
    cargo_alvo: str
    resumo_pessoal_bruto: str
    habilidades: List[str]
    experiencias: List[ExperienciaBruta]
    formacao: List[FormacaoAcademica]

class ExperienciaReformulada(BaseModel):
    cargo: str = Field(description="Cargo ocupado")
    empresa: str = Field(description="Nome da empresa")
    periodo: str = Field(description="Período de atuação")
    conquistas: List[str] = Field(description="Lista de conquistas e responsabilidades usando verbos de ação e impacto")

class CategoriaHabilidade(BaseModel):
    categoria: str = Field(description="Ex: Técnicas, Ferramentas, Interpessoais")
    itens: List[str] = Field(description="Lista de habilidades dessa categoria")

class CurriculoProfissional(BaseModel):
    resumo_profissional_otimizado: str = Field(description="Resumo profissional otimizado e atraente para recrutadores e sistemas ATS")
    cargo_sugerido: str = Field(description="Cargo sugerido ou otimizado para o currículo")
    experiencias_reformuladas: List[ExperienciaReformulada] = Field(description="Lista de experiências profissionais reformuladas com conquistas de alto impacto")
    habilidades_organizadas: List[CategoriaHabilidade] = Field(description="Habilidades categorizadas em grupos")
    formacao_formatada: List[str] = Field(description="Lista de formações acadêmicas formatadas profissionalmente")
    dicas_para_entrevista: List[str] = Field(description="Dicas estratégicas para entrevistas focadas no cargo alvo")

# --- Rotas ---
@app.get("/")
def read_root():
    return {"status": "SaaS Online", "versao": "1.0.0"}

@app.get("/saudacao/{nome}")
def saudacao(nome: str):
    return {"mensagem": f"Olá, {nome}! Seja bem-vindo(a) ao SaaS de Currículos com IA."}

@app.post("/api/v1/curriculo/gerar", response_model=CurriculoProfissional)
def gerar_curriculo(dados: DadosEntradaCurriculo):
    try:
        client = genai.Client()

        prompt = f"""
        Você é um especialista senior em recrutamento e otimização de currículos para sistemas ATS (Applicant Tracking Systems).
        Transforme as informações brutas fornecidas em um currículo profissional de alta performance adaptado para o cargo alvo.

        DADOS DO CANDIDATO:
        - Nome: {dados.nome_completo}
        - Email: {dados.email}
        - Telefone: {dados.telefone}
        - LinkedIn: {dados.linkedin or 'Não informado'}
        - Cargo Alvo: {dados.cargo_alvo}
        - Resumo Pessoal Bruto: {dados.resumo_pessoal_bruto}
        - Habilidades Informadas: {", ".join(dados.habilidades)}

        EXPERIÊNCIAS BRUTAS:
        {[exp.model_dump() for exp in dados.experiencias]}

        FORMAÇÃO ACADÊMICA:
        {[form.model_dump() for form in dados.formacao]}

        DIRETRIZES:
        1. Crie um resumo profissional persuasivo focado no cargo alvo e indique um cargo sugerido adaptado.
        2. Reformule as experiências profissionais em conquistas usando verbos de ação marcantes.
        3. Organize e categorize as habilidades em grupos lógicos (ex: 'Técnicas', 'Ferramentas', 'Interpessoais').
        4. Formate a formação acadêmica de maneira limpa.
        5. Forneça dicas estratégicas e personalizadas de entrevista para o cargo alvo.
        """

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CurriculoProfissional,
            ),
        )

        return response.parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar currículo com IA: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
