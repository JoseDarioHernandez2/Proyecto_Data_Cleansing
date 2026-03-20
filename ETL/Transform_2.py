import pandas as pd
import numpy as np

def agregar_rango_precios(df, columna_objetivo='Valor comercial'):
    """
    Agrega la variable 'Rango precios' categorizada y ordenada.
    """
    bins = [0, 280_000_000, 460_000_000, 730_000_000, 1_100_000_000, 1_800_000_000, np.inf]
    labels = [
        'VIS', 
        'Confort Medio', 
        'Confort Familiar', 
        'Alto Confort', 
        'Confort Lujo', 
        'Premium Confort Lujo'
    ]
    
    df['Rango precios'] = pd.cut(
        df[columna_objetivo], 
        bins=bins, 
        labels=labels, 
        include_lowest=True
    )
    
    df['Rango precios'] = pd.Categorical(
        df['Rango precios'], 
        categories=labels, 
        ordered=True
    )
    return df

def imputar_datos_globales(df):
    """
    Etapa 2 de Transformación: Inteligencia Colectiva y Segmentación.
    """
    print("\n🧠 [Transform_2] Iniciando procesamiento global...")
    
    ANIO_ACTUAL = 2026 

    # A. Limpieza de tipos
    columnas_num = ["Area total", "Area privada", "Valor comercial", "Valor catastral", "Valor m2", "Estrato", "Año construccion", "Vetustez"]
    for col in columnas_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # B. Regla Año Construcción (Año = 2026 - Vetustez)
    mask_anio = (df["Año construccion"] < 1850) & (df["Vetustez"] > 0)
    if mask_anio.any():
        print(f"   -> Corrigiendo {mask_anio.sum()} registros de 'Año construccion'...")
        df.loc[mask_anio, "Año construccion"] = (ANIO_ACTUAL - df.loc[mask_anio, "Vetustez"]).astype(int)

    # C. Imputación de Áreas
    df_ref_areas = df[df["Area total"] > 0].copy()
    if not df_ref_areas.empty:
        ref_a1 = df_ref_areas.groupby(["Estrato", "numero de zonas inmueble"])[["Area total", "Area privada"]].median()
        ref_a2 = df_ref_areas.groupby(["Estrato"])[["Area total", "Area privada"]].median()
        ref_a3 = df_ref_areas[["Area total", "Area privada"]].median()

        def buscar_area(row, col):
            try:
                v = ref_a1.loc[(row["Estrato"], row["numero de zonas inmueble"]), col]
                if pd.notna(v) and v > 0: return v
            except: pass
            try:
                v = ref_a2.loc[row["Estrato"], col]
                if pd.notna(v) and v > 0: return v
            except: pass
            return ref_a3[col]

        for col in ["Area total", "Area privada"]:
            mask = (df[col] == 0)
            if mask.any():
                df.loc[mask, col] = df[mask].apply(lambda r: buscar_area(r, col), axis=1)

    # D. Imputación de Precios y Catastro
    UMBRAL_PRECIO = 10000000
    df_ref_precios = df[df["Valor comercial"] > UMBRAL_PRECIO].copy()

    if not df_ref_precios.empty:
        tabla_m2_estrato = df_ref_precios.groupby("Estrato")["Valor m2"].mean()
        promedio_m2_global = df_ref_precios["Valor m2"].mean()

        # Reconstruir Valor Comercial
        mask_comercial = (df["Valor comercial"] <= UMBRAL_PRECIO)
        if mask_comercial.any():
            df.loc[mask_comercial, "Valor comercial"] = df[mask_comercial].apply(
                lambda r: int(r["Area total"] * tabla_m2_estrato.get(r["Estrato"], promedio_m2_global)), axis=1
            )

        # Ajustar Valor Catastral (45%)
        mask_catastral = (df["Valor catastral"] <= UMBRAL_PRECIO)
        if mask_catastral.any():
            df.loc[mask_catastral, "Valor catastral"] = (df.loc[mask_catastral, "Valor comercial"] * 0.45).astype(int)

        # Recalcular m2
        df["Valor m2"] = (df["Valor comercial"] / df["Area total"].replace(0, np.nan)).fillna(0).round(2)

    # --- NUEVO PASO: SEGMENTACIÓN ---
    print("   -> Clasificando registros por 'Rango precios'...")
    df = agregar_rango_precios(df)

    print("✅ [Transform_2] Todo normalizado y segmentado.")
    return df