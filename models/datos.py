"""models/datos.py - Único lugar que abre archivos del proyecto (Excel y PDF)."""

from pathlib import Path
from datetime import datetime

import pandas as pd
import pdfplumber

# Carpeta de datos (solo lectura)
# En Render (Linux) no existe el junction "data/", por lo que usamos la ruta real.
DATA_DIR = Path("Insumos_Control_Polizas")
CLIENTES_XLSX = DATA_DIR / "Maestro_Clientes.xlsx"
POLIZAS_DIR = DATA_DIR / "polizas"

# Diccionario: etiqueta del PDF -> nombre del campo interno
CAMPOS = {
    "Numero de poliza": "numero",
    "Ramo": "ramo",
    "Tomador / Asegurado": "nombre",
    "Cedula": "cedula",
    "Vigencia desde": "desde",
    "Vigencia hasta": "hasta",
    "Prima anual": "prima",
    "Forma de pago": "pago",
    "Suma asegurada": "suma",
    "Asesor": "asesor",
}


def _texto_a_fecha(texto):
    """Convierte una cadena en formato dd/mm/aaaa a objeto date.
    Devuelve None si el texto está vacío o no es una fecha válida."""
    if not texto or not str(texto).strip():
        return None
    texto = str(texto).strip()
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        return None


def _texto_a_numero(texto):
    """Convierte un monto como "CRC 228,000.00" a número (float).
    Devuelve None si el texto está vacío o no se puede convertir."""
    if not texto or not str(texto).strip():
        return None
    texto = str(texto).strip()
    # Quitar símbolos de moneda y espacios
    texto = texto.replace("CRC", "").replace("USD", "").replace("$", "").strip()
    try:
        # Si tiene coma y punto: "228,000.00" -> quitar coma de miles
        if "," in texto and "." in texto:
            texto = texto.replace(",", "")
        elif "," in texto:
            # Podría ser decimal europeo "228,00" o miles "228,000"
            partes = texto.split(",")
            if len(partes[-1]) == 2:
                texto = texto.replace(",", ".")
            else:
                texto = texto.replace(",", "")
        return float(texto)
    except ValueError:
        return None


def cargar_clientes():
    """Lee data/Maestro_Clientes.xlsx (hoja Clientes) con pandas.
    Devuelve el DataFrame con la columna Cedula como texto sin espacios."""
    df = pd.read_excel(CLIENTES_XLSX, sheet_name="Clientes")
    df["Cedula"] = df["Cedula"].astype(str).str.strip()
    return df


def leer_poliza(ruta_pdf):
    """Abre un PDF con pdfplumber, toma el texto de la primera página y devuelve
    un diccionario con: archivo, aseguradora, numero, ramo, nombre, cedula,
    desde, hasta, prima, pago, suma, asesor."""
    ruta = Path(ruta_pdf)

    diccionario = {
        "archivo": ruta.name,
        "aseguradora": "",
        "numero": None,
        "ramo": None,
        "nombre": None,
        "cedula": None,
        "desde": None,
        "hasta": None,
        "prima": None,
        "pago": None,
        "suma": None,
        "asesor": None,
    }

    with pdfplumber.open(ruta) as pdf:
        pagina = pdf.pages[0]
        texto = pagina.extract_text() or ""

    lineas = texto.split("\n")

    if not lineas:
        return diccionario

    # Primera línea del texto es el nombre de la aseguradora
    diccionario["aseguradora"] = lineas[0].strip()

    # Recorrer las demás líneas con un bucle
    for linea in lineas[1:]:
        linea = linea.strip()
        if ":" not in linea:
            continue
        etiqueta, valor = linea.split(":", 1)
        etiqueta = etiqueta.strip()
        valor = valor.strip()

        if etiqueta in CAMPOS:
            campo = CAMPOS[etiqueta]
            if campo in ("desde", "hasta"):
                diccionario[campo] = _texto_a_fecha(valor)
            elif campo in ("prima", "suma"):
                diccionario[campo] = _texto_a_numero(valor)
            else:
                diccionario[campo] = valor

    return diccionario


def cargar_polizas():
    """Recorre data/polizas en orden alfabético y devuelve una lista con
    el diccionario de cada PDF."""
    polizas = []
    archivos = sorted(POLIZAS_DIR.glob("*.pdf"))
    for archivo in archivos:
        polizas.append(leer_poliza(archivo))
    return polizas
