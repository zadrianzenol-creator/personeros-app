from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db, peru_now
from models.personero import Colegio, Mesa, Personero
from models.voto import Voto, VotoEspecial, PARTIDOS, CARGOS
from models.activity import ActivityLog
from datetime import datetime, timedelta
import user_agents

main_bp = Blueprint("main", __name__)


def is_mobile(request):
    ua = user_agents.parse(request.headers.get('User-Agent', ''))
    return ua.is_mobile


def log_activity(tipo, detalle=None, personero_id=None, user_id=None, request_obj=None):
    try:
        ip = request_obj.remote_addr if request_obj else None
        ua_str = request_obj.headers.get("User-Agent", "")[:300] if request_obj else None
        entry = ActivityLog(
            personero_id=personero_id,
            user_id=user_id,
            tipo=tipo,
            detalle=detalle,
            ip_address=ip,
            user_agent=ua_str,
        )
        db.session.add(entry)
    except Exception:
        pass


def update_personero_active(personero):
    personero.last_active = peru_now()


ONLINE_THRESHOLD_MINUTES = 5


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    colegios = Colegio.query.filter_by(is_active=True).order_by(Colegio.nombre).all()
    return render_template("dashboard.html", colegios=colegios)


@main_bp.route("/registrar", methods=["GET", "POST"])
def registrar():
    use_mobile = is_mobile(request)

    if request.method == "POST":
        dni = request.form.get("dni", "").strip()
        template = "mobile_registrar.html" if use_mobile else "registrar.html"

        if not dni:
            flash("Ingrese un DNI valido.", "error")
            return render_template(template)

        personero = Personero.query.filter_by(dni=dni).first()
        if not personero:
            flash(f"El DNI {dni} no se encuentra registrado en el sistema.", "error")
            return render_template(template)

        if personero.estado == "PRESENTE":
            flash(f"{personero.nombre_completo} ya fue registrado(a) anteriormente.", "error")
            return render_template(template)

        now = peru_now()
        personero.estado = "PRESENTE"
        personero.fecha_registro = now
        personero.hora_llegada = now.strftime("%H:%M:%S")
        personero.ip_address = request.remote_addr
        personero.last_active = now
        log_activity("CHECK_IN", f"Registro de asistencia - Mesa {personero.numero_mesa}", personero_id=personero.id, request_obj=request)
        db.session.commit()

        return redirect(url_for("main.contar_votos", personero_id=personero.id))

    template = "mobile_registrar.html" if use_mobile else "registrar.html"
    return render_template(template)


@main_bp.route("/api/personero-dni/<dni>")
def api_personero_dni(dni):
    personero = Personero.query.filter_by(dni=dni).first()
    if not personero:
        return jsonify({"found": False})

    now = peru_now()
    personero.last_active = now
    log_activity("BUSQUEDA_DNI", f"DNI {dni} consultado", personero_id=personero.id, request_obj=request)
    db.session.commit()

    return jsonify({
        "found": True,
        "id": personero.id,
        "nombre_completo": personero.nombre_completo,
        "dni": personero.dni,
        "telefono": personero.telefono or "",
        "rol": personero.rol,
        "colegio_id": personero.colegio_id,
        "colegio_nombre": personero.colegio.nombre if personero.colegio else "",
        "mesa_id": personero.mesa_id,
        "numero_mesa": personero.numero_mesa,
    })


@main_bp.route("/c/<int:personero_id>")
def contar_votos(personero_id):
    personero = Personero.query.get_or_404(personero_id)
    if personero.estado != "PRESENTE":
        personero.estado = "PRESENTE"

    now = peru_now()
    personero.last_active = now
    log_activity("ACCESO_VOTOS", f"Acceso al formulario de votos", personero_id=personero.id, request_obj=request)
    db.session.commit()

    return render_template(
        "contar_votos.html",
        personero=personero,
        partidos=PARTIDOS,
        cargos=CARGOS,
    )


