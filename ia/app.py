import os
import joblib
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

ml_models = {}
MODEL_PATH = "models/produtividade_model.pkl"

@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.path.exists(MODEL_PATH):
        ml_models["produtividade"] = joblib.load(MODEL_PATH)
    yield
    ml_models.clear()

app = FastAPI(title="Módulo Tropical - API IA", lifespan=lifespan)

class PrevisaoRequest(BaseModel):
    proximo_dia: int = Field(..., gt=0)
    proximo_peso_kg: float = Field(..., gt=0)

class PrevisaoResponse(BaseModel):
    produtividade_prevista: float

@app.post("/previsao_produtividade", response_model=PrevisaoResponse)
def previsao(payload: PrevisaoRequest):
    modelo = ml_models.get("produtividade")
    if not modelo:
        raise HTTPException(status_code=503, detail="Modelo não carregado")

    entrada = [[payload.proximo_dia, payload.proximo_peso_kg]]
    predicao = modelo.predict(entrada)
    return PrevisaoResponse(produtividade_prevista=round(float(predicao[0]), 2))

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
