import os
import json
from flask import Flask, render_template, jsonify
from flask_login import LoginManager
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
    seed_from_json()
    seed_admin()

if __name__ == "__main__":
    print(">> Sistema de Personeros: http://localhost:5050")
    app.run(debug=True, host="0.0.0.0", port=5050)