@main_bp.route("/api/guardar-votos/<int:personero_id>", methods=["POST"])
def api_guardar_votos(personero_id):
    personero = Personero.query.get_or_404(personero_id)
    data = request.get_json()

    if not data or "cargo" not in data or "votos" not in data:
        return jsonify({"error": "Datos incompletos"}), 400

    cargo_id = data["cargo"]
    votos_data = data["votos"]
    especiales = data.get("especiales", {})
    cargo_nombre = next((c["nombre"] for c in CARGOS if c["id"] == cargo_id), cargo_id)
    total_votos = sum(item["votos"] for item in votos_data)
    total_especial = sum(especiales.values())

    for item in votos_data:
        partido_id = item["partido_id"]
        partido_info = next((p for p in PARTIDOS if p["id"] == partido_id), None)
        if not partido_info:
            continue

        existing = Voto.query.filter_by(
            mesa_id=personero.mesa_id,
            partido_id=partido_id,
            cargo=cargo_id,
        ).first()

        if existing:
            existing.votos = item["votos"]
        else:
            db.session.add(Voto(
                mesa_id=personero.mesa_id,
                colegio_id=personero.colegio_id,
                partido_id=partido_id,
                partido_nombre=partido_info["nombre"],
                partido_sigla=partido_info["sigla"],
                cargo=cargo_id,
                votos=item["votos"],
                registrado_por=None,
                personero_id=personero.id,
            ))

    for tipo in ["BLANCO", "NULO", "IMPUGNADO"]:
        cantidad = especiales.get(tipo, 0)
        existing = VotoEspecial.query.filter_by(
            mesa_id=personero.mesa_id,
            cargo=cargo_id,
            tipo=tipo,
        ).first()
        if existing:
            existing.cantidad = cantidad
        else:
            db.session.add(VotoEspecial(
                mesa_id=personero.mesa_id,
                colegio_id=personero.colegio_id,
                cargo=cargo_id,
                tipo=tipo,
                cantidad=cantidad,
                registrado_por=None,
                personero_id=personero.id,
            ))

    now = peru_now()
    personero.last_active = now
    log_activity(
        "VOTOS_GUARDADOS",
        f"Guardo votos de {cargo_nombre} - Total partidos: {total_votos}, Especiales: {total_especial}",
        personero_id=personero.id,
        request_obj=request,
    )
    db.session.commit()
    return jsonify({"ok": True, "message": f"Votos de {cargo_id} guardados correctamente"})


@main_bp.route("/confirmar/<int:personero_id>", methods=["POST"])
@login_required
def confirmar_asistencia(personero_id):
    personero = Personero.query.get_or_404(personero_id)
    nuevo_estado = request.form.get("estado", "PRESENTE").strip()
    incidente = request.form.get("incidente", "NINGUNO").strip()
    estado_anterior = personero.estado

    if nuevo_estado in ["PRESENTE", "AUSENTE"]:
        personero.estado = nuevo_estado
        personero.incidente = incidente
        log_activity(
            "CAMBIO_ESTADO",
            f"Cambio de estado: {estado_anterior} -> {nuevo_estado}" + (f" - Incidente: {incidente}" if incidente != "NINGUNO" else ""),
            personero_id=personero.id,
            user_id=current_user.id,
            request_obj=request,
        )
        db.session.commit()
        flash(f"Asistencia de {personero.nombre_completo} actualizada a {nuevo_estado}.", "success")

    return redirect(request.referrer or url_for("main.dashboard"))


@main_bp.route("/api/mesas/<int:colegio_id>")
def api_mesas(colegio_id):
    mesas = Mesa.query.filter_by(colegio_id=colegio_id, is_active=True).order_by(Mesa.numero).all()
    return jsonify([m.to_dict() for m in mesas])


@main_bp.route("/api/personeros")
@login_required
def api_personeros():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    colegio_id = request.args.get("colegio_id", type=int)
    fecha = request.args.get("fecha", "")
    search = request.args.get("search", "").strip()
    estado = request.args.get("estado", "")

    query = Personero.query

    if colegio_id:
        query = query.filter_by(colegio_id=colegio_id)
    if fecha:
        try:
            f = datetime.strptime(fecha, "%Y-%m-%d").date()
            query = query.filter(db.func.date(Personero.fecha_registro) == f)
        except ValueError:
            pass
    if search:
        query = query.filter(
            Personero.dni.ilike(f"%{search}%")
        )
    if estado:
        query = query.filter_by(estado=estado)

    query = query.order_by(Personero.fecha_registro.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "personeros": [p.to_dict() for p in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
    })


