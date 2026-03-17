import pdfplumber

def extraer_datos_pdf(ruta_pdf):
    datos_crudos = []
    with pdfplumber.open(ruta_pdf) as pdf:
        pagina = pdf.pages[0]
        # Usamos table_settings para detectar tablas basadas en las líneas visibles del formulario
        tabla = pagina.extract_table({
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
        })
        if tabla:
            datos_crudos = tabla
    return datos_crudos