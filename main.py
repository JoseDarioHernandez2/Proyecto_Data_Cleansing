import os
import pandas as pd
import logging
import joblib
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from sklearn.metrics import mean_absolute_error, r2_score

# Importaciones de tus módulos locales
from ETL.Extract_api import ProcesadorAvaluos
from ETL.Transform import transformar_datos
from validate import validar_datos
from ETL.Transform_2 import imputar_datos_globales, agregar_rango_precios # ✅ Agregamos la nueva función

# 1. VARIABLES DE ENTORNO
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# 2. RUTAS
RUTA_RAW = Path("data/data_extraida/Base_Datos_Avaluos.xlsx")
RUTA_FINAL = Path("data/data_procesada/dataset_avaluos_final.xlsx")
RUTA_PKL = RUTA_FINAL.with_suffix('.pkl')
# ✅ Apuntamos al nuevo modelo v2 que es el Pipeline
RUTA_MODELO = Path("modelos/modelo_inmobiliario_v2.pkl") 

# Carpetas
os.makedirs("logs", exist_ok=True)
os.makedirs("data/data_procesada", exist_ok=True)
os.makedirs("modelos", exist_ok=True)

# Logging
logging.basicConfig(
    filename=f"logs/pipeline_{datetime.now().strftime('%Y%m%d')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

# =================================================
# ==== FUNCIÓN ML CORREGIDA (PIPELINE) ============
# =================================================
def realizar_predicciones_ia(df):
    try:
        if not RUTA_MODELO.exists():
            print(f"⚠️ El archivo de modelo no existe en {RUTA_MODELO}. Saltando predicciones.")
            return df

        print("🔮 [ML] Generando valuaciones con Pipeline de Random Forest...")
        
        # Cargamos el Pipeline (incluye Preprocesador + Modelo)
        modelo_pipeline = joblib.load(RUTA_MODELO)

        columnas_modelo = [
            'Area total', 'Estrato', 'Total habitaciones',
            'Total baños', 'Total garajes', 'Vetustez',
            'Piso numero', 'Ciudad', 'Tipo inmueble', 'Estado acabados'
        ]

        # Validar presencia de columnas
        for col in columnas_modelo:
            if col not in df.columns:
                raise ValueError(f"Falta la columna requerida para el modelo: {col}")

        X = df[columnas_modelo].copy()

        # Predicción DIRECTA (el pipeline escala y codifica por nosotros)
        df['Valor Predicho IA'] = modelo_pipeline.predict(X)

        # Cálculo de métricas si existe el valor comercial real para comparar
        if 'Valor comercial' in df.columns:
            # Eliminar filas donde Valor comercial sea nulo para el cálculo
            df_valido = df.dropna(subset=['Valor comercial', 'Valor Predicho IA'])
            
            mae = mean_absolute_error(df_valido['Valor comercial'], df_valido['Valor Predicho IA'])
            r2 = r2_score(df_valido['Valor comercial'], df_valido['Valor Predicho IA'])
            
            print(f"📊 Desempeño Actual: R² = {r2:.4f} | MAE = ${mae:,.0f} COP")

            # Desviación %
            df['Desviacion %'] = ((df['Valor comercial'] - df['Valor Predicho IA']) / df['Valor Predicho IA']) * 100

        print("✅ Predicciones generadas correctamente")

    except Exception as e:
        print(f"❌ Error en el modelo: {e}")
        logging.error(f"Error en predicción: {e}", exc_info=True)

    return df

# =================================================
# ==== IMPUTACIÓN CATEGÓRICA ======================
# =================================================
def imputar_variables_categoricas(df):
    columnas_a_imputar = ["Nombre edificio", "Barrio", "Tipo garaje"]
    print("🧠 Iniciando imputación por moda...")

    for col in columnas_a_imputar:
        if col in df.columns:
            df[col] = df[col].replace(["SIN INFORMACION", "0", 0, "NAN", "NONE"], pd.NA)
            moda_serie = df[col].dropna().mode()

            if not moda_serie.empty:
                moda_valor = moda_serie[0]
                df[col] = df[col].fillna(moda_valor)
                print(f"   ✨ {col}: Imputado con '{moda_valor}'")
            else:
                df[col] = df[col].fillna("SIN INFORMACION")
    return df

# =================================================
# ==== MAIN =======================================
# =================================================
def main():
    print("\n" + "="*30)
    print("🚀 INICIANDO PIPELINE DE AVALUOS")
    print("="*30)

    if not API_KEY:
        print("❌ Error: Falta GEMINI_API_KEY en el archivo .env")
        return

    try:
        # 1. EXTRACT (PDFs a Excel Raw)
        procesador = ProcesadorAvaluos(api_key=API_KEY)
        print("📥 Extrayendo datos de PDFs...")
        procesador.iniciar_procesamiento_lote()

        # 2. LOAD RAW
        if not RUTA_RAW.exists():
            print(f"⚠️ No se encontró el archivo: {RUTA_RAW}")
            return
        df_raw = pd.read_excel(RUTA_RAW)

        # 3. TRANSFORM (Limpieza inicial)
        print(f"🛠️ Transformando {len(df_raw)} registros...")
        registros = []
        for _, fila in df_raw.iterrows():
            datos = fila.to_dict()
            nombre = datos.get("archivo_origen", "S/N")
            limpio = transformar_datos(datos, nombre)
            registros.append(limpio)
        
        df_final = pd.DataFrame(registros)

        # 4. ENRIQUECIMIENTO E IMPUTACIONES
        df_final = imputar_variables_categoricas(df_final)
        df_final = imputar_datos_globales(df_final)
        
        # ✅ Agregamos la categorización de rangos para visualización
        print("🏷️ Categorizando rangos de precios para negocio...")
        df_final = agregar_rango_precios(df_final)

        # 5. VALIDACIÓN TÉCNICA
        print("🔍 Validando calidad de datos...")
        validar_datos(df_final)

        # 6. MACHINE LEARNING (Predicciones)
        df_final = realizar_predicciones_ia(df_final)

        # 7. GUARDADO FINAL
        print(f"💾 Guardando resultados en {RUTA_FINAL}...")
        df_final.to_excel(RUTA_FINAL, index=False)
        df_final.to_pickle(RUTA_PKL)

        print("\n✅ PIPELINE COMPLETADO EXITOSAMENTE")
        print("="*30)

    except Exception as e:
        print(f"\n❌ Error crítico en el pipeline: {e}")
        logging.error(f"Error crítico: {e}", exc_info=True)


if __name__ == "__main__":
    main()
    
    # ================================================
    # =====                                     ======
    # =====  ejecuta con -> poetry run main.py  ======
    # =====                                     ======
    # ================================================