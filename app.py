"""app.py - Punto de entrada de la aplicación Flask.

Crea la app Flask con template_folder="views",
static_folder="public/static", static_url_path="/static",
y registra el Blueprint de pólizas.
"""

import os

from flask import Flask

from controllers.polizas_controller import polizas_bp

app = Flask(
    __name__,
    template_folder="views",
    static_folder="public/static",
    static_url_path="/static",
)

app.register_blueprint(polizas_bp)


@app.template_filter("fecha")
def _filtro_fecha(valor):
    """Formatea una fecha a dd/mm/aaaa (solo presentación)."""
    if valor is None:
        return ""
    if hasattr(valor, "strftime"):
        return valor.strftime("%d/%m/%Y")
    return str(valor)


@app.template_filter("moneda")
def _filtro_moneda(valor):
    """Formatea un monto como CRC 228,000.00 o 'No registrada' (solo presentación)."""
    if valor is None:
        return "No registrada"
    return f"CRC {valor:,.2f}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
