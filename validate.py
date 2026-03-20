import logging

def validar_datos(df):
    """
    Revisa la calidad de los datos transformados.
    """
    logging.info("Iniciando validación de negocio...")

    if df.empty:
        logging.warning("El dataframe está vacío.")
        return

    # Validar valores comerciales en 0
    if "Valor comercial" in df.columns:
        en_cero = df[df["Valor comercial"] <= 0].shape[0]
        if en_cero > 0:
            logging.warning(f"⚠️ {en_cero} registros tienen Valor comercial en 0.")

    # Validar áreas sospechosas
    if "Area total" in df.columns:
        areas_raras = df[df["Area total"] < 5].shape[0]
        if areas_raras > 0:
            logging.warning(f"⚠️ {areas_raras} registros tienen áreas sospechosamente pequeñas.")

    # Validar duplicados de ID avaluo (por si acaso)
    if "ID avaluo" in df.columns:
        dups = df.duplicated(subset=["ID avaluo"]).sum()
        if dups > 0:
            logging.error(f"❌ Se encontraron {dups} duplicados de 'ID avaluo' tras transformación.")

    logging.info("Validación finalizada.")