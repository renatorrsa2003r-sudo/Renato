from fastapi import FastAPI
import uvicorn

app = FastAPI(title="SaaS API", version="1.0.0")

@app.get("/")
def read_root():
    return {"status": "SaaS Online", "versao": "1.0.0"}

@app.get("/saudacao/{nome}")
def saudacao(nome: str):
    return {"mensagem": f"Olá, {nome}! Seja bem-vindo(a) ao SaaS."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
