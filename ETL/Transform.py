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


# 🔹 4. Limpieza específica (simbolo dinero)
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

# 🔹 7. Feature Engineering
def crear_features(datos):

    # 🔹 1. Valor por metro cuadrado (SOLO Area total)
    valor = datos.get("Valor comercial")
    area = datos.get("Area total")

    if isinstance(valor, (int, float)) and isinstance(area, (int, float)) and area > 0:
        datos["Valor m2"] = valor / area
    else:
        datos["Valor m2"] = None

    # 🔹 2. Áreas por inmueble
    campos_areas = [
        "Total Sala comedor",
        "Total habitaciones",
        "Total estudio",
        "Total baños",
        "Total patios",
        "Total balcon",
        "Total terrazas",
        "Total garajes"
    ]

    suma = 0
    hay_datos = False

    for campo in campos_areas:
        val = datos.get(campo)

        if isinstance(val, (int, float)):
            suma += val
            hay_datos = True

    datos["areas por inmueble"] = suma if hay_datos else None

    return datos


# 🔹 8. Limpieza final
def limpiar_datos(datos):

    for k, v in datos.items():

        if k not in CAMPOS_NUMERICOS:
            datos[k] = limpiar_texto(v)

    return datos

# 9. validación de datos
import pandas as pd


def validar_datos(df: pd.DataFrame) -> bool:
    """
    Valida la calidad de los datos transformados antes de guardarlos.
    Lanza errores si encuentra inconsistencias críticas.
    """

    if df is None or df.empty:
        raise ValueError("El DataFrame está vacío o es None")

    # 🔹 Columnas esperadas (ajústalas según tu Transform)
    columnas_obligatorias = [
        "Valor comercial",
        "Area total",
        "Estrato",
        "Valor m2"
    ]

    for col in columnas_obligatorias:
        if col not in df.columns:
            raise ValueError(f"Falta la columna obligatoria: {col}")

    # 🔹 Validaciones de nulos
    if df["Valor comercial"].isnull().any():
        raise ValueError("Hay valores nulos en 'Valor comercial'")

    if df["Area total"].isnull().any():
        raise ValueError("Hay valores nulos en 'Area total'")

    # 🔹 Validaciones de rango lógico
    if (df["Valor comercial"] <= 0).any():
        raise ValueError("Hay valores <= 0 en 'Valor comercial'")

    if (df["Area total"] <= 0).any():
        raise ValueError("Hay valores <= 0 en 'Area total'")

    if (df["valor_m2"] <= 0).any():
        raise ValueError("Hay valores <= 0 en 'valor_m2'")

    # 🔹 Estrato (valores típicos en Colombia: 1–6)
    if df["Estrato"].notnull().any():
        estratos_invalidos = df[
            ~df["Estrato"].isin([1, 2, 3, 4, 5, 6])
        ]

        if not estratos_invalidos.empty:
            raise ValueError("Hay valores inválidos en 'Estrato'")

    return True


# 🔹 FUNCIÓN PRINCIPAL
def transformar_datos(datos_raw, archivo_origen):
    # El orden de las funciones
    datos = estructurar_datos(datos_raw)
    # datos = normalizar_claves(datos_raw) # ya se hace dentro de estructurar_datos
    datos = limpiar_datos(datos)
    # convertir tipos antes de crear features, porque algunas features dependen de los tipos numéricos
    datos = convertir_tipos(datos)
    # convertir booleanos después de convertir tipos, para evitar conflictos
    datos = convertir_booleanos(datos) 
    # 🔥 Feature Engineering
    datos = crear_features(datos)
    # 🔥 Validación de datos
    validar_datos(pd.DataFrame([datos]))
    # agregar archivo origen
    datos["archivo_origen"] = archivo_origen

    return datos