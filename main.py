import os
import pandas as pd
from ETL.Extract import extraer_datos_pdf
from ETL.Transform import transformar_a_diccionario, crear_dataframe, limpiar_y_enriquecer_dataset

def normalizar_id(val):
    """
    Limpia el ID para evitar duplicados por formato (científico, decimales, etc.)
    """
    if val is None:
        return ""
    return str(val).strip().replace('.0', '')

def ejecutar_proceso():
    # 1. CONFIGURACIÓN DE RUTAS
    ruta_entrada = "data/pdf_originales"
    ruta_salida = "data/data_procesada/Dataset_avaluos_final.xlsx"
    
    df_existente = pd.DataFrame()
    ids_procesados = set()
    
    # 2. CARGAR DATOS PREVIOS
    if os.path.exists(ruta_salida):
        try:
            df_existente = pd.read_excel(ruta_salida)
            if 'ID avaluo' in df_existente.columns:
                ids_procesados = set(
                    df_existente['ID avaluo'].apply(normalizar_id).unique()
                )
                print(f"[*] Registros previos en Excel: {len(ids_procesados)}")
        except Exception as e:
            print(f"[!] Aviso: No se pudo leer el archivo previo: {e}")

    # 3. ESCANEAR CARPETA DE PDFS
    if not os.path.exists(ruta_entrada):
        print(f"[!] Error: La carpeta {ruta_entrada} no existe.")
        return

    archivos = [f for f in os.listdir(ruta_entrada) if f.lower().endswith('.pdf')]
    nuevos_datos = []

    print(f"[*] Escaneando {len(archivos)} archivos...")

    for archivo in archivos:
        ruta_completa = os.path.join(ruta_entrada, archivo)
        matriz = extraer_datos_pdf(ruta_completa)
        
        if matriz:
            diccionario = transformar_a_diccionario(matriz)
            id_actual = normalizar_id(diccionario.get('ID avaluo'))
            
            # Validación de duplicados y existencia de ID
            if not id_actual:
                print(f"[?] Saltando {archivo}: Sin ID válido.")
                continue
                
            if id_actual in ids_procesados:
                # Opcional: print(f"[-] Saltando {archivo}: Ya existe.")
                continue
            
            print(f"[+] Extrayendo: {archivo} (ID: {id_actual})")
            nuevos_datos.append(diccionario)
            ids_procesados.add(id_actual)
        else:
            print(f"[!] Error en extracción: {archivo}")

    # 4. CONSOLIDACIÓN, LIMPIEZA Y GUARDADO
    if nuevos_datos or not df_existente.empty:
        # Unir nuevos con existentes
        if nuevos_datos:
            df_nuevos = crear_dataframe(nuevos_datos)
            df_final = pd.concat([df_existente, df_nuevos], ignore_index=True)
        else:
            df_final = df_existente
            
        # APLICAR LIMPIEZA PROFUNDA (Transform.py)
        print("[*] Aplicando limpieza profunda y reglas de negocio...")
        df_final = limpiar_y_enriquecer_dataset(df_final)
        
        # Guardar resultado
        os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
        with pd.ExcelWriter(ruta_salida, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False)
            
        print(f"\n==========================================")
        print(f"PROCESO TERMINADO")
        print(f"Nuevos registros: {len(nuevos_datos)}")
        print(f"Total en Dataset: {len(df_final)}")
        print(f"==========================================")
    else:
        print("\n[i] No hay datos para procesar.")

if __name__ == "__main__":
    ejecutar_proceso()