import os
import pandas as pd
import logging
from datetime import datetime

# 🔹 Módulos del proyecto
from Extract_api import (
    extraer_pdf_con_api,
    obtener_archivos_procesados,
    obtener_pdfs_nuevos
)

from Transform import transformar_datos
from validate import validar_datos


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


# 🔹 PROCESO PRINCIPAL
def main():

    logging.info("Inicio del proceso")

    try:
        # 🔹 Identificar PDFs nuevos
        procesados = obtener_archivos_procesados(RUTA_DATASET)
        nuevos_pdfs = obtener_pdfs_nuevos(RUTA_PDFS, procesados)

        if not nuevos_pdfs:
            logging.info("No hay PDFs nuevos para procesar")
            print("✔ Todo está actualizado")
            return

        logging.info(f"{len(nuevos_pdfs)} PDFs nuevos encontrados")

        resultados = []

        for archivo in nuevos_pdfs:

            ruta_pdf = os.path.join(RUTA_PDFS, archivo)

            try:
                logging.info(f"Iniciando procesamiento: {archivo}")

                # 🔹 EXTRACT
                datos_raw = extraer_pdf_con_api(ruta_pdf)

                # 🔹 TRANSFORM
                datos_limpios = transformar_datos(datos_raw, archivo)

                # 🔹 VALIDATE
                df_temp = pd.DataFrame([datos_limpios])
                validar_datos(df_temp)

                resultados.append(datos_limpios)

                logging.info(
                    f"{archivo} | OK | "
                    f"Valor: {datos_limpios.get('Valor comercial')} | "
                    f"Área: {datos_limpios.get('Area total')}"
                )

                print(f"✔ {archivo} procesado")

            except Exception as e:
                logging.error(f"Error en {archivo}: {str(e)}")
                print(f"✖ Error en {archivo}")

        # 🔹 LOAD (una sola escritura eficiente)
        if resultados:

            df_nuevo = pd.DataFrame(resultados)

            if os.path.exists(RUTA_DATASET):
                df_existente = pd.read_excel(RUTA_DATASET)
                df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
            else:
                df_final = df_nuevo

            df_final.to_excel(RUTA_DATASET, index=False)

            logging.info(f"Datos guardados correctamente. Total nuevos registros: {len(df_nuevo)}")

        logging.info("Proceso finalizado correctamente")

    except Exception as e:
        logging.critical(f"Error crítico en el pipeline: {str(e)}")
        print("✖ Error crítico en el pipeline")


# 🔹 EJECUCIÓN
if __name__ == "__main__":
    main()

# --- IGNORE ---
# Este código es el punto de entrada del pipeline ETL. Se encarga de:
# 1. Configurar rutas y logging.
# 2. Identificar qué PDFs son nuevos y necesitan ser procesados.
# 3. Por cada PDF nuevo, ejecutar las etapas de Extract, Transform y Validate.
# 4. Al final, guardar todos los nuevos registros en un solo paso para optimizar
#    la escritura en disco.
# 5. Manejar errores de forma robusta y registrar toda la actividad en logs detall
#    para facilitar la depuración y el monitoreo del proceso.

# Para ejecutar este script, asegúrate de tener las dependencias instaladas y el 
# archivo .env configurado con las variables API_URL y API_KEY. Luego, puedes correrlo con:
# ============================
# ==== poetry run main.py ====
# ============================