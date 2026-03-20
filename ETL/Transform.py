import re
import pandas as pd
import numpy as np
from datetime import datetime

# Configuración de variables
CAMPOS_NUMERICOS = [
    "Estrato", "Año construccion", "Vetustez", "Piso numero", "Total Sala comedor",
    "Total habitaciones", "Total estudio", "Total baños", "Total patios",
    "Total balcon", "Total terrazas", "Total garajes", "Total depositos",
    "Total ascensores", "Area total", "Area privada", "Valor catastral", "Valor comercial"
]

COLUMNAS_DICOTOMICAS = [
    "Porteria", "Juegos niños", "Citofono", "Total ascensores", "Salon comunal", 
    "Bicicletero", "Piscina", "Club house", "Zonas verdes", 
    "Parqueadero visitantes", "Arborización"
]

COLUMNAS_PARA_SUMAR_ZONAS = [
    "Total Sala comedor", "Total habitaciones", "Total estudio", "Total baños",
    "Total patios", "Total balcon", "Total terrazas", "Total garajes", "Total depositos"
]

def limpiar_numero(valor):
    """Limpia strings numéricos y asegura que el valor sea float inicial."""
    if pd.isna(valor) or str(valor).strip().lower() in ["nan", "none", "", "n/a", "no encontrado"]:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    
    texto = str(valor).strip().replace("$", "").replace(" ", "")
    # Manejo de separadores: 1.234.567,89 -> 1234567.89
    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."): # Caso europeo/latino: . mil , decimal
            texto = texto.replace(".", "").replace(",", ".")
        else: # Caso gringo: , mil . decimal
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(",", ".")
        
    limpio = re.sub(r"[^\d.]", "", texto)
    try:
        return float(limpio) if limpio else 0.0
    except:
        return 0.0

def normalizar_dicotomica(valor):
    """Convierte SI/NO/NO ENCONTRADO/Números a 0 o 1."""
    v = str(valor).strip().upper()
    if v in ["SI", "1", "1.0", "EXISTE", "CONFIRMADO"]:
        return 1
    return 0

def homologar_tipo_inmueble(valor):
    v = str(valor).strip().upper()
    if any(x in v for x in ["APTO", "APARTAMENTO", "DEPARTAMENTO"]):
        return "APARTAMENTO"
    return "CASA"

def homologar_estados(valor):
    """Para Estado acabados y Estado inmueble."""
    v = str(valor).strip().upper()
    if "EXCELENTE" in v: return "EXCELENTE"
    if "REGULAR" in v: return "REGULAR"
    return "BUENO" # Default para BUENO, USADA, BUEN ESTADO, etc.

def limpiar_fecha(fecha_raw):
    fecha_str = str(fecha_raw).strip().lower()
    if fecha_str in ["nan", "none", "", "n/a", "no encontrado", "0"]:
        return "SIN INFORMACION"
    meses = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04", 
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08", 
        "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
    }
    try:
        for mes_nombre, mes_num in meses.items():
            if mes_nombre in fecha_str:
                fecha_str = fecha_str.replace(mes_nombre, mes_num).replace(" de ", "-")
        fecha_str = fecha_str.replace("/", "-").replace(".", "-").replace(" ", "-")
        dt = pd.to_datetime(fecha_str, dayfirst=True, errors='coerce')
        return dt.strftime('%d-%m-%Y') if not pd.isna(dt) else "SIN INFORMACION"
    except:
        return "SIN INFORMACION"

def corregir_coherencia_garajes(total_garajes, tipo_garaje_raw):
    total = float(total_garajes)
    tipo_raw = str(tipo_garaje_raw).upper()
    if total == 0: return 0
    if any(x in tipo_raw for x in ["CUBIERTO", "PRIVADO"]): return 1
    if any(x in tipo_raw for x in ["DESCUBIERTO", "LINEAL", "COMUN"]): return 2
    return 1

# =================================================
# ==== FUNCIÓN PRINCIPAL DE TRANSFORMACIÓN =======
# =================================================

def transformar_datos(datos_dict, archivo_origen):
    df = pd.DataFrame([datos_dict])
    df.columns = [str(c).strip() for c in df.columns]
    
    # 1. Procesar Numéricos Iniciales
    for col in CAMPOS_NUMERICOS:
        val = df[col].iloc[0] if col in df.columns else 0.0
        df[col] = limpiar_numero(val)

    # 2. Homologar Tipo Inmueble (Punto 1)
    if "Tipo inmueble" in df.columns:
        df["Tipo inmueble"] = df["Tipo inmueble"].apply(homologar_tipo_inmueble)

    # 3. Homologar Estados (Puntos 2 y 3)
    for col in ["Estado acabados", "Estado inmueble"]:
        if col in df.columns:
            df[col] = df[col].apply(homologar_estados)

    # 4. Normalizar Dicotómicas (Punto 4)
    for col in COLUMNAS_DICOTOMICAS:
        if col in df.columns:
            df[col] = df[col].apply(normalizar_dicotomica)

    # 5. Estandarizar Valor Comercial a ENTERO (Punto 5)
    # Se redondea para no perder decimales por truncamiento y luego se pasa a int
    df["Valor comercial"] = df["Valor comercial"].round().astype(int)

    # 6. Reglas de Negocio (Garajes y Fechas)
    total_g = df["Total garajes"].iloc[0]
    tipo_g_raw = df["Tipo garaje"].iloc[0] if "Tipo garaje" in df.columns else "SIN INFORMACION"
    df["Tipo garaje"] = corregir_coherencia_garajes(total_g, tipo_g_raw)
    
    fecha_raw = df["Fecha avaluo"].iloc[0] if "Fecha avaluo" in df.columns else "SIN INFORMACION"
    df["Fecha avaluo"] = limpiar_fecha(fecha_raw)

    # 7. Sumar zonas
    cols_suma = [c for c in COLUMNAS_PARA_SUMAR_ZONAS if c in df.columns]
    df["numero de zonas inmueble"] = df[cols_suma].sum(axis=1)

    # 8. Procesar Textos Restantes
    cols_obj = df.select_dtypes(exclude=[np.number]).columns
    for col in cols_obj:
        if col == "Fecha avaluo": continue
        df[col] = df[col].astype(str).str.strip().str.upper()
        df[col] = df[col].replace(["NAN", "NONE", "N/A", "0", "NO ENCONTRADO"], "SIN INFORMACION")

    # 9. Valor m2
    area = df["Area total"].iloc[0] if df["Area total"].iloc[0] > 0 else df["Area privada"].iloc[0]
    df["Valor m2"] = (df["Valor comercial"].iloc[0] / area) if area > 0 else 0.0
    
    df["archivo_origen"] = archivo_origen
    return df.iloc[0].to_dict()