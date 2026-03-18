import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")

if not API_URL or not API_KEY:
    raise ValueError("API_URL o API_KEY no están definidas en el .env")


def extraer_pdf_con_api(pdf_path):

    try:
        with open(pdf_path, "rb") as f:

            response = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}"
                },
                files={"file": f},
                timeout=30
            )

    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión con API: {e}")

    if response.status_code != 200:
        raise Exception(f"Error API: {response.text}")

    try:
        return response.json()
    except ValueError:
        raise Exception("La API no devolvió un JSON válido")


def obtener_archivos_procesados(ruta_dataset):

    if not os.path.exists(ruta_dataset):
        return set()

    df = pd.read_excel(ruta_dataset)

    if "archivo_origen" not in df.columns:
        return set()

    return set(df["archivo_origen"].dropna().unique())


def obtener_pdfs_nuevos(carpeta_pdf, procesados):

    archivos = os.listdir(carpeta_pdf)

    nuevos = [
        f for f in archivos
        if f.lower().endswith(".pdf") and f not in procesados
    ]

    return nuevos