import os
import json
import traceback
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_login import LoginManager, current_user
from config import Config
from database import db, init_db
from models.user import User
from routes.auth_routes import auth_bp
from routes.main_routes import main_bp
from routes.voto_routes import votos_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = ""
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(votos_bp, url_prefix="/votos")

    ENDPOINTS_PERMITIDOS_DIGITADOR = {
        "votos.registrar_votos",
        "votos.api_mesas",
        "votos.api_votos_existen",
        "auth.logout",
        "static",
    }

    @app.before_request
    def restringir_acceso_digitador():
        if current_user.is_authenticated and current_user.role == "digitador":
            endpoint = request.endpoint
            if endpoint and endpoint not in ENDPOINTS_PERMITIDOS_DIGITADOR:
                return redirect(url_for("votos.registrar_votos"))

    @app.route("/ping")
    def ping():
        return jsonify({"status": "ok"}), 200

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        try:
            from database import db
            from models.activity import ActivityLog
            entry = ActivityLog(
                tipo="ERROR_500",
                detalle=f"{request.method} {request.path} - {e}"[:2000],
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent", "")[:300],
            )
            db.session.add(entry)
            db.session.commit()
        except Exception:
            db.session.rollback()
        app.logger.error("Error 500 en %s %s:\n%s", request.method, request.path, traceback.format_exc())
        return render_template("errors/500.html"), 500

    return app


def seed_from_json():
    from models.personero import Colegio, Mesa, Personero

    if Colegio.query.first() is not None:
        return

    seed_path = os.path.join(os.path.dirname(__file__), "seed_data.json")
    if not os.path.exists(seed_path):
        print(">> seed_data.json no encontrado, saltando seed.")
        return

    with open(seed_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    locales = data.get("locales", {})
    mesas_map = data.get("mesas", {})
    personeros_list = data.get("personeros", [])

    local_ids = {}
    mesa_ids = {}
    for local_id, nombre in locales.items():
        colegio = Colegio(
            codigo=f"COL-{local_id}",
            nombre=nombre,
            direccion="Chulucanas",
            distrito="Chulucanas",
        )
        db.session.add(colegio)
        db.session.flush()
        local_ids[local_id] = colegio.id

        local_mesas = mesas_map.get(local_id, [])
        for num in local_mesas:
            mesa = Mesa(numero=num, colegio_id=colegio.id, capacidad=400)
            db.session.add(mesa)
            db.session.flush()
            mesa_ids[(local_id, num)] = mesa.id

    db.session.commit()
    print(f">> {len(locales)} colegios y mesas creados desde seed_data.json")

    num = 0
    for local_id, mesa_num, dni, nombre_completo, celular in personeros_list:
        mesa_id = mesa_ids.get((local_id, mesa_num))
        colegio_id = local_ids.get(local_id)
        if not mesa_id or not colegio_id:
            continue
        personero = Personero(
            nombre_completo=nombre_completo,
            dni=dni,
            telefono=celular if celular else "",
            rol="Personero",
            colegio_id=colegio_id,
            mesa_id=mesa_id,
            numero_mesa=mesa_num,
            estado="PENDIENTE",
            incidente="NINGUNO",
        )
        db.session.add(personero)
        num += 1

    db.session.commit()
    print(f">> {num} personeros importados desde seed_data.json")


def seed_admin():
    if User.query.filter_by(username="admin").first() is not None:
        return

    admin = User(
        username="admin",
        full_name="Administrador",
        role="admin",
        is_active=True,
    )
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    print(">> Admin creado (user: admin / pass: admin123)")


app = create_app()

with app.app_context():
    db.create_all()

    with db.engine.connect() as conn:
        try:
            columnas_nuevas = [
                ("last_active", "TIMESTAMP"),
                ("votos_finalizados", "BOOLEAN DEFAULT FALSE NOT NULL"),
                ("votos_finalizados_at", "TIMESTAMP"),
                ("modalidad_reporte", "VARCHAR(30) DEFAULT 'DIRECTO_SISTEMA' NOT NULL"),
            ]
            if db.engine.dialect.name == "sqlite":
                cols = [row[1] for row in conn.execute(db.text("PRAGMA table_info(personeros)"))]
                for nombre, tipo in columnas_nuevas:
                    if nombre not in cols:
                        conn.execute(db.text(f"ALTER TABLE personeros ADD COLUMN {nombre} {tipo}"))
            else:
                for nombre, tipo in columnas_nuevas:
                    conn.execute(db.text(f"ALTER TABLE personeros ADD COLUMN IF NOT EXISTS {nombre} {tipo}"))
            conn.commit()
        except Exception:
            pass
        try:
            # DNIs cargados en el padron con modalidad de reporte ASISTIDO_DIGITADOR
            # (el resto queda con el valor por defecto DIRECTO_SISTEMA). Se reaplica
            # en cada arranque para que el dato llegue a cualquier base de datos
            # donde se despliegue el sistema, sin depender de un script manual.
            dnis_asistido_digitador = [
                "60811039", "74352600", "70585798", "40665454", "42187975",
                "03309298", "70840025", "03372755", "70853935", "03377866",
                "03312670", "03304653", "40224194", "73462909", "74592169",
                "73323943", "42059550", "03313238", "41401543", "70792656",
                "74896317", "70792640", "76181142", "80277714", "03853912",
                "42414980", "76636517", "45238202", "03311581", "73017017",
                "75470138", "74624224", "74249273", "74504398", "71509942",
                "61303442", "75219165", "03372976", "80444738",
            ]
            for dni in dnis_asistido_digitador:
                conn.execute(
                    db.text("UPDATE personeros SET modalidad_reporte='ASISTIDO_DIGITADOR' WHERE dni=:dni"),
                    {"dni": dni},
                )
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(db.text("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id SERIAL PRIMARY KEY,
                    personero_id INTEGER REFERENCES personeros(id),
                    user_id INTEGER REFERENCES users(id),
                    tipo VARCHAR(50) NOT NULL,
                    detalle TEXT,
                    ip_address VARCHAR(45),
                    user_agent VARCHAR(300),
                    fecha TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC' - INTERVAL '5 hours')
                )
            """))
            conn.execute(db.text("CREATE INDEX IF NOT EXISTS idx_log_personero ON activity_logs(personero_id)"))
            conn.execute(db.text("CREATE INDEX IF NOT EXISTS idx_log_fecha ON activity_logs(fecha)"))
            conn.execute(db.text("CREATE INDEX IF NOT EXISTS idx_log_tipo ON activity_logs(tipo)"))
            conn.commit()
        except Exception:
            pass

    seed_from_json()
    seed_admin()

if __name__ == "__main__":
    print(">> Sistema de Personeros: http://localhost:5050")
    app.run(debug=True, host="0.0.0.0", port=5050)
