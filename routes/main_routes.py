from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db, peru_now
from models.personero import Colegio, Mesa, Personero
from datetime import datetime
import user_agents

main_bp = Blueprint("main", __name__)


def is_mobile(request):
    ua = user_agents.parse(request.headers.get('User-Agent', ''))
    return ua.is_mobile


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
    colegios = Colegio.query.filter_by(is_active=True).order_by(Colegio.nombre).all()
    use_mobile = is_mobile(request)

    if request.method == "POST":
        codigo = request.form.get("codigo", "").strip().upper()
        nombre = request.form.get("nombre_completo", "").strip()
        dni = request.form.get("dni", "").strip()
        telefono = request.form.get("telefono", "").strip()
        partido = request.form.get("partido_politico", "").strip()
        rol = request.form.get("rol", "Personero").strip()
        colegio_id = request.form.get("colegio_id", type=int)
        mesa_id = request.form.get("mesa_id", type=int)
        numero_mesa = request.form.get("numero_mesa", "").strip()

        template = "mobile_registrar.html" if use_mobile else "registrar.html"

        if not codigo or not nombre or not dni or not partido or not colegio_id or not mesa_id or not numero_mesa:
            flash("Complete todos los campos obligatorios.", "error")
            return render_template(template, colegios=colegios, form_data=request.form)

        existing = Personero.query.filter_by(codigo=codigo).first()
        if existing:
            flash("Este código ya está registrado.", "error")
            return render_template(template, colegios=colegios, form_data=request.form)

        now = peru_now()
        personero = Personero(
            codigo=codigo,
            nombre_completo=nombre,
            dni=dni,
            telefono=telefono,
            partido_politico=partido,
            rol=rol,
            colegio_id=colegio_id,
            mesa_id=mesa_id,
            numero_mesa=int(numero_mesa),
            estado="PENDIENTE",
            incidente="NINGUNO",
            fecha_registro=now,
            hora_llegada=now.strftime("%H:%M:%S"),
            ip_address=request.remote_addr,
        )
        db.session.add(personero)
        db.session.commit()

        flash(f"Personero {nombre} registrado exitosamente.", "success")
        return redirect(url_for("main.registrar"))

    template = "mobile_registrar.html" if use_mobile else "registrar.html"
    return render_template(template, colegios=colegios, form_data={})


@main_bp.route("/confirmar/<int:personero_id>", methods=["POST"])
@login_required
def confirmar_asistencia(personero_id):
    personero = Personero.query.get_or_404(personero_id)
    nuevo_estado = request.form.get("estado", "PRESENTE").strip()
    incidente = request.form.get("incidente", "NINGUNO").strip()

    if nuevo_estado in ["PRESENTE", "AUSENTE"]:
        personero.estado = nuevo_estado
        personero.incidente = incidente
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
            db.or_(
                Personero.nombre_completo.ilike(f"%{search}%"),
                Personero.codigo.ilike(f"%{search}%"),
                Personero.dni.ilike(f"%{search}%"),
            )
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

    stats = db.session.query(
        db.func.count(Personero.id).label("total_hoy"),
        db.func.count(db.case((Personero.estado == "PRESENTE", 1))).label("presentes"),
        db.func.count(db.case((Personero.estado == "AUSENTE", 1))).label("ausentes"),
        db.func.count(db.case((Personero.estado == "PENDIENTE", 1))).label("pendientes"),
        db.func.count(db.distinct(Personero.colegio_id)).label("colegios"),
        db.func.count(db.distinct(Personero.mesa_id)).label("mesas"),
    ).filter(db.func.date(Personero.fecha_registro) == hoy).first()

    total_general = Personero.query.count()

    por_partido = db.session.query(
        Personero.partido_politico, db.func.count(Personero.id)
    ).group_by(Personero.partido_politico).order_by(
        db.func.count(Personero.id).desc()
    ).all()

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
        "registros_recientes": 0,
        "por_partido": {p: c for p, c in por_partido},
        "por_colegio": {},
        "ultimos": [p.to_dict() for p in ultimos],
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
