import os
import shutil
import time
import json
import pandas as pd
import google.generativeai as genai


class ProcesadorAvaluos:
    """
    Clase encargada de gestionar la extracción de datos de PDFs inmobiliarios
    utilizando la API multimodal de Google Gemini.

    Flujo:
      - Extrae datos de cada PDF mediante Gemini
      - Guarda/acumula resultados en Base_Datos_Avaluos.xlsx (archivo raw)
      - No permite duplicados por 'ID avaluo' en el archivo raw
      - Mueve cada PDF procesado a la carpeta de procesados
    """

    def __init__(
        self,
        api_key,
        carpeta_pendientes="data\\pdf_pendientes",
        carpeta_procesados="data\\pdf_procesados",
        carpeta_salida="data\\data_extraida",
    ):
        self.carpeta_pendientes = carpeta_pendientes
        self.carpeta_procesados = carpeta_procesados
        self.carpeta_salida = carpeta_salida
        self.nombre_excel = os.path.join(self.carpeta_salida, "Base_Datos_Avaluos.xlsx")

        os.makedirs(self.carpeta_pendientes, exist_ok=True)
        os.makedirs(self.carpeta_procesados, exist_ok=True)
        os.makedirs(self.carpeta_salida, exist_ok=True)

        genai.configure(api_key=api_key)
        self.nombre_del_modelo = "gemini-2.5-flash-lite"
        self.modelo = genai.GenerativeModel(self.nombre_del_modelo)

        print(f"✅ Inicializado ProcesadorAvaluos con modelo: {self.nombre_del_modelo}")
        print(f"📁 Archivo raw: {self.nombre_excel}")

    def _obtener_instruccion(self):
        """Retorna el prompt estricto para la extracción de datos."""
        return """
        Eres un experto analista de datos inmobiliarios con atención meticulosa al detalle.
        Tu tarea es observar el documento PDF adjunto y extraer la información solicitada con precisión absoluta.

        REGLAS ESTRICTAS DE EXTRACCIÓN:
        1. "Nombre solicitante": Extrae SOLO el nombre del cliente que solicita el avalúo. NUNCA lo confundas con el Perito.
        2. "ID solicitante": Extrae únicamente los números del documento de identidad.
        3. "Tipo inmueble": Responde EXCLUSIVAMENTE "Casa" o "Apartamento".
        4. "Vetustez": Años de antigüedad del inmueble. Responde ÚNICAMENTE con el número entero.
        5. "Area total" y "Area privada": Identifica los valores numéricos. Usa SIEMPRE punto para los decimales.
        6. "Perito": Busca el nombre del profesional que realiza el avalúo.
        7. "Ciudad" y "Departamento": Busca en el encabezado, pie de página o en la sección de "Ubicación".
        8. "Barrio": Si no ves la palabra "Barrio", busca bajo los términos "Sector", "Urbanización", "Conjunto" o "Vereda".
        9. "Codigo DANE": Suele ser un número largo asociado a la ubicación.
        10. Si después de aplicar estas reglas el dato realmente no existe en el documento, responde exactamente "No encontrado".

        Devuelve la respuesta ESTRICTAMENTE en formato JSON, sin texto adicional:
        {
            "Entidad avaluadora": "respuesta aquí",
            "ID avaluo": "respuesta aquí",
            "Perito": "respuesta aquí",
            "Nombre solicitante": "respuesta aquí",
            "ID solicitante": "respuesta aquí",
            "Fecha avaluo": "respuesta aquí",
            "Departamento": "respuesta aquí",
            "Ciudad": "respuesta aquí",
            "Codigo DANE": "respuesta aquí",
            "Direccion": "respuesta aquí",
            "Nombre edificio": "respuesta aquí",
            "Barrio": "respuesta aquí",
            "Estrato": "respuesta aquí",
            "Tipo inmueble": "respuesta aquí",
            "Año construccion": "respuesta aquí",
            "Vetustez": "respuesta aquí",
            "Piso numero": "respuesta aquí",
            "Total Sala comedor": "respuesta aquí",
            "Total habitaciones": "respuesta aquí",
            "Total estudio": "respuesta aquí",
            "Total baños": "respuesta aquí",
            "Total patios": "respuesta aquí",
            "Total balcon": "respuesta aquí",
            "Total terrazas": "respuesta aquí",
            "Total garajes": "respuesta aquí",
            "Tipo garaje": "respuesta aquí",
            "Total depositos": "respuesta aquí",
            "Estado acabados": "respuesta aquí",
            "Estado inmueble": "respuesta aquí",
            "Porteria": "respuesta aquí",
            "Juegos niños": "respuesta aquí",
            "Citofono": "respuesta aquí",
            "Total ascensores": "respuesta aquí",
            "Salon comunal": "respuesta aquí",
            "Bicicletero": "respuesta aquí",
            "Piscina": "respuesta aquí",
            "Club house": "respuesta aquí",
            "Zonas verdes": "respuesta aquí",
            "Parqueadero visitantes": "respuesta aquí",
            "Arborización": "respuesta aquí",
            "Area total": "respuesta aquí",
            "Area privada": "respuesta aquí",
            "Valor catastral": "respuesta aquí",
            "Valor comercial": "respuesta aquí"
        }
        """

    def extraer_datos_pdf(self, nombre_archivo) -> dict | None:
        """
        Procesa un archivo PDF individual.
        Retorna diccionario con datos extraídos, o None si falla/ya fue procesado.
        """
        ruta_origen = os.path.join(self.carpeta_pendientes, nombre_archivo)
        ruta_destino = os.path.join(self.carpeta_procesados, nombre_archivo)

        if os.path.exists(ruta_destino):
            print(f"⏭️  {nombre_archivo} ya fue procesado anteriormente. Saltando...")
            return None

        print(f"--- Procesando: {nombre_archivo} ---")
        archivo_subido = None
        datos_extraidos = None

        try:
            archivo_subido = genai.upload_file(ruta_origen)
            instruccion = self._obtener_instruccion()

            exito = False
            intentos = 0

            while not exito and intentos < 3:
                try:
                    respuesta_ia = self.modelo.generate_content(
                        [archivo_subido, instruccion],
                        generation_config=genai.types.GenerationConfig(temperature=0.0),
                    )

                    texto_json = respuesta_ia.text.strip().replace("```json", "").replace("```", "")
                    datos_extraidos = json.loads(texto_json)

                    # Registrar el nombre del PDF de origen
                    datos_extraidos["archivo_origen"] = nombre_archivo

                    shutil.move(ruta_origen, ruta_destino)
                    print(f"✅ Extraído y movido a procesados: {nombre_archivo}")
                    exito = True

                except Exception as e_interno:
                    if "429" in str(e_interno):
                        intentos += 1
                        print(f"⚠️  Rate limit. Esperando 35s... (Intento {intentos}/3)")
                        time.sleep(35)
                    else:
                        print(f"❌ Error al parsear JSON de {nombre_archivo}: {e_interno}")
                        break

        except Exception as e:
            print(f"❌ Error general con {nombre_archivo}: {e}")

        finally:
            if archivo_subido:
                try:
                    genai.delete_file(archivo_subido.name)
                except Exception:
                    pass

        return datos_extraidos

    def guardar_en_base_raw(self, resultados: list) -> None:
        """
        Guarda los resultados extraídos en Base_Datos_Avaluos.xlsx (archivo raw).
        - Si el archivo ya existe, concatena con los datos previos.
        - Deduplica por 'ID avaluo' (keep='last') antes de guardar.
        - No aplica ninguna transformación: los datos quedan tal como los entrega Gemini.
        """
        if not resultados:
            print("⚠️  No hay resultados nuevos para guardar en la base raw.")
            return

        df_nuevos = pd.DataFrame(resultados)

        if os.path.exists(self.nombre_excel):
            df_existente = pd.read_excel(self.nombre_excel)
            df_combinado = pd.concat([df_existente, df_nuevos], ignore_index=True)
            print(f"📎 Concatenando {len(df_nuevos)} nuevos sobre {len(df_existente)} existentes...")
        else:
            df_combinado = df_nuevos
            print("✨ Creando Base_Datos_Avaluos.xlsx por primera vez...")

        # Deduplicar por ID avaluo en el archivo raw
        if "ID avaluo" in df_combinado.columns:
            df_combinado["ID avaluo"] = df_combinado["ID avaluo"].astype(str).str.strip()
            antes = len(df_combinado)
            df_combinado = df_combinado.drop_duplicates(subset=["ID avaluo"], keep="last").reset_index(drop=True)
            eliminados = antes - len(df_combinado)
            if eliminados:
                print(f"🔁 {eliminados} duplicados eliminados en base raw.")

        df_combinado.to_excel(self.nombre_excel, index=False)
        print(f"💾 Base raw guardada: '{self.nombre_excel}' — {len(df_combinado)} registros totales.")

    def iniciar_procesamiento_lote(self) -> None:
        """
        Orquesta la extracción de todos los PDFs en cola y guarda en Base_Datos_Avaluos.xlsx.
        No retorna nada — el main.py lee el archivo directamente en el paso siguiente.
        """
        archivos_en_cola = [
            f for f in os.listdir(self.carpeta_pendientes) if f.lower().endswith(".pdf")
        ]

        if not archivos_en_cola:
            print(f"📭 No hay PDFs para procesar en '{self.carpeta_pendientes}'.")
            return

        print(f"\n🚀 {len(archivos_en_cola)} PDFs en cola. Iniciando extracción...\n")

        resultados_totales = []

        for i, nombre_archivo in enumerate(archivos_en_cola):
            datos = self.extraer_datos_pdf(nombre_archivo)
            if datos:
                resultados_totales.append(datos)

            if i < len(archivos_en_cola) - 1:
                time.sleep(10)

        print(f"\n🎉 Extracción finalizada. {len(resultados_totales)} registros extraídos.")

        # Guardar en archivo raw independientemente de si hubo nuevos o no
        self.guardar_en_base_raw(resultados_totales)