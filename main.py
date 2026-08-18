from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import uvicorn
from google import genai
from google.genai import types

app = FastAPI(title="SaaS API - Gerador de Curriculos Profissionais", version="1.0.0")

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
    periodo: str = Field(description="Periodo de atuacao")
    conquistas: List[str] = Field(description="Lista de conquistas e responsabilidades usando verbos de acao e impacto")

class CategoriaHabilidade(BaseModel):
    categoria: str = Field(description="Ex: Tecnicas, Ferramentas, Interpessoais")
    itens: List[str] = Field(description="Lista de habilidades dessa categoria")

class CurriculoProfissional(BaseModel):
    resumo_profissional_otimizado: str = Field(description="Resumo profissional otimizado e atraente para recrutadores e sistemas ATS")
    cargo_sugerido: str = Field(description="Cargo sugerido ou otimizado para o curriculo")
    experiencias_reformuladas: List[ExperienciaReformulada] = Field(description="Lista de experiencias profissionais reformuladas com conquistas de alto impacto")
    habilidades_organizadas: List[CategoriaHabilidade] = Field(description="Habilidades categorizadas em grupos")
    formacao_formatada: List[str] = Field(description="Lista de formacoes academicas formatadas profissionalmente")
    dicas_para_entrevista: List[str] = Field(description="Dicas estrategicas para entrevistas focadas no cargo alvo")

