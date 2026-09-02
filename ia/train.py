import os
import joblib
import pandas as pd
from sklearn.linear_model import LinearRegression

dados = [
    {"dias": 1, "peso_kg": 450.0, "produtividade": 85.0},
    {"dias": 2, "peso_kg": 520.0, "produtividade": 92.0},
    {"dias": 3, "peso_kg": 600.0, "produtividade": 98.0},
    {"dias": 4, "peso_kg": 680.0, "produtividade": 104.0},
    {"dias": 5, "peso_kg": 750.0, "produtividade": 112.0},
]

df = pd.DataFrame(dados)
X = df[["dias", "peso_kg"]]
y = df["produtividade"]

modelo = LinearRegression()
modelo.fit(X, y)

# Garante o caminho correto no ambiente local e no Render
os.makedirs("models", exist_ok=True)
joblib.dump(modelo, "models/produtividade_model.pkl")
print("✅ Modelo do Módulo Tropical treinado e salvo com sucesso!")
