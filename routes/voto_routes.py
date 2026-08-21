from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db, peru_now
from models.personero import Colegio, Mesa, Personero
from models.voto import Voto, VotoEspecial, PARTIDOS

votos_bp = Blueprint("votos", __name__)


@votos_bp.route("/registrar-votos", methods=["GET", "POST"])
@login_required
def registrar_votos():
    colegios = Colegio.query.filter_by(is_active=True).order_by(Colegio.nombre).all()

    if request.method == "POST":
        colegio_id = request.form.get("colegio_id", type=int)
        mesa_id = request.form.get("mesa_id", type=int)

        if not colegio_id or not mesa_id:
            flash("Seleccione colegio y mesa.", "error")
            return redirect(url_for("votos.registrar_votos"))

        for partido in PARTIDOS:
            key = f"voto_{partido['id']}"
            valor = request.form.get(key, 0, type=int)
            if valor > 0:
                existing = Voto.query.filter_by(
                    mesa_id=mesa_id, partido_id=partido["id"]
                ).first()
                if existing:
                    existing.votos = valor
                else:
                    db.session.add(Voto(
                        mesa_id=mesa_id,
                        colegio_id=colegio_id,
                        partido_id=partido["id"],
                        partido_nombre=partido["nombre"],
                        partido_sigla=partido["sigla"],
                        votos=valor,
                        registrado_por=current_user.id,
                    ))

        tipos_especiales = ["BLANCO", "NULO", "IMPUGNADO"]
        for tipo in tipos_especiales:
            key = f"voto_{tipo.lower()}"
            valor = request.form.get(key, 0, type=int)
            if valor >= 0:
                existing = VotoEspecial.query.filter_by(
                    mesa_id=mesa_id, tipo=tipo
                ).first()
                if existing:
                    existing.cantidad = valor
                else:
                    db.session.add(VotoEspecial(
                        mesa_id=mesa_id,
                        colegio_id=colegio_id,
                        tipo=tipo,
                        cantidad=valor,
                        registrado_por=current_user.id,
                    ))

        db.session.commit()
        flash("Votos registrados exitosamente.", "success")
        return redirect(url_for("votos.registrar_votos"))

    return render_template("registrar_votos.html", colegios=colegios, partidos=PARTIDOS)


@votos_bp.route("/api/mesas/<int:colegio_id>")
@login_required
def api_mesas(colegio_id):
    mesas = Mesa.query.filter_by(colegio_id=colegio_id, is_active=True).order_by(Mesa.numero).all()
    return jsonify([m.to_dict() for m in mesas])


@votos_bp.route("/api/votos-resumen")
@login_required
def api_votos_resumen():
    colegio_id = request.args.get("colegio_id", type=int)
    mesa_id = request.args.get("mesa_id", type=int)

    query = Voto.query
    query_especial = VotoEspecial.query

    if colegio_id:
        query = query.filter_by(colegio_id=colegio_id)
        query_especial = query_especial.filter_by(colegio_id=colegio_id)
    if mesa_id:
        query = query.filter_by(mesa_id=mesa_id)
        query_especial = query_especial.filter_by(mesa_id=mesa_id)

    votos_por_partido = {}
    for v in query.all():
        if v.partido_nombre not in votos_por_partido:
            votos_por_partido[v.partido_nombre] = {"sigla": v.partido_sigla, "votos": 0, "id": v.partido_id}
        votos_por_partido[v.partido_nombre]["votos"] += v.votos

    votos_especiales = {}
    total_especial = 0
    for ve in query_especial.all():
        votos_especiales[ve.tipo] = ve.cantidad
        total_especial += ve.cantidad

    total_partidos = sum(v["votos"] for v in votos_por_partido.values())
    total_general = total_partidos + total_especial

    return jsonify({
        "por_partido": votos_por_partido,
        "especiales": votos_especiales,
        "total_partidos": total_partidos,
        "total_especial": total_especial,
        "total_general": total_general,
    })