# --- Interface Web (HTML/Tailwind) ---
HTML_CONTENT = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CurriculoAI - Gerador Inteligente de Curriculos</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @media print {
            body * {
                visibility: hidden;
            }
            #printable-curriculum, #printable-curriculum * {
                visibility: visible;
            }
            #printable-curriculum {
                position: absolute;
                left: 0;
                top: 0;
                width: 100%;
                padding: 0;
                margin: 0;
                box-shadow: none !important;
                border: none !important;
            }
            .no-print {
                display: none !important;
            }
        }
    </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen font-sans antialiased">
    <!-- Header -->
    <header class="bg-slate-800 border-b border-slate-700 py-6 px-4 no-print">
        <div class="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <div class="bg-indigo-600 p-3 rounded-xl shadow-lg">
                    <i class="fa-solid me-2 fa-file-contract text-2xl text-white"></i>
                </div>
                <div>
                    <h1 class="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
                        CurriculoAI
                    </h1>
                    <p class="text-xs text-slate-400">Transforme sua trajetoria em um curriculo de alto impacto com IA</p>
                </div>
            </div>
            <span class="bg-indigo-950 text-indigo-300 border border-indigo-800 text-xs font-semibold px-3 py-1 rounded-full">
                Otimizado para ATS & Recrutadores
            </span>
        </div>
    </header>

    <!-- Conteudo Principal -->
    <main class="max-w-7xl mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-8 my-6">
        <!-- Formulario (Lado Esquerdo) -->
        <section class="lg:col-span-6 space-y-6 no-print">
            <div class="bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl">
                <h2 class="text-xl font-bold text-indigo-400 mb-4 flex items-center gap-2">
                    <i class="fa-solid fa-user-pen"></i> 1. Dados Pessoais & Objetivo
                </h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Nome Completo *</label>
                        <input type="text" id="nome_completo" placeholder="Ex: Maria Silva" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">E-mail *</label>
                        <input type="email" id="email" placeholder="maria@email.com" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Telefone *</label>
                        <input type="text" id="telefone" placeholder="(11) 99999-9999" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">LinkedIn (Opcional)</label>
                        <input type="text" id="linkedin" placeholder="linkedin.com/in/mariasilva" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                    </div>
                    <div class="md:col-span-2">
                        <label class="block text-xs font-medium text-slate-300 mb-1">Cargo Alvo Desejado *</label>
                        <input type="text" id="cargo_alvo" placeholder="Ex: Desenvolvedor Full Stack Senior" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                    </div>
                </div>
            </div>

            <!-- Experiencia / Resumo Bruto -->
            <div class="bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl">
                <h2 class="text-xl font-bold text-indigo-400 mb-4 flex items-center gap-2">
                    <i class="fa-solid fa-briefcase"></i> 2. Resumo da Trajetoria & Experiencias
                </h2>
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Desabafe sua Trajetoria Profissional *</label>
                        <textarea id="resumo_pessoal_bruto" rows="3" placeholder="Conte em poucas palavras o que voce faz, seus principais desafios e momentos marcantes..." class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"></textarea>
                    </div>
                    
                    <div class="border-t border-slate-700 pt-4">
                        <label class="block text-xs font-semibold text-slate-200 mb-2">Ultima Experiencia Profissional</label>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <input type="text" id="exp_empresa" placeholder="Empresa (Ex: Tech Corp)" class="bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm text-white">
                            <input type="text" id="exp_cargo" placeholder="Cargo (Ex: Analista de Sistemas)" class="bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm text-white">
                            <input type="text" id="exp_periodo" placeholder="Periodo (Ex: 2021 - Atual)" class="bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm text-white md:col-span-2">
                            <textarea id="exp_descricao" rows="3" placeholder="O que voce fazia la? O que conquistou? Pode escrever de forma simples!" class="bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm text-white md:col-span-2"></textarea>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Habilidades & Formacao -->
            <div class="bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl space-y-4">
                <h2 class="text-xl font-bold text-indigo-400 mb-4 flex items-center gap-2">
                    <i class="fa-solid fa-graduation-cap"></i> 3. Habilidades & Formacao
                </h2>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Habilidades (separadas por virgula) *</label>
                    <input type="text" id="habilidades" placeholder="Python, JavaScript, Docker, Lideranca de Equipe, SQL" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3 border-t border-slate-700 pt-4">
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Curso *</label>
                        <input type="text" id="form_curso" placeholder="Ex: Ciencia da Computacao" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-sm text-white">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Instituicao *</label>
                        <input type="text" id="form_inst" placeholder="Ex: USP" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-sm text-white">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-300 mb-1">Ano Conclusao *</label>
                        <input type="text" id="form_ano" placeholder="Ex: 2022" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-sm text-white">
                    </div>
                </div>
            </div>

            <!-- Botao de Gerar -->
            <button id="btn-gerar" onclick="gerarCurriculo()" class="w-full bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-bold py-4 rounded-xl shadow-lg transition duration-200 flex items-center justify-center gap-2 text-lg">
                <span>✨ Gerar Meu Curriculo Profissional</span>
            </button>
        </section>

        <!-- Painel de Preview (Lado Direito) -->
        <section class="lg:col-span-6">
            <div class="sticky top-6 space-y-4">
                <div class="flex items-center justify-between no-print">
                    <h2 class="text-lg font-semibold text-slate-300 flex items-center gap-2">
                        <i class="fa-solid fa-eye"></i> Pre-visualizacao do Curriculo
                    </h2>
                    <button id="btn-print" onclick="window.print()" disabled class="opacity-50 cursor-not-allowed bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold py-2 px-4 rounded-lg flex items-center gap-2 transition">
                        <i class="fa-solid fa-print"></i> Imprimir / Salvar PDF
                    </button>
                </div>

                <!-- Card / Folha A4 do Curriculo -->
                <div id="printable-curriculum" class="bg-white text-slate-900 rounded-2xl p-8 shadow-2xl min-h-[650px] flex flex-col justify-between border border-slate-200">
                    
                    <!-- Estado Inicial / Placeholder -->
                    <div id="preview-placeholder" class="my-auto text-center py-16 text-slate-400 space-y-4 no-print">
                        <i class="fa-solid fa-wand-magic-sparkles text-5xl text-indigo-300 animate-pulse"></i>
                        <p class="text-sm font-medium">Preencha o formulario ao lado e clique em <br><strong class="text-indigo-600">"Gerar Meu Curriculo Profissional"</strong></p>
                    </div>

                    <!-- Loading State -->
                    <div id="preview-loading" class="hidden my-auto text-center py-16 space-y-4 no-print">
                        <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-indigo-600 border-t-transparent"></div>
                        <p class="text-sm font-semibold text-indigo-600 animate-pulse">Nossa Inteligencia Artificial esta otimizando seu curriculo...</p>
                    </div>

                    <!-- Conteudo do Curriculo Gerado -->
                    <div id="curriculum-content" class="hidden space-y-6">
                        <!-- Cabeçalho -->
                        <div class="border-b-2 border-indigo-600 pb-4">
                            <h1 id="cv-nome" class="text-3xl font-extrabold text-slate-900 uppercase tracking-tight">Nome do Candidato</h1>
                            <p id="cv-cargo" class="text-md font-semibold text-indigo-600 mt-1">Cargo Alvo Sugerido</p>
                            <div class="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600 mt-3">
                                <span id="cv-email"><i class="fa-solid fa-envelope mr-1"></i> email@exemplo.com</span>
                                <span id="cv-telefone"><i class="fa-solid fa-phone mr-1"></i> (00) 00000-0000</span>
                                <span id="cv-linkedin"><i class="fa-brands fa-linkedin mr-1"></i> linkedin.com/in/perfil</span>
                            </div>
                        </div>

                        <!-- Perfil Profissional -->
                        <div>
                            <h2 class="text-xs font-bold uppercase tracking-wider text-indigo-600 border-b border-slate-200 pb-1 mb-2">Perfil Profissional</h2>
                            <p id="cv-resumo" class="text-xs leading-relaxed text-slate-700 justify-baseline"></p>
                        </div>

                        <!-- Experiencias -->
                        <div>
                            <h2 class="text-xs font-bold uppercase tracking-wider text-indigo-600 border-b border-slate-200 pb-1 mb-2">Experiencia Profissional</h2>
                            <div id="cv-experiencias" class="space-y-3"></div>
                        </div>

                        <!-- Habilidades Organizadas -->
                        <div>
                            <h2 class="text-xs font-bold uppercase tracking-wider text-indigo-600 border-b border-slate-200 pb-1 mb-2">Habilidades & Competencias</h2>
                            <div id="cv-habilidades" class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs"></div>
                        </div>

                        <!-- Formacao -->
                        <div>
                            <h2 class="text-xs font-bold uppercase tracking-wider text-indigo-600 border-b border-slate-200 pb-1 mb-2">Formacao Academica</h2>
                            <ul id="cv-formacao" class="list-disc list-inside text-xs text-slate-700 space-y-1"></ul>
                        </div>
                    </div>
                </div>

                <!-- Box de Dicas de Entrevista -->
                <div id="box-dicas" class="hidden bg-slate-800 border border-indigo-900 rounded-2xl p-5 shadow-lg no-print">
                    <h3 class="text-sm font-bold text-amber-400 mb-2 flex items-center gap-2">
                        <i class="fa-solid fa-lightbulb"></i> Dicas de Ouro para a sua Entrevista
                    </h3>
                    <ul id="cv-dicas" class="list-disc list-inside text-xs text-slate-300 space-y-1.5"></ul>
                </div>
            </div>
        </section>
    </main>

    <script>
        async function gerarCurriculo() {
            const nome = document.getElementById('nome_completo').value.trim();
            const email = document.getElementById('email').value.trim();
            const telefone = document.getElementById('telefone').value.trim();
            const linkedin = document.getElementById('linkedin').value.trim();
            const cargo_alvo = document.getElementById('cargo_alvo').value.trim();
            const resumo = document.getElementById('resumo_pessoal_bruto').value.trim();
            const habInput = document.getElementById('habilidades').value.trim();
            
            if (!nome || !email || !telefone || !cargo_alvo || !resumo || !habInput) {
                alert('Por favor, preencha todos os campos obrigatorios (*) para continuar.');
                return;
            }

            const habilidades = habInput.split(',').map(h => h.trim()).filter(h => h);
            
            const empresa = document.getElementById('exp_empresa').value.trim() || 'Empresa';
            const cargoExp = document.getElementById('exp_cargo').value.trim() || cargo_alvo;
            const periodoExp = document.getElementById('exp_periodo').value.trim() || 'Recente';
            const descExp = document.getElementById('exp_descricao').value.trim() || resumo;

            const experiencias = [{
                empresa: empresa,
                cargo: cargoExp,
                descricao_bruta: descExp,
                periodo: periodoExp
            }];

            const curso = document.getElementById('form_curso').value.trim() || 'Graduacao';
            const inst = document.getElementById('form_inst').value.trim() || 'Universidade';
            const ano = document.getElementById('form_ano').value.trim() || '2023';

            const formacao = [{
                instituicao: inst,
                curso: curso,
                ano_conclusao: ano
            }];

            const payload = {
                nome_completo: nome,
                email: email,
                telefone: telefone,
                linkedin: linkedin || null,
                cargo_alvo: cargo_alvo,
                resumo_pessoal_bruto: resumo,
                habilidades: habilidades,
                experiencias: experiencias,
                formacao: formacao
            };

            // UI Loading
            document.getElementById('preview-placeholder').classList.add('hidden');
            document.getElementById('curriculum-content').classList.add('hidden');
            document.getElementById('box-dicas').classList.add('hidden');
            document.getElementById('preview-loading').classList.remove('hidden');
            document.getElementById('btn-gerar').disabled = true;
            document.getElementById('btn-gerar').classList.add('opacity-50');

            try {
                const response = await fetch('/api/v1/curriculo/gerar', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Erro ao gerar curriculo.');
                }

                const data = await response.json();
                renderizarCurriculo(data, payload);
            } catch (error) {
                alert('Ocorreu um erro ao processar: ' + error.message);
                document.getElementById('preview-loading').classList.add('hidden');
                document.getElementById('preview-placeholder').classList.remove('hidden');
            } finally {
                document.getElementById('btn-gerar').disabled = false;
                document.getElementById('btn-gerar').classList.remove('opacity-50');
            }
        }

        function renderizarCurriculo(data, inputPayload) {
            document.getElementById('preview-loading').classList.add('hidden');
            document.getElementById('curriculum-content').classList.remove('hidden');
            document.getElementById('box-dicas').classList.remove('hidden');

            // Preencher cabecalho
            document.getElementById('cv-nome').innerText = inputPayload.nome_completo;
            document.getElementById('cv-cargo').innerText = data.cargo_sugerido || inputPayload.cargo_alvo;
            document.getElementById('cv-email').innerHTML = `<i class="fa-solid fa-envelope mr-1"></i>${inputPayload.email}`;
            document.getElementById('cv-telefone').innerHTML = `<i class="fa-solid fa-phone mr-1"></i>${inputPayload.telefone}`;
            
            const linkedinSpan = document.getElementById('cv-linkedin');
            if (inputPayload.linkedin) {
                linkedinSpan.style.display = 'inline-block';
                linkedinSpan.innerHTML = `<i class="fa-brands fa-linkedin mr-1"></i>${inputPayload.linkedin}`;
            } else {
                linkedinSpan.style.display = 'none';
            }

            // Resumo
            document.getElementById('cv-resumo').innerText = data.resumo_profissional_otimizado;

            // Experiencias
            const expContainer = document.getElementById('cv-experiencias');
            expContainer.innerHTML = '';
            data.experiencias_reformuladas.forEach(exp => {
                const expDiv = document.createElement('div');
                expDiv.className = 'space-y-1';
                let conquistasHtml = exp.conquistas.map(c => `<li class="text-xs text-slate-700">${c}</li>`).join('');
                expDiv.innerHTML = `
                    <div class="flex justify-between items-baseline">
                        <span class="font-bold text-xs text-slate-900">${exp.cargo} - <span class="text-indigo-600">${exp.empresa}</span></span>
                        <span class="text-[10px] text-slate-500 font-medium">${exp.periodo}</span>
                    </div>
                    <ul class="list-disc list-inside space-y-0.5 ml-1">${conquistasHtml}</ul>
                `;
                expContainer.appendChild(expDiv);
            });

            // Habilidades Organizadas
            const habContainer = document.getElementById('cv-habilidades');
            habContainer.innerHTML = '';
            data.habilidades_organizadas.forEach(cat => {
                const catDiv = document.createElement('div');
                catDiv.innerHTML = `<strong class="text-slate-800">${cat.categoria}:</strong> <span class="text-slate-600">${cat.itens.join(', ')}</span>`;
                habContainer.appendChild(catDiv);
            });

            // Formacao
            const formContainer = document.getElementById('cv-formacao');
            formContainer.innerHTML = '';
            data.formacao_formatada.forEach(f => {
                const li = document.createElement('li');
                li.innerText = f;
                formContainer.appendChild(li);
            });

            // Dicas de Entrevista
            const dicasContainer = document.getElementById('cv-dicas');
            dicasContainer.innerHTML = '';
            data.dicas_para_entrevista.forEach(dica => {
                const li = document.createElement('li');
                li.innerText = dica;
                dicasContainer.appendChild(li);
            });

            // Habilitar botao de impressao
            const btnPrint = document.getElementById('btn-print');
            btnPrint.disabled = false;
            btnPrint.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    </script>
</body>
</html>
"""

# --- Rotas ---
@app.get("/", response_class=HTMLResponse)
def read_root():
    return HTML_CONTENT

@app.get("/saudacao/{nome}")
def saudacao(nome: str):
    return {"mensagem": f"Ola, {nome}! Seja bem-vindo(a) ao SaaS de Curriculos com IA."}

@app.post("/api/v1/curriculo/gerar", response_model=CurriculoProfissional)
def gerar_curriculo(dados: DadosEntradaCurriculo):
    try:
        client = genai.Client()

        prompt = f"""
        Voce e um especialista senior em recrutamento e otimizacao de curriculos para sistemas ATS (Applicant Tracking Systems).
        Transforme as informacoes brutas fornecidas em um curriculo profissional de alta performance adaptado para o cargo alvo.

        DADOS DO CANDIDATO:
        - Nome: {dados.nome_completo}
        - Email: {dados.email}
        - Telefone: {dados.telefone}
        - LinkedIn: {dados.linkedin or 'Nao informado'}
        - Cargo Alvo: {dados.cargo_alvo}
        - Resumo Pessoal Bruto: {dados.resumo_pessoal_bruto}
        - Habilidades Informadas: {", ".join(dados.habilidades)}

        EXPERIENCIAS BRUTAS:
        {[exp.model_dump() for exp in dados.experiencias]}

        FORMACAO ACADEMICA:
        {[form.model_dump() for form in dados.formacao]}

        DIRETRIZES:
        1. Crie um resumo profissional persuasivo focado no cargo alvo e indique um cargo sugerido adaptado.
        2. Reformule as experiencias profissionais em conquistas usando verbos de acao marcantes.
        3. Organize e categorize as habilidades em grupos logicos (ex: 'Tecnicas', 'Ferramentas', 'Interpessoais').
        4. Formate a formacao academica de maneira limpa.
        5. Forneca dicas estrategicas e personalizadas de entrevista para o cargo alvo.
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
        raise HTTPException(status_code=500, detail=f"Erro ao processar curriculo com IA: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