@main_bp.route("/api/stats")
@login_required
def api_stats():
    hoy = peru_now().date()
    now = peru_now()

    stats = db.session.query(
        db.func.count(Personero.id).label("total_hoy"),
        db.func.count(db.case((Personero.estado == "PRESENTE", 1))).label("presentes"),
        db.func.count(db.case((Personero.estado == "AUSENTE", 1))).label("ausentes"),
        db.func.count(db.case((Personero.estado == "PENDIENTE", 1))).label("pendientes"),
        db.func.count(db.distinct(Personero.colegio_id)).label("colegios"),
        db.func.count(db.distinct(Personero.mesa_id)).label("mesas"),
    ).filter(db.func.date(Personero.fecha_registro) == hoy).first()

    total_general = Personero.query.count()

    online_threshold = now - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)
    online_count = Personero.query.filter(
        Personero.last_active >= online_threshold,
        Personero.estado == "PRESENTE",
    ).count()

    ultimos = Personero.query.order_by(
        Personero.fecha_registro.desc()
    ).limit(10).all()

    return jsonify({
        "total_hoy": stats.total_hoy if stats else 0,
        "total_general": total_general,
        "presentes_hoy": stats.presentes if stats else 0,
        "ausentes_hoy": stats.ausentes if stats else 0,
        "pendientes_hoy": stats.pendientes if stats else 0,
        "colegios_con_personeros": stats.colegios if stats else 0,
        "mesas_con_personeros": stats.mesas if stats else 0,
        "online_count": online_count,
        "ultimos": [p.to_dict() for p in ultimos],
    })


@main_bp.route("/api/votos-por-cargo/<int:personero_id>")
def api_votos_por_cargo(personero_id):
    personero = Personero.query.get_or_404(personero_id)

    votos_existentes = {}
    for v in Voto.query.filter_by(mesa_id=personero.mesa_id).all():
        if v.cargo not in votos_existentes:
            votos_existentes[v.cargo] = {}
        votos_existentes[v.cargo][v.partido_id] = v.votos

    especiales_existentes = {}
    for ve in VotoEspecial.query.filter_by(mesa_id=personero.mesa_id).all():
        if ve.cargo not in especiales_existentes:
            especiales_existentes[ve.cargo] = {}
        especiales_existentes[ve.cargo][ve.tipo] = ve.cantidad

    return jsonify({
        "votos": votos_existentes,
        "especiales": especiales_existentes,
    })


@main_bp.route("/detalle/<int:colegio_id>")
@login_required
def detalle_colegio(colegio_id):
    colegio = Colegio.query.get_or_404(colegio_id)
    personeros = Personero.query.filter_by(colegio_id=colegio_id).order_by(
        Personero.numero_mesa, Personero.fecha_registro.desc()
    ).all()
    mesas = Mesa.query.filter_by(colegio_id=colegio_id, is_active=True).order_by(Mesa.numero).all()
    return render_template(
        "detalle_colegio.html",
        colegio=colegio,
        personeros=personeros,
        mesas=mesas,
    )


@main_bp.route("/monitoreo")
@login_required
def monitoreo():
    return render_template("monitoreo.html")


@main_bp.route("/api/monitoreo/actividad")
@login_required
def api_monitoreo_actividad():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    tipo = request.args.get("tipo", "")
    personero_id = request.args.get("personero_id", type=int)
    fecha = request.args.get("fecha", "")

    query = ActivityLog.query

    if tipo:
        query = query.filter_by(tipo=tipo)
    if personero_id:
        query = query.filter_by(personero_id=personero_id)
    if fecha:
        try:
            f = datetime.strptime(fecha, "%Y-%m-%d").date()
            query = query.filter(db.func.date(ActivityLog.fecha) == f)
        except ValueError:
            pass

    query = query.order_by(ActivityLog.fecha.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "actividades": [a.to_dict() for a in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
    })


