import re

# 🔹 Estructura oficial del dataset
CAMPOS = [
    "Entidad avaluadora", "ID avaluo", "Perito",
    "Nombre solicitante", "ID solicitante", "Fecha avaluo",
    "Departamento", "Ciudad", "Codigo DANE", "Direccion",
    "Nombre edificio", "Barrio", "Estrato", "Tipo inmueble",
    "Año construccion", "Vetustez", "Piso numero",
    "Total Sala comedor", "Total habitaciones", "Total estudio",
    "Total baños", "Total patios", "Total balcon",
    "Total terrazas", "Total garajes", "Tipo garaje",
    "Total depositos", "Estado acabados", "Estado inmueble",
    "Porteria", "Juegos niños", "Citofono",
    "Total ascensores", "Salon comunal", "Bicicletero",
    "Piscina", "Club house", "Zonas verdes",
    "Parquedadero visitantes", "Arborización",
    "Area privada", "Valor catastral", "Valor comercial",
    "archivo_origen"
]

# 🔹 Campos numéricos
CAMPOS_NUMERICOS = [
    "Estrato", "Año construccion", "Vetustez", "Piso numero",
    "Total Sala comedor", "Total habitaciones", "Total estudio",
    "Total baños", "Total patios", "Total balcon",
    "Total terrazas", "Total garajes", "Total depositos",
    "Total ascensores",
    "Area privada", "Valor catastral", "Valor comercial"
]

# 🔹 Campos booleanos
CAMPOS_BOOLEANOS = [
    "Porteria", "Juegos niños", "Citofono",
    "Salon comunal", "Bicicletero", "Piscina",
    "Club house", "Zonas verdes",
    "Parquedadero visitantes", "Arborización"
]


# 🔹 1. Normalizar claves (por si la API devuelve variaciones)
def normalizar_claves(datos):

    claves_limpias = {}

    for k, v in datos.items():
        k_limpio = k.strip().lower()
        claves_limpias[k_limpio] = v

    return claves_limpias


# 🔹 2. Mapear a estructura oficial
def estructurar_datos(datos):

    datos_norm = normalizar_claves(datos)

    resultado = {}

    for campo in CAMPOS:
        campo_norm = campo.lower()

        valor = datos_norm.get(campo_norm, None)
        resultado[campo] = valor

    return resultado


# 🔹 3. Limpieza general
def limpiar_texto(valor):

    if valor is None:
        return None

    valor = str(valor).strip()

    # eliminar espacios múltiples
    valor = re.sub(r"\s+", " ", valor)

    return valor


# 🔹 4. Limpieza específica (dinero)
def limpiar_numero(valor):

    if valor is None:
        return None

    valor = str(valor)

    # quitar símbolos
    valor = valor.replace("$", "").replace(".", "").replace(",", "")

    # dejar solo números
    valor = re.sub(r"[^\d]", "", valor)

    return valor


# 🔹 5. Convertir tipos
def convertir_tipos(datos):

    for campo in CAMPOS_NUMERICOS:

        valor = datos.get(campo)

        if valor is None or valor == "":
            datos[campo] = None
            continue

        limpio = limpiar_numero(valor)

        try:
            datos[campo] = float(limpio)
        except:
            datos[campo] = None

    return datos


# 🔹 6. Convertir booleanos
def convertir_booleanos(datos):

    for campo in CAMPOS_BOOLEANOS:

        valor = datos.get(campo)

        if valor is None:
            continue

        valor_str = str(valor).lower()

        if valor_str in ["1", "si", "sí", "true"]:
            datos[campo] = 1
        else:
            datos[campo] = 0

    return datos


# 🔹 7. Limpieza final
def limpiar_datos(datos):

    for k, v in datos.items():

        if k not in CAMPOS_NUMERICOS:
            datos[k] = limpiar_texto(v)

    return datos


# 🔹 FUNCIÓN PRINCIPAL
def transformar_datos(datos_raw, archivo_origen):

    datos = estructurar_datos(datos_raw)

    datos = limpiar_datos(datos)

    datos = convertir_tipos(datos)

    datos = convertir_booleanos(datos)

    # agregar archivo origen
    datos["archivo_origen"] = archivo_origen

    return datos