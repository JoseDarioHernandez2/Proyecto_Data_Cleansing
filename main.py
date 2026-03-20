import os
import pandas as pd
import logging
import joblib  # 🔹 Nueva: Para cargar el modelo .pkl
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 🔹 Importaciones desde la carpeta ETL
from ETL.Extract_api import ProcesadorAvaluos
from ETL.Transform import transformar_datos
from validate import validar_datos
from ETL.Transform_2 import imputar_datos_globales

# 1. CARGAR VARIABLES DE ENTORNO
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# 2. CONFIGURACIÓN DE RUTAS
RUTA_RAW = Path("data/data_extraida/Base_Datos_Avaluos.xlsx")
RUTA_FINAL = Path("data/data_procesada/dataset_avaluos_final.xlsx")
RUTA_SCALER = Path("modelos\escalador.pkl") 
RUTA_PKL = RUTA_FINAL.with_suffix('.pkl')
RUTA_MODELO = Path("modelos\modelo_v1.pkl") # 🔹 Ruta de tu modelo entrenado

# Asegurar carpetas
os.makedirs("logs", exist_ok=True)
os.makedirs("data/data_procesada", exist_ok=True)

# Configurar Logging
logging.basicConfig(
    filename=f"logs/pipeline_{datetime.now().strftime('%Y%m%d')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)
# =================================================
# ==== FUNCIONES DE TRANSFORMACIÓN ADICIONALES ====
# =================================================

# Definimos función de predicción de ML (Paso 7)
def realizar_predicciones_ia(df):
    try:
        print("🔮 [ML] Aplicando Scaler y generando valuaciones...")
        modelo = joblib.load(RUTA_MODELO)
        scaler = joblib.load(RUTA_SCALER) # ⬅️ CARGAR EL ESCALADOR
        
        features_modelo = [
            'Area total', 'Estrato', 'Total habitaciones', 'Total baños', 'Total garajes', 
            'Vetustez', 'Piso numero', 'Ciudad_BOGOTA D.C.', 'Ciudad_BOGOTÁ', 
            'Ciudad_MEDELLÍN', 'Ciudad_TOCANCIPÁ', 'Tipo inmueble_APARTAMENTO', 
            'Tipo inmueble_CASA', 'Estado acabados_BUENO', 
            'Estado acabados_EXCELENTE', 'Estado acabados_REGULAR'
        ]

        # 1. Preparar Dummies y alinear columnas
        df_prep = pd.get_dummies(df, columns=['Ciudad', 'Tipo inmueble', 'Estado acabados'])
        for col in features_modelo:
            if col not in df_prep.columns:
                df_prep[col] = 0
        
        X = df_prep[features_modelo].fillna(0)

        # 2. ⚡ EL PASO CRÍTICO: Escalar los datos antes de predecir
        X_scaled = scaler.transform(X) # ⬅️ Esto convierte 120m2 en el valor decimal que el modelo entiende

        # 3. Predecir
        predicciones = modelo.predict(X_scaled)
        
        # 4. Si usaste logaritmos en el entrenamiento, descomenta la siguiente línea:
        # import numpy as np
        # predicciones = np.exp(predicciones)

        df['Valor Predicho IA'] = predicciones
        
        # Calcular Desviación
        df['Desviacion %'] = ((df['Valor comercial'] - df['Valor Predicho IA']) / df['Valor Predicho IA']) * 100
        
        print(f"✅ ¡POR FIN! Predicciones coherentes generadas.")

    except Exception as e:
        print(f"❌ Error en el Scaler o Modelo: {e}")
        
    return df

def imputar_variables_categoricas(df):
    """Imputa por moda: Nombre edificio, Barrio, Tipo garaje."""
    columnas_a_imputar = ["Nombre edificio", "Barrio", "Tipo garaje"]
    print("🧠 Iniciando imputación por moda...")
    for col in columnas_a_imputar:
        if col in df.columns:
            df[col] = df[col].replace(["SIN INFORMACION", "0", 0, "NAN", "NONE"], pd.NA)
            moda_serie = df[col].dropna().mode()
            if not moda_serie.empty:
                moda_valor = moda_serie[0]
                df[col] = df[col].fillna(moda_valor)
                logging.info(f"Imputación: Columna '{col}' completada con moda: {moda_valor}")
                print(f"   ✨ {col}: Imputado con '{moda_valor}'")
            else:
                df[col] = df[col].fillna("SIN INFORMACION")
    return df

def main():
    print("🚀 INICIANDO PIPELINE CON VARIABLES DE ENTORNO...")

    if not API_KEY:
        print("❌ ERROR: No se encontró GEMINI_API_KEY en el archivo .env")
        return

    try:
        # --- PASO 1: EXTRACT ---
        procesador = ProcesadorAvaluos(api_key=API_KEY)
        print("📥 Extrayendo PDFs...")
        procesador.iniciar_procesamiento_lote()

        # --- PASO 2: LOAD RAW ---
        if not RUTA_RAW.exists():
            print("⚠️ No hay datos RAW para procesar.")
            return
        df_raw = pd.read_excel(RUTA_RAW)

        # --- PASO 3: TRANSFORM (Fila por fila) ---
        print(f"🛠️ Limpiando y formateando {len(df_raw)} registros...")
        registros_limpios = []
        for _, fila in df_raw.iterrows():
            datos_dict = fila.to_dict()
            nombre = datos_dict.get("archivo_origen", "S/N")
            datos_limpios = transformar_datos(datos_dict, nombre)
            registros_limpios.append(datos_limpios)
        df_final = pd.DataFrame(registros_limpios)

        # --- PASO 4: IMPUTACIÓN POR MODA (Global) ---
        df_final = imputar_variables_categoricas(df_final)

        # --- PASO 5: IMPUTACIÓN DE ÁREAS (Transform_2) ---
        df_final = imputar_datos_globales(df_final)

        # --- PASO 6: VALIDATE ---
        print("🔍 Validando consistencia final...")
        validar_datos(df_final)

        # --- 🚀 PASO 7: PREDICCIÓN DE Modelo ML (NUEVO) ---
        df_final = realizar_predicciones_ia(df_final)
        
        # --- GUARDADO FINAL ---
        df_final.to_excel(RUTA_FINAL, index=False)
        df_final.to_pickle(RUTA_PKL)

        print(f"✅ Pipeline completado con éxito!")
        print(f"📊 Excel con predicción valor comercial guardado en: {RUTA_FINAL}")
        print(f"📦 Pickle guardado en: {RUTA_PKL}")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        logging.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    main()