import pandas as pd
import numpy as np

# Función para extraer datos de la matriz y convertirlos en un diccionario (extraer del PDF)
def transformar_a_diccionario(matriz_datos):
    resultado = {}
    for i in range(0, len(matriz_datos), 2):
        etiquetas = matriz_datos[i]
        valores = matriz_datos[i+1] if i+1 < len(matriz_datos) else None
        if valores:
            for etiqueta, valor in zip(etiquetas, valores):
                if etiqueta and etiqueta.strip():
                    val_limpio = valor.strip() if valor else ""
                    clave = etiqueta.replace("\n", " ").strip()
                    resultado[clave] = val_limpio
    return resultado
# Función para crear un DataFrame a partir de una lista de diccionarios
def crear_dataframe(lista_dict):
    return pd.DataFrame(lista_dict)
# Función para limpiar y enriquecer el dataset final
def limpiar_y_enriquecer_dataset(df):
    df = df.copy()

    # --- 1. CONVERSIÓN DE FECHAS (Prioridad para cálculos posteriores) ---
    if 'Fecha avaluo' in df.columns:
        df['Fecha avaluo'] = pd.to_datetime(df['Fecha avaluo'], dayfirst=True, errors='coerce')

    # --- 2. LIMPIEZA NUMÉRICA ---
    cols_numericas = ['Valor comercial', 'Valor catastral', 'Area total', 'Area privada', 'Estrato', 'Año construccion']
    for col in cols_numericas:
        if col in df.columns:
            df[col] = (df[col].astype(str)
                       .replace(r'[\$\.\s]', '', regex=True)
                       .replace(['', 'nan', 'None'], np.nan))
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # --- 3. ESTANDARIZACIÓN DE TEXTO ---
    cols_texto = ['Tipo inmueble', 'Barrio', 'Ciudad', 'Estado acabados']
    for col in cols_texto:
        if col in df.columns:
            df[col] = df[col].str.upper().str.strip()

    # --- 4. FEATURE ENGINEERING & DATA QUALITY ---
    
    # Valor por metro cuadrado (con manejo de errores)
    if 'Valor comercial' in df.columns and 'Area total' in df.columns:
        # Reemplazamos ceros por NaN para evitar divisiones infinitas
        areas_limpias = df['Area total'].replace(0, np.nan)
        df['valor_m2'] = df['Valor comercial'] / areas_limpias

    # Validación lógica: Flag de error en áreas
    if 'Area total' in df.columns and 'Area privada' in df.columns:
        df['error_area'] = df['Area privada'] > df['Area total']

    return df