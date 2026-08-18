from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn
from google import genai
from google.genai import types

app = FastAPI(title="SaaS API - Receitas Naturais Inteligentes e Econômicas", version="1.0.0")

# --- Modelos Pydantic ---
class IngredienteItem(BaseModel):
    nome: str = Field(description="Nome do ingrediente")
    quantidade: str = Field(description="Quantidade com unidade de medida (ex: 200g, 2 colheres de sopa)")
    substituto_economico: Optional[str] = Field(None, description="Opção de substituto mais econômico se houver")

class TabelaNutricional(BaseModel):
    calorias_kcal: int = Field(description="Total aproximado de calorias em kcal por porção")
    proteinas_g: float = Field(description="Quantidade de proteínas em gramas por porção")
    carboidratos_g: float = Field(description="Quantidade de carboidratos em gramas por porção")
    gorduras_g: float = Field(description="Quantidade de gorduras em gramas por porção")
    fibras_g: float = Field(description="Quantidade de fibras em gramas por porção")

class DadosEntradaReceita(BaseModel):
    ingredientes_em_casa: List[str] = Field(description="Lista de ingredientes disponíveis na geladeira/despensa")
    faixa_orcamento: str = Field(description="Faixa de orçamento: 'Super Econômico', 'Moderado', ou 'Sem Limite / Gourmet'")
    objetivo_saude: str = Field(description="Objetivo de saúde: 'Emagrecimento', 'Ganho de Energia', 'Digestão Leve', 'Anti-inflamatório', 'Geral'")
    restricoes: List[str] = Field(description="Restrições alimentares: 'Sem Glúten', 'Sem Lactose', 'Vegano', 'Vegetariano', 'Nenhuma'")
    tempo_maximo_minutos: int = Field(description="Tempo máximo de preparo em minutos")
    porcoes: int = Field(description="Número de porções a serem servidas")

class ReceitaNatural(BaseModel):
    titulo: str = Field(description="Título atrativo e apetitoso da receita")
    descricao_apetitosa: str = Field(description="Descrição envolvente ressaltando os sabores e aroma")
    tempo_preparo_minutos: int = Field(description="Tempo de preparo em minutos")
    custo_estimado_total_reais: float = Field(description="Custo estimado total da receita em reais")
    custo_por_porcao_reais: float = Field(description="Custo estimado por porção em reais")
    nivel_dificuldade: str = Field(description="Nível de dificuldade: Fácil, Médio ou Avançado")
    ingredientes: List[IngredienteItem] = Field(description="Lista detalhada dos ingredientes com quantidades e substitutos")
    modo_de_preparo: List[str] = Field(description="Passo a passo claro e sequencial")
    tabela_nutricional: TabelaNutricional = Field(description="Informações nutricionais por porção")
    beneficios_para_saude: List[str] = Field(description="Explicação de como os ingredientes atuam no organismo")
    dica_desperdicio_zero: str = Field(description="Dica para reaproveitamento integral de cascas, talos ou sobras")

# --- Rotas ---
@app.get("/")
def read_root():
    return {
        "status": "online",
        "servico": "SaaS API - Receitas Naturais Inteligentes e Econômicas",
        "versao": "1.0.0"
    }

@app.post("/api/v1/receitas/gerar", response_model=ReceitaNatural)
def gerar_receita(dados: DadosEntradaReceita):
    try:
        client = genai.Client()

        prompt = f"""
        Você é um chef especialista em culinária saudável, nutrição funcional e economia doméstica.
        Crie uma receita natural, saborosa, altamente nutritiva e econômica adaptada aos parâmetros do usuário.

        DADOS DO USUÁRIO:
        - Ingredientes disponíveis em casa: {", ".join(dados.ingredientes_em_casa) if dados.ingredientes_em_casa else "Nenhum informado (utilize ingredientes acessíveis)"}
        - Faixa de orçamento: {dados.faixa_orcamento}
        - Objetivo de saúde: {dados.objetivo_saude}
        - Restrições alimentares: {", ".join(dados.restricoes)}
        - Tempo máximo de preparo: {dados.tempo_maximo_minutos} minutos
        - Número de porções: {dados.porcoes}

        DIRETRIZES:
        1. Priorize o uso dos ingredientes disponíveis em casa informados pelo usuário.
        2. Priorize ingredientes naturais, sazonais e acessíveis adequados à faixa de orçamento "{dados.faixa_orcamento}".
        3. Respeite rigorosamente as restrições alimentares informadas ({", ".join(dados.restricoes)}).
        4. Mantenha o tempo total de preparo em até {dados.tempo_maximo_minutos} minutos.
        5. Estime custos realistas em Reais (R$) para o custo total e por porção.
        6. Forneça ao menos uma dica inteligente de desperdício zero (reaproveitamento de cascas, talos ou sementes).
        """

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ReceitaNatural,
            ),
        )

        return response.parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar receita inteligente: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
