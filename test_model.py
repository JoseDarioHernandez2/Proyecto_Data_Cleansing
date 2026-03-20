import pandas as pd
import joblib
import numpy as np
from pathlib import Path

def probar_modelo_entrenado():
    print("🧪 Iniciando test de predicción sincronizado...")

    try:
        # 1. CARGAR COMPONENTES
        modelo = joblib.load("modelos/modelo_v1.pkl")
        escalador = joblib.load("modelos/escalador.pkl")
        df = pd.read_pickle("data/data_procesada/dataset_avaluos_final.pkl")

        if df.empty:
            print("❌ El dataset está vacío.")
            return

        # 2. DEFINIR ESTRUCTURA ORIGINAL (Lo que hiciste en el Notebook)
        columnas_numericas = [
            'Area total', 'Estrato', 'Total habitaciones', 'Total baños', 
            'Total garajes', 'Vetustez', 'Piso numero'
        ]
        columnas_categoricas = ['Ciudad', 'Tipo inmueble', 'Estado acabados']

        # Tomamos el primer registro para la prueba
        registro_ejemplo = df.iloc[[0]].copy()
        valor_real = registro_ejemplo["Valor comercial"].values[0]

        print(f"\n🏠 Probando inmueble con Area: {registro_ejemplo['Area total'].values[0]}m2")
        print(f"💰 Valor Real en DB: ${valor_real:,.0f}")

        # 3. APLICAR GET_DUMMIES (Igual que en el entrenamiento)
        # Esto crea las columnas 'Ciudad_BOGOTA', etc., para este registro
        X_test_dummies = pd.get_dummies(
            registro_ejemplo[columnas_numericas + columnas_categoricas], 
            columns=columnas_categoricas
        )

        # 4. REINDEXAR (El paso maestro)
        # Esto asegura que X_test tenga las MISMAS columnas que el modelo conoce.
        # Las que faltan se llenan con 0.
        columnas_entrenamiento = escalador.feature_names_in_
        X_test_final = X_test_dummies.reindex(columns=columnas_entrenamiento, fill_value=0)

        # 5. ESCALAR Y PREDECIR
        print("⚙️ Escalando datos y prediciendo...")
        X_scaled = escalador.transform(X_test_final)
        
        prediccion = modelo.predict(X_scaled)[0]

        # 6. MOSTRAR RESULTADOS
        error_abs = abs(valor_real - prediccion)
        precision = (1 - (error_abs / valor_real)) * 100 if valor_real > 0 else 0

        print("-" * 40)
        print(f"🔮 PREDICCIÓN IA: ${prediccion:,.0f}")
        print(f"📊 Margen de acierto: {precision:.2f}%")
        print("-" * 40)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    probar_modelo_entrenado()