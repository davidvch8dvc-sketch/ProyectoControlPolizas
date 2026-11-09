"""services/generador_aviso.py - Genera el PDF de aviso de renovación con fpdf2."""

from datetime import date
from pathlib import Path

from fpdf import FPDF

# Colores del diseño (según AGENTS.md)
ROJO = (174, 24, 0)      # #AE1800
NEGRO = (32, 30, 29)     # #201E1D
GRIS_CLARO = (243, 242, 242)  # #F3F2F2
GRIS_TEXTO = (120, 120, 120)  # gris para pie de página


def _to_latin1(texto):
    """Convierte texto a latin-1 para que las tildes no fallen en Helvetica."""
    if texto is None:
        return ""
    return str(texto).encode("latin-1", errors="replace").decode("latin-1")


def _fecha_str(fecha):
    """Formatea una fecha a dd/mm/aaaa o devuelve cadena vacía si es None."""
    if fecha is None:
        return ""
    if isinstance(fecha, date):
        return fecha.strftime("%d/%m/%Y")
    return str(fecha)


def _moneda_str(valor):
    """Devuelve el monto formateado o 'No registrada' si es None."""
    if valor is None:
        return "No registrada"
    return f"CRC {valor:,.2f}"


def crear_aviso_pdf(poliza):
    """Crea un aviso de renovación de póliza en PDF (A4 vertical) y lo devuelve en bytes.

    Recibe un diccionario con los campos de la póliza (numero, aseguradora, ramo,
    nombre, cedula, desde, hasta, prima, pago, asesor, estado, dias).
    """
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ----------------------------------------------------------------
    # Banda superior roja
    # ----------------------------------------------------------------
    pdf.set_fill_color(*ROJO)
    pdf.rect(0, 0, pdf.w, 30, style="F")

    pdf.set_xy(10, 8)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 6, _to_latin1("Corredora de Seguros Horizonte"), ln=True, align="L")

    pdf.set_xy(10, 16)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 6, _to_latin1("Aviso de renovación de póliza"), ln=True, align="L")

    pdf.set_y(36)

    # ----------------------------------------------------------------
    # Saludo
    # ----------------------------------------------------------------
    pdf.set_text_color(*NEGRO)
    pdf.set_font("Helvetica", "", 11)
    nombre = poliza.get("nombre") or "Cliente"
    pdf.cell(0, 7, _to_latin1(f"Estimado(a) {nombre}:"), ln=True)
    pdf.ln(4)

    # ----------------------------------------------------------------
    # Párrafo según estado
    # ----------------------------------------------------------------
    estado = poliza.get("estado")
    dias = poliza.get("dias")
    hasta = poliza.get("hasta")

    pdf.set_font("Helvetica", "", 11)
    if estado == "Vencida":
        fecha_venc = _fecha_str(hasta)
        pdf.multi_cell(
            0, 6,
            _to_latin1(
                f"Su póliza {poliza.get('numero')} venció el {fecha_venc}. "
                f"Por favor, comuníquese con su asesor para renovarla lo antes posible."
            ),
        )
    elif estado == "Por vencer":
        fecha_vence = _fecha_str(hasta)
        pdf.multi_cell(
            0, 6,
            _to_latin1(
                f"Su póliza {poliza.get('numero')} vence el {fecha_vence} "
                f"en {dias} días. Su asesor se comunicará con usted para coordinar la renovación."
            ),
        )
    else:
        pdf.multi_cell(
            0, 6,
            _to_latin1(
                f"Su póliza {poliza.get('numero')} se encuentra vigente. "
                f"Este aviso es informativo."
            ),
        )
    pdf.ln(6)

    # ----------------------------------------------------------------
    # Tabla de datos de la póliza
    # ----------------------------------------------------------------
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(*GRIS_CLARO)

    ancho_col_etiqueta = 55
    ancho_col_valor = pdf.w - 20 - ancho_col_etiqueta

    filas = [
        ("Número de póliza", poliza.get("numero") or ""),
        ("Aseguradora", poliza.get("aseguradora") or ""),
        ("Ramo", poliza.get("ramo") or ""),
        ("Cédula", poliza.get("cedula") or ""),
        ("Vigencia", f"{_fecha_str(poliza.get('desde'))} al {_fecha_str(poliza.get('hasta'))}"),
        ("Prima anual", _moneda_str(poliza.get("prima"))),
        ("Forma de pago", poliza.get("pago") or ""),
    ]

    for etiqueta, valor in filas:
        pdf.set_x(10)
        pdf.set_fill_color(*GRIS_CLARO)
        pdf.cell(ancho_col_etiqueta, 7, _to_latin1(etiqueta), border=1, fill=True)
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(ancho_col_valor, 7, _to_latin1(valor), border=1, ln=True)

    pdf.ln(8)

    # ----------------------------------------------------------------
    # Pie de página gris
    # ----------------------------------------------------------------
    pdf.set_y(-20)
    pdf.set_fill_color(*GRIS_CLARO)
    pdf.rect(0, pdf.h - 15, pdf.w, 15, style="F")
    pdf.set_xy(10, pdf.h - 12)
    pdf.set_text_color(*GRIS_TEXTO)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(
        0, 4,
        _to_latin1(
            "Documento ficticio con fines académicos. "
            "No tiene validez legal ni comercial."
        ),
        align="L",
    )

    # ----------------------------------------------------------------
    # Salida en bytes
    # ----------------------------------------------------------------
    salida = pdf.output(dest="S")
    if isinstance(salida, str):
        return salida.encode("latin-1")
    return bytes(salida)
