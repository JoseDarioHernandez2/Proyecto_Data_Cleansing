import os
import pandas as pd
import logging
from datetime import datetime

# Importar tus módulos
from extract_ai_api import (
    extraer_pdf_con_api,
    obtener_archivos_procesados,
    obtener_pdfs_nuevos
)

from transform import transformar_datos


# 🔹 CONFIGURACIÓN DE RUTAS
RUTA_PDFS = "data/pdf_originales"
RUTA_DATASET = "data/data_procesada/dataset_avaluos_final.xlsx"
RUTA_LOGS = "logs"

os.makedirs(RUTA_LOGS, exist_ok=True)

# 🔹 CONFIGURAR LOGS
log_file = os.path.join(
    RUTA_LOGS,
    f"proceso_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# 🔹 GUARDAR DATOS
def guardar_datos(datos, ruta):

    df_nuevo = pd.DataFrame([datos])

    if os.path.exists(ruta):
        df_existente = pd.read_excel(ruta)
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    else:
        df_final = df_nuevo

    df_final.to_excel(ruta, index=False)


# 🔹 PROCESO PRINCIPAL
def main():

    logging.info("Inicio del proceso")

    try:
        procesados = obtener_archivos_procesados(RUTA_DATASET)
        nuevos_pdfs = obtener_pdfs_nuevos(RUTA_PDFS, procesados)

        if not nuevos_pdfs:
            logging.info("No hay PDFs nuevos para procesar")
            print("✔ Todo está actualizado")
            return

        logging.info(f"{len(nuevos_pdfs)} PDFs nuevos encontrados")

        for archivo in nuevos_pdfs:

            ruta_pdf = os.path.join(RUTA_PDFS, archivo)

            try:
                logging.info(f"Procesando: {archivo}")

                # 🔹 EXTRACT
                datos_raw = extraer_pdf_con_api(ruta_pdf)

                # 🔹 TRANSFORM
                datos_limpios = transformar_datos(datos_raw, archivo)

                # 🔹 LOAD
                guardar_datos(datos_limpios, RUTA_DATASET)

                logging.info(f"Procesado correctamente: {archivo}")
                print(f"✔ {archivo} procesado")

            except Exception as e:
                logging.error(f"Error procesando {archivo}: {str(e)}")
                print(f"✖ Error en {archivo}")

        logging.info("Proceso finalizado")

    except Exception as e:
        logging.critical(f"Error crítico: {str(e)}")
        print("✖ Error crítico en el pipeline")


# 🔹 EJECUCIÓN
if __name__ == "__main__":
    main()