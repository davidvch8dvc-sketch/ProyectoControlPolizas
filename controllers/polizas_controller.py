"""controllers/polizas_controller.py - Rutas de Flask (Blueprint).

No calcula nada: solo llama a models/ y services/.
"""

import io
import os
import zipfile
from pathlib import Path

from flask import (
    Blueprint,
    render_template,
    send_file,
    abort,
    request,
    session,
    redirect,
    url_for,
    flash,
)
from werkzeug.utils import secure_filename

from models.polizas import (
    calcular_resultados,
    contar_por_estado,
    primas_por_aseguradora,
    buscar_inconsistencias,
    FECHA_CORTE,
    buscar_por_numero,
)
from services.generador_aviso import crear_aviso_pdf

polizas_bp = Blueprint("polizas", __name__)

# Carpeta donde se guardan temporalmente los Excel importados (fuera de data/)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@polizas_bp.route("/")
def inicio():
    """Tablero principal: contadores, primas por aseguradora, inconsistencias
    y tabla de pólizas ordenada por días para vencer (lo urgente primero)."""
    ruta_clientes = session.get("clientes_xlsx")
    resultados = calcular_resultados(ruta_clientes=ruta_clientes)
    conteo = contar_por_estado(resultados)
    primas = primas_por_aseguradora(resultados)
    inconsistencias = buscar_inconsistencias(
        resultados, ruta_clientes=ruta_clientes
    )
    return render_template(
        "inicio.html",
        resultados=resultados,
        conteo=conteo,
        primas=primas,
        inconsistencias=inconsistencias,
        fecha_corte=FECHA_CORTE,
    )


@polizas_bp.route("/aviso/<numero>")
def aviso(numero):
    """Devuelve el aviso de renovación en PDF para verlo en el navegador.
    404 si la póliza no existe o está Vigente."""
    poliza = buscar_por_numero(numero)

    if poliza is None:
        abort(404)

    if poliza.get("estado") == "Vigente":
        abort(404)

    pdf_bytes = crear_aviso_pdf(poliza)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"aviso_{numero}.pdf",
    )


@polizas_bp.route("/descargar-avisos")
def descargar_avisos():
    """Arma en memoria un .zip con los avisos de todas las pólizas
    Por vencer y Vencidas, y lo envía para descarga."""
    resultados = calcular_resultados()

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in resultados:
            if r.get("estado") in ("Por vencer", "Vencida"):
                pdf_bytes = crear_aviso_pdf(r)
                zf.writestr(f"aviso_{r.get('numero')}.pdf", pdf_bytes)

    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="avisos.zip",
    )


@polizas_bp.route("/importar-clientes", methods=["POST"])
def importar_clientes():
    """Recibe un Excel de clientes, lo guarda en uploads/ y lo guarda en sesión
    para usarlo en el tablero (sin tocar data/)."""
    if "archivo" not in request.files:
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for("polizas.inicio"))

    archivo = request.files["archivo"]

    if archivo.filename == "":
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for("polizas.inicio"))

    if not archivo.filename.lower().endswith((".xlsx", ".xls")):
        flash("El archivo debe ser un Excel (.xlsx o .xls).", "error")
        return redirect(url_for("polizas.inicio"))

    nombre_seguro = secure_filename(archivo.filename)
    ruta_guardada = UPLOAD_DIR / nombre_seguro
    archivo.save(str(ruta_guardada))

    session["clientes_xlsx"] = str(ruta_guardada)
    flash(f"Clientes importados desde '{archivo.filename}'.", "exito")
    return redirect(url_for("polizas.inicio"))


@polizas_bp.route("/procesar")
def procesar():
    """Recalcula resultados usando el Excel de sesión (o el maestro por defecto)
    y vuelve al tablero."""
    return redirect(url_for("polizas.inicio"))
