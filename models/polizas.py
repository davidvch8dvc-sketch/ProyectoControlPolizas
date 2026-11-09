"""models/polizas.py - Reglas del negocio de control de pólizas."""

from datetime import date

from models.datos import cargar_clientes, cargar_polizas

FECHA_CORTE = date(2026, 11, 9)
DIAS_AVISO = 30


def estado_poliza(hasta, fecha_corte=FECHA_CORTE):
    """Devuelve el estado de una póliza según su fecha de vigencia hasta.

    Reglas:
    - Sin fecha: si hasta es None.
    - Vencida: hasta < fecha_corte.
    - Por vencer: 0 <= días hasta vencer <= DIAS_AVISO.
    - Vigente: más de DIAS_AVISO días.
    """
    if hasta is None:
        return "Sin fecha"

    dias = (hasta - fecha_corte).days

    if hasta < fecha_corte:
        return "Vencida"
    elif 0 <= dias <= DIAS_AVISO:
        return "Por vencer"
    else:
        return "Vigente"


def _indexar_clientes():
    """Lee el maestro de clientes y devuelve un dict: cedula -> correo."""
    df = cargar_clientes()
    index = {}
    for _, fila in df.iterrows():
        cedula = str(fila["Cedula"]).strip()
        correo = fila.get("Correo", "")
        if pd_notna(correo):
            correo = str(correo).strip()
        else:
            correo = ""
        index[cedula] = correo
    return index


def pd_notna(valor):
    """Devuelve True si el valor no es NaN/None (evita importar pandas aquí)."""
    return valor is not None and str(valor).strip() != "" and str(valor).lower() != "nan"


def calcular_resultados(fecha_corte=FECHA_CORTE):
    """Cruza cada póliza con el maestro por cédula, calcula días hasta vencer
    y estado, y devuelve una lista de diccionarios ordenada de menos a más
    días (lo urgente primero)."""
    clientes_por_cedula = _indexar_clientes()
    cedulas_maestro = set(clientes_por_cedula.keys())

    polizas = cargar_polizas()
    resultados = []

    for poliza in polizas:
        cedula = poliza.get("cedula")
        en_maestro = bool(cedula) and cedula in cedulas_maestro
        correo = clientes_por_cedula.get(cedula, "") if en_maestro else ""

        hasta = poliza.get("hasta")
        estado = estado_poliza(hasta, fecha_corte)

        if hasta is not None:
            dias = (hasta - fecha_corte).days
        else:
            dias = None

        resultado = {
            **poliza,
            "correo": correo,
            "en_maestro": en_maestro,
            "dias": dias,
            "estado": estado,
        }
        resultados.append(resultado)

    # Ordenar: primero los que tienen días (menos a más), las sin fecha al final
    resultados.sort(
        key=lambda r: (
            r["dias"] is None,
            r["dias"] if r["dias"] is not None else float("inf"),
        )
    )

    return resultados


def contar_por_estado(resultados):
    """Devuelve un diccionario con cuántas pólizas hay de cada estado."""
    conteos = {"Vigente": 0, "Por vencer": 0, "Vencida": 0, "Sin fecha": 0}
    for r in resultados:
        estado = r["estado"]
        if estado in conteos:
            conteos[estado] += 1
        else:
            conteos[estado] = 1
    return conteos


def primas_por_aseguradora(resultados):
    """Devuelve un diccionario aseguradora -> suma de primas de pólizas no
    vencidas, ordenado de mayor a menor."""
    sumas = {}
    for r in resultados:
        if r["estado"] != "Vencida" and r.get("prima") is not None:
            aseguradora = r.get("aseguradora", "Sin aseguradora")
            sumas[aseguradora] = sumas.get(aseguradora, 0) + r["prima"]
    return dict(sorted(sumas.items(), key=lambda item: item[1], reverse=True))


def buscar_inconsistencias(resultados):
    """Devuelve una lista de textos con los 3 tipos de problema:
    1. cliente del maestro sin ninguna póliza
    2. póliza cuya cédula no está en el maestro
    3. póliza sin prima o con fecha ilegible
    """
    inconsistencias = []

    clientes_df = cargar_clientes()
    cedulas_maestro = set()
    for _, fila in clientes_df.iterrows():
        cedulas_maestro.add(str(fila["Cedula"]).strip())

    cedulas_polizas = set()
    for r in resultados:
        ced = r.get("cedula")
        if ced:
            cedulas_polizas.add(ced)

    # 1. Cliente del maestro sin ninguna póliza
    for cedula in sorted(cedulas_maestro - cedulas_polizas):
        inconsistencias.append(f"Cliente del maestro sin póliza: cédula {cedula}")

    # 2. Póliza cuya cédula no está en el maestro
    for r in resultados:
        ced = r.get("cedula")
        if ced and ced not in cedulas_maestro:
            inconsistencias.append(
                f"Póliza {r.get('numero')} con cédula {ced} no está en el maestro"
            )

    # 3. Póliza sin prima o con fecha ilegible
    for r in resultados:
        problemas = []
        if r.get("prima") is None:
            problemas.append("sin prima")
        if r.get("desde") is None or r.get("hasta") is None:
            problemas.append("fecha ilegible")
        if problemas:
            inconsistencias.append(
                f"Póliza {r.get('numero')} con {' y '.join(problemas)}"
            )

    return inconsistencias


def buscar_por_numero(numero):
    """Busca una póliza por su número en los resultados calculados."""
    for r in calcular_resultados():
        if r.get("numero") == numero:
            return r
    return None
