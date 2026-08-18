from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
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
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NutriChef Natural & Econômico</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @media print {
            .no-print { display: none !important; }
            .print-only { display: block !important; }
            body { background: white !important; color: black !important; }
            .recipe-card { border: none !important; box-shadow: none !important; }
        }
    </style>
</head>
<body class="bg-emerald-50/50 min-h-screen font-sans text-slate-800">
    <header class="bg-emerald-700 text-white shadow-md no-print">
        <div class="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-4">
            <div>
                <div class="flex items-center gap-3">
                    <i class="fa-solid fa-leaf text-3xl text-emerald-300"></i>
                    <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight">NutriChef Natural & Econômico</h1>
                </div>
                <p class="text-emerald-100 text-sm mt-1">Sua culinária saudável, funcional e zero desperdício potencializada por Inteligência Artificial</p>
            </div>
            <span class="bg-emerald-800 text-emerald-200 text-xs font-semibold px-3 py-1.5 rounded-full border border-emerald-600 flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                100% IA Funcional
            </span>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <!-- Coluna 1: Formulário de Configuração (no-print) -->
            <div class="lg:col-span-5 bg-white p-6 rounded-2xl shadow-sm border border-emerald-100 no-print space-y-6">
                <h2 class="text-xl font-bold text-emerald-900 border-b border-emerald-100 pb-3 flex items-center gap-2">
                    <i class="fa-solid fa-sliders text-emerald-600"></i> Monte suas Preferências
                </h2>

                <form id="recipeForm" onsubmit="gerarReceita(event)" class="space-y-5">
                    <!-- Ingredientes -->
                    <div>
                        <label class="block text-sm font-semibold text-slate-700 mb-1">Ingredientes na Geladeira/Despensa</label>
                        <input type="text" id="ingredientes" placeholder="Ex: abóbora, cenoura, aveia, ovos, gengibre"
                            class="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition">
                        <span class="text-xs text-slate-400 mt-1 block">Separe os ingredientes por vírgula</span>
                    </div>

                    <!-- Faixa de Orçamento -->
                    <div>
                        <label class="block text-sm font-semibold text-slate-700 mb-2">Faixa de Orçamento</label>
                        <div class="grid grid-cols-3 gap-2">
                            <label class="cursor-pointer">
                                <input type="radio" name="orcamento" value="Super Econômico" checked class="peer sr-only">
                                <div class="p-2.5 text-center text-xs font-medium rounded-xl border border-slate-200 peer-checked:border-emerald-600 peer-checked:bg-emerald-50 peer-checked:text-emerald-800 transition">
                                    💰 Super Econômico
                                </div>
                            </label>
                            <label class="cursor-pointer">
                                <input type="radio" name="orcamento" value="Moderado" class="peer sr-only">
                                <div class="p-2.5 text-center text-xs font-medium rounded-xl border border-slate-200 peer-checked:border-emerald-600 peer-checked:bg-emerald-50 peer-checked:text-emerald-800 transition">
                                    ⚖️ Moderado
                                </div>
                            </label>
                            <label class="cursor-pointer">
                                <input type="radio" name="orcamento" value="Sem Limite / Gourmet" class="peer sr-only">
                                <div class="p-2.5 text-center text-xs font-medium rounded-xl border border-slate-200 peer-checked:border-emerald-600 peer-checked:bg-emerald-50 peer-checked:text-emerald-800 transition">
                                    ✨ Gourmet
                                </div>
                            </label>
                        </div>
                    </div>

                    <!-- Objetivo de Saúde -->
                    <div>
                        <label class="block text-sm font-semibold text-slate-700 mb-1">Objetivo de Saúde</label>
                        <select id="objetivo" class="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition bg-white">
                            <option value="Geral">Geral / Equilíbrio</option>
                            <option value="Emagrecimento">Emagrecimento</option>
                            <option value="Ganho de Energia">Ganho de Energia</option>
                            <option value="Digestão Leve">Digestão Leve</option>
                            <option value="Anti-inflamatório">Anti-inflamatório</option>
                        </select>
                    </div>

                    <!-- Restrições Alimentares -->
                    <div>
                        <label class="block text-sm font-semibold text-slate-700 mb-2">Restrições Alimentares</label>
                        <div class="grid grid-cols-2 gap-2 text-xs">
                            <label class="flex items-center gap-2 p-2 rounded-lg border border-slate-100 hover:bg-slate-50 cursor-pointer">
                                <input type="checkbox" name="restricao" value="Sem Glúten" class="rounded text-emerald-600 focus:ring-emerald-500"> Sem Glúten
                            </label>
                            <label class="flex items-center gap-2 p-2 rounded-lg border border-slate-100 hover:bg-slate-50 cursor-pointer">
                                <input type="checkbox" name="restricao" value="Sem Lactose" class="rounded text-emerald-600 focus:ring-emerald-500"> Sem Lactose
                            </label>
                            <label class="flex items-center gap-2 p-2 rounded-lg border border-slate-100 hover:bg-slate-50 cursor-pointer">
                                <input type="checkbox" name="restricao" value="Vegano" class="rounded text-emerald-600 focus:ring-emerald-500"> Vegano
                            </label>
                            <label class="flex items-center gap-2 p-2 rounded-lg border border-slate-100 hover:bg-slate-50 cursor-pointer">
                                <input type="checkbox" name="restricao" value="Vegetariano" class="rounded text-emerald-600 focus:ring-emerald-500"> Vegetariano
                            </label>
                        </div>
                    </div>

                    <!-- Controles de Tempo e Porções -->
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <div class="flex justify-between items-center mb-1">
                                <label class="text-xs font-semibold text-slate-700">Tempo Máximo</label>
                                <span id="tempoValue" class="text-xs font-bold text-emerald-700">30 min</span>
                            </div>
                            <input type="range" id="tempo" min="10" max="90" step="5" value="30" oninput="document.getElementById('tempoValue').innerText = this.value + ' min'"
                                class="w-full accent-emerald-600 cursor-pointer">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-700 mb-1">Porções</label>
                            <input type="number" id="porcoes" min="1" max="12" value="2"
                                class="w-full text-sm px-3 py-1.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 text-center">
                        </div>
                    </div>

                    <!-- Botão Submeter -->
                    <button type="submit" id="btnSubmit" class="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white font-bold rounded-xl shadow-md hover:shadow-lg transition flex items-center justify-center gap-2">
                        <span>🌿 Criar Minha Receita Inteligente</span>
                    </button>
                </form>
            </div>

            <!-- Coluna 2: Card da Receita Gerada -->
            <div class="lg:col-span-7">
                <!-- Estado Inicial -->
                <div id="initialState" class="bg-white p-12 rounded-2xl border border-dashed border-emerald-200 text-center flex flex-col items-center justify-center min-h-[450px]">
                    <div class="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center text-2xl mb-4">
                        <i class="fa-solid fa-utensils"></i>
                    </div>
                    <h3 class="text-lg font-bold text-slate-700">Sua Receita Aparecerá Aqui</h3>
                    <p class="text-slate-400 text-sm max-w-sm mt-2">Preencha suas preferências e clique no botão para a Inteligência Artificial criar uma receita sob medida para você.</p>
                </div>

                <!-- Estado Loading -->
                <div id="loadingState" class="hidden bg-white p-12 rounded-2xl border border-emerald-100 text-center flex flex-col items-center justify-center min-h-[450px] space-y-4">
                    <div class="animate-spin rounded-full h-12 w-12 border-4 border-emerald-600 border-t-transparent"></div>
                    <p class="text-emerald-900 font-bold">Criando sua receita sob medida...</p>
                    <p class="text-slate-400 text-xs">Calculando macros nutricionais, harmonização de ingredientes e dicas de economia zero desperdício.</p>
                </div>

                <!-- Estado Resultado / Receita -->
                <div id="recipeCard" class="hidden recipe-card bg-white p-6 sm:p-8 rounded-2xl border border-emerald-100 shadow-sm space-y-6">
                    <!-- Topo: Título e Badges -->
                    <div class="border-b border-slate-100 pb-5">
                        <div class="flex flex-wrap items-center justify-between gap-3 mb-2">
                            <span id="badgeDificuldade" class="text-xs font-semibold px-2.5 py-1 rounded-md bg-emerald-100 text-emerald-800"></span>
                            <div class="flex items-center gap-4 text-xs font-medium text-slate-500">
                                <span id="resTempo" class="flex items-center gap-1"><i class="fa-regular fa-clock text-emerald-600"></i> <span></span></span>
                                <span id="resCustoPorcao" class="flex items-center gap-1 text-emerald-700 font-bold"><i class="fa-solid fa-tag"></i> <span></span></span>
                            </div>
                        </div>
                        <h2 id="resTitulo" class="text-2xl font-black text-slate-800 mb-2"></h2>
                        <p id="resDescricao" class="text-sm text-slate-600 leading-relaxed italic"></p>
                    </div>

                    <!-- Tabela Nutricional -->
                    <div class="bg-emerald-50/70 p-4 rounded-xl border border-emerald-100">
                        <h4 class="text-xs font-bold text-emerald-900 uppercase tracking-wider mb-3 flex items-center gap-2">
                            <i class="fa-solid fa-chart-pie text-emerald-600"></i> Informações Nutricionais (Por Porção)
                        </h4>
                        <div class="grid grid-cols-5 gap-2 text-center">
                            <div class="bg-white p-2 rounded-lg">
                                <span class="block text-[10px] text-slate-400 font-medium">Calorias</span>
                                <span id="nutriCalorias" class="text-sm font-bold text-emerald-800"></span>
                            </div>
                            <div class="bg-white p-2 rounded-lg">
                                <span class="block text-[10px] text-slate-400 font-medium">Proteínas</span>
                                <span id="nutriProteinas" class="text-sm font-bold text-emerald-800"></span>
                            </div>
                            <div class="bg-white p-2 rounded-lg">
                                <span class="block text-[10px] text-slate-400 font-medium">Carboidratos</span>
                                <span id="nutriCarbos" class="text-sm font-bold text-emerald-800"></span>
                            </div>
                            <div class="bg-white p-2 rounded-lg">
                                <span class="block text-[10px] text-slate-400 font-medium">Gorduras</span>
                                <span id="nutriGorduras" class="text-sm font-bold text-emerald-800"></span>
                            </div>
                            <div class="bg-white p-2 rounded-lg">
                                <span class="block text-[10px] text-slate-400 font-medium">Fibras</span>
                                <span id="nutriFibras" class="text-sm font-bold text-emerald-800"></span>
                            </div>
                        </div>
                    </div>

                    <!-- Ingredientes -->
                    <div>
                        <h4 class="text-base font-bold text-slate-800 mb-3 flex items-center gap-2">
                            <i class="fa-solid fa-basket-shopping text-emerald-600"></i> Ingredientes
                        </h4>
                        <ul id="resIngredientes" class="space-y-2 text-sm"></ul>
                    </div>

                    <!-- Modo de Preparo -->
                    <div>
                        <h4 class="text-base font-bold text-slate-800 mb-3 flex items-center gap-2">
                            <i class="fa-solid fa-list-check text-emerald-600"></i> Modo de Preparo
                        </h4>
                        <div id="resModoPreparo" class="space-y-2 text-sm"></div>
                    </div>

                    <!-- Benefícios e Dica Desperdício Zero -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div class="bg-blue-50/60 p-4 rounded-xl border border-blue-100">
                            <h5 class="text-xs font-bold text-blue-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                                <i class="fa-solid fa-heart-pulse text-blue-600"></i> Benefícios para Saúde
                            </h5>
                            <ul id="resBeneficios" class="text-xs text-blue-950 space-y-1 list-disc list-inside"></ul>
                        </div>
                        <div class="bg-amber-50/60 p-4 rounded-xl border border-amber-100">
                            <h5 class="text-xs font-bold text-amber-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                                <i class="fa-solid fa-recycle text-amber-600"></i> Dica Desperdício Zero
                            </h5>
                            <p id="resDica" class="text-xs text-amber-950 leading-relaxed"></p>
                        </div>
                    </div>

                    <!-- Botão Imprimir -->
                    <div class="pt-4 border-t border-slate-100 flex justify-between items-center no-print">
                        <span id="resCustoTotal" class="text-xs text-slate-500 font-medium"></span>
                        <button onclick="window.print()" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl transition flex items-center gap-2">
                            <i class="fa-solid fa-print"></i> Imprimir / Salvar Receita
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        async function gerarReceita(e) {
            e.preventDefault();

            const rawIngredientes = document.getElementById('ingredientes').value;
            const ingredientes_em_casa = rawIngredientes ? rawIngredientes.split(',').map(i => i.trim()).filter(i => i.length > 0) : [];
            const faixa_orcamento = document.querySelector('input[name="orcamento"]:checked').value;
            const objetivo_saude = document.getElementById('objetivo').value;

            const restricoesNodes = document.querySelectorAll('input[name="restricao"]:checked');
            const restricoes = Array.from(restricoesNodes).map(cb => cb.value);
            if (restricoes.length === 0) restricoes.push("Nenhuma");

            const tempo_maximo_minutos = parseInt(document.getElementById('tempo').value, 10);
            const porcoes = parseInt(document.getElementById('porcoes').value, 10);

            const payload = {
                ingredientes_em_casa,
                faixa_orcamento,
                objetivo_saude,
                restricoes,
                tempo_maximo_minutos,
                porcoes
            };

            // UI States
            document.getElementById('initialState').classList.add('hidden');
            document.getElementById('recipeCard').classList.add('hidden');
            document.getElementById('loadingState').classList.remove('hidden');
            document.getElementById('btnSubmit').disabled = true;

            try {
                const response = await fetch('/api/v1/receitas/gerar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    throw new Error('Falha ao gerar receita. Tente novamente.');
                }

                const data = await response.json();
                renderizarReceita(data);

                document.getElementById('loadingState').classList.add('hidden');
                document.getElementById('recipeCard').classList.remove('hidden');
            } catch (err) {
                alert(err.message || 'Erro de conexão.');
                document.getElementById('loadingState').classList.add('hidden');
                document.getElementById('initialState').classList.remove('hidden');
            } finally {
                document.getElementById('btnSubmit').disabled = false;
            }
        }

        function renderizarReceita(data) {
            document.getElementById('resTitulo').innerText = data.titulo;
            document.getElementById('resDescricao').innerText = data.descricao_apetitosa;
            document.getElementById('badgeDificuldade').innerText = 'Dificuldade: ' + data.nivel_dificuldade;
            document.getElementById('resTempo').querySelector('span').innerText = data.tempo_preparo_minutos + ' min';
            document.getElementById('resCustoPorcao').querySelector('span').innerText = 'R$ ' + data.custo_por_porcao_reais.toFixed(2) + ' / porção';
            document.getElementById('resCustoTotal').innerText = 'Custo estimado total: R$ ' + data.custo_estimado_total_reais.toFixed(2);

            // Nutrição
            const t = data.tabela_nutricional;
            document.getElementById('nutriCalorias').innerText = t.calorias_kcal + ' kcal';
            document.getElementById('nutriProteinas').innerText = t.proteinas_g + 'g';
            document.getElementById('nutriCarbos').innerText = t.carboidratos_g + 'g';
            document.getElementById('nutriGorduras').innerText = t.gorduras_g + 'g';
            document.getElementById('nutriFibras').innerText = t.fibras_g + 'g';

            // Ingredientes
            const ingUl = document.getElementById('resIngredientes');
            ingUl.innerHTML = '';
            data.ingredientes.forEach(ing => {
                const li = document.createElement('li');
                li.className = 'flex flex-col sm:flex-row sm:items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100 gap-1';
                let subHtml = ing.substituto_economico ? `<span class="text-xs text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">💡 Opção econômica: ${ing.substituto_economico}</span>` : '';
                li.innerHTML = `<div><span class="font-semibold text-slate-800">${ing.nome}</span> - <span class="text-slate-600">${ing.quantidade}</span></div> ${subHtml}`;
                ingUl.appendChild(li);
            });

            // Modo de preparo
            const modoDiv = document.getElementById('resModoPreparo');
            modoDiv.innerHTML = '';
            data.modo_de_preparo.forEach((passo, idx) => {
                const step = document.createElement('label');
                step.className = 'flex items-start gap-3 p-3 rounded-lg border border-slate-100 hover:bg-slate-50/80 cursor-pointer transition';
                step.innerHTML = `
                    <input type="checkbox" class="mt-1 rounded text-emerald-600 focus:ring-emerald-500">
                    <span class="text-slate-700 leading-relaxed"><strong class="text-emerald-800">Passo ${idx + 1}:</strong> ${passo}</span>
                `;
                modoDiv.appendChild(step);
            });

            // Benefícios
            const benUl = document.getElementById('resBeneficios');
            benUl.innerHTML = '';
            data.beneficios_para_saude.forEach(b => {
                const li = document.createElement('li');
                li.innerText = b;
                benUl.appendChild(li);
            });

            // Dica
            document.getElementById('resDica').innerText = data.dica_desperdicio_zero;
        }
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)

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
