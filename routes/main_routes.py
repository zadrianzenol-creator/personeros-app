from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db, peru_now
from models.personero import Colegio, Mesa, Personero
from models.voto import Voto, VotoEspecial, PARTIDOS, CARGOS
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
        nombre = request.form.get("nombre_completo", "").strip()
        dni = request.form.get("dni", "").strip()
        telefono = request.form.get("telefono", "").strip()
        rol = request.form.get("rol", "Personero").strip()
        colegio_id = request.form.get("colegio_id", type=int)
        mesa_id = request.form.get("mesa_id", type=int)
        numero_mesa = request.form.get("numero_mesa", "").strip()

        template = "mobile_registrar.html" if use_mobile else "registrar.html"

        if not nombre or not dni or not colegio_id or not mesa_id or not numero_mesa:
            flash("Complete todos los campos obligatorios.", "error")
            return render_template(template, colegios=colegios, form_data=request.form)

        dni_en_mesa = Personero.query.filter_by(dni=dni, mesa_id=mesa_id).first()
        if dni_en_mesa:
            flash("Este DNI ya está registrado en esta mesa.", "error")
            return render_template(template, colegios=colegios, form_data=request.form)

        dni_en_colegio = Personero.query.filter_by(dni=dni, colegio_id=colegio_id).first()
        if dni_en_colegio:
            flash("Este DNI ya está registrado en este colegio.", "error")
            return render_template(template, colegios=colegios, form_data=request.form)

        now = peru_now()
        personero = Personero(
            nombre_completo=nombre,
            dni=dni,
            telefono=telefono,
            rol=rol,
            colegio_id=colegio_id,
            mesa_id=mesa_id,
            numero_mesa=int(numero_mesa),
            estado="PRESENTE",
            incidente="NINGUNO",
            fecha_registro=now,
            hora_llegada=now.strftime("%H:%M:%S"),
            ip_address=request.remote_addr,
        )
        db.session.add(personero)
        db.session.commit()

        return redirect(url_for("main.contar_votos", personero_id=personero.id))

    template = "mobile_registrar.html" if use_mobile else "registrar.html"
    return render_template(template, colegios=colegios, form_data={})


@main_bp.route("/api/personero-dni/<dni>")
def api_personero_dni(dni):
    personero = Personero.query.filter_by(dni=dni).first()
    if not personero:
        return jsonify({"found": False})
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

    db.session.commit()
    return jsonify({"ok": True, "message": f"Votos de {cargo_id} guardados correctamente"})


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

    stats = db.session.query(
        db.func.count(Personero.id).label("total_hoy"),
        db.func.count(db.case((Personero.estado == "PRESENTE", 1))).label("presentes"),
        db.func.count(db.case((Personero.estado == "AUSENTE", 1))).label("ausentes"),
        db.func.count(db.case((Personero.estado == "PENDIENTE", 1))).label("pendientes"),
        db.func.count(db.distinct(Personero.colegio_id)).label("colegios"),
        db.func.count(db.distinct(Personero.mesa_id)).label("mesas"),
    ).filter(db.func.date(Personero.fecha_registro) == hoy).first()

    total_general = Personero.query.count()

    por_partido = {}

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
        "por_partido": {},
        "por_colegio": {},
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