@main_bp.route("/api/monitoreo/personero/<int:personero_id>")
@login_required
def api_monitoreo_personero(personero_id):
    personero = Personero.query.get_or_404(personero_id)
    actividades = ActivityLog.query.filter_by(personero_id=personero_id).order_by(
        ActivityLog.fecha.desc()
    ).limit(100).all()

    votos_por_cargo = {}
    for v in Voto.query.filter_by(personero_id=personero_id).all():
        if v.cargo not in votos_por_cargo:
            votos_por_cargo[v.cargo] = {"total": 0, "partidos": {}}
        votos_por_cargo[v.cargo]["total"] += v.votos
        votos_por_cargo[v.cargo]["partidos"][v.partido_sigla] = v.votos

    especiales_por_cargo = {}
    for ve in VotoEspecial.query.filter_by(personero_id=personero_id).all():
        if ve.cargo not in especiales_por_cargo:
            especiales_por_cargo[ve.cargo] = {}
        especiales_por_cargo[ve.cargo][ve.tipo] = ve.cantidad

    return jsonify({
        "personero": personero.to_dict(),
        "actividades": [a.to_dict() for a in actividades],
        "votos": votos_por_cargo,
        "especiales": especiales_por_cargo,
    })


@main_bp.route("/api/monitoreo/online")
@login_required
def api_monitoreo_online():
    now = peru_now()
    online_threshold = now - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)

    online = Personero.query.filter(
        Personero.last_active >= online_threshold,
        Personero.estado == "PRESENTE",
    ).order_by(Personero.last_active.desc()).all()

    return jsonify({
        "online": [p.to_dict() for p in online],
        "count": len(online),
        "threshold_minutes": ONLINE_THRESHOLD_MINUTES,
    })


@main_bp.route("/api/monitoreo/resumen")
@login_required
def api_monitoreo_resumen():
    now = peru_now()
    hoy = now.date()
    online_threshold = now - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)

    total_personeros = Personero.query.count()
    presentes = Personero.query.filter_by(estado="PRESENTE").count()
    ausentes = Personero.query.filter_by(estado="AUSENTE").count()
    pendientes = Personero.query.filter_by(estado="PENDIENTE").count()
    online = Personero.query.filter(
        Personero.last_active >= online_threshold,
        Personero.estado == "PRESENTE",
    ).count()

    checkins_hoy = ActivityLog.query.filter(
        ActivityLog.tipo == "CHECK_IN",
        db.func.date(ActivityLog.fecha) == hoy,
    ).count()

    votos_hoy = ActivityLog.query.filter(
        ActivityLog.tipo == "VOTOS_GUARDADOS",
        db.func.date(ActivityLog.fecha) == hoy,
    ).count()

    total_votos_partidos = db.session.query(
        db.func.coalesce(db.func.sum(Voto.votos), 0)
    ).scalar()

    total_votos_especiales = db.session.query(
        db.func.coalesce(db.func.sum(VotoEspecial.cantidad), 0)
    ).scalar()

    por_colegio = db.session.query(
        Colegio.nombre,
        db.func.count(Personero.id),
        db.func.count(db.case((Personero.estado == "PRESENTE", 1))),
        db.func.count(db.case((Personero.estado == "AUSENTE", 1))),
    ).join(Personero, Personero.colegio_id == Colegio.id).group_by(Colegio.id).all()

    colegios_stats = []
    for nombre, total, pres, aus in por_colegio:
        colegios_stats.append({
            "nombre": nombre,
            "total": total,
            "presentes": pres,
            "ausentes": aus,
            "porcentaje": round(pres / total * 100) if total > 0 else 0,
        })
    colegios_stats.sort(key=lambda x: x["porcentaje"], reverse=True)

    return jsonify({
        "total_personeros": total_personeros,
        "presentes": presentes,
        "ausentes": ausentes,
        "pendientes": pendientes,
        "online": online,
        "checkins_hoy": checkins_hoy,
        "votos_hoy": votos_hoy,
        "total_votos_partidos": total_votos_partidos,
        "total_votos_especiales": total_votos_especiales,
        "total_votos": total_votos_partidos + total_votos_especiales,
        "por_colegio": colegios_stats,
    })
