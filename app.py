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


def seed_colegios():
    from models.personero import Colegio, Mesa

    if Colegio.query.first() is not None:
        return

    colegios_data = [
        {"codigo": "COL-001", "nombre": "I.E.P. San Gabriel", "direccion": "Jr. Ica 431", "distrito": "Chulucanas", "num_mesas": 9},
        {"codigo": "COL-002", "nombre": "I.E.P. San Ignacio de Loyola", "direccion": "Jr. Ayacucho 181", "distrito": "Chulucanas", "num_mesas": 12},
        {"codigo": "COL-003", "nombre": "I.E. 14613 Jorge Duberly Benites Sánchez", "direccion": "Chulucanas", "distrito": "Chulucanas", "num_mesas": 10},
        {"codigo": "COL-004", "nombre": "I.E. 14620 Señor de la Divina Misericordia", "direccion": "Chulucanas", "distrito": "Chulucanas", "num_mesas": 8},
        {"codigo": "COL-005", "nombre": "I.E. 14612 Lusmila Briceño Carrasco", "direccion": "Ñacara", "distrito": "Chulucanas", "num_mesas": 6},
        {"codigo": "COL-006", "nombre": "I.E. 14996 Chulucanas", "direccion": "Rinconada", "distrito": "Chulucanas", "num_mesas": 5},
        {"codigo": "COL-007", "nombre": "I.E. 44", "direccion": "Batanes", "distrito": "Chulucanas", "num_mesas": 4},
        {"codigo": "COL-008", "nombre": "I.E. 43", "direccion": "Cruz Pampa", "distrito": "Chulucanas", "num_mesas": 4},
    ]

    for data in colegios_data:
        num = data.pop("num_mesas", 5)
        colegio = Colegio(**data)
        db.session.add(colegio)
        db.session.flush()
        for i in range(1, num + 1):
            db.session.add(Mesa(numero=i, colegio_id=colegio.id, capacidad=400))

    db.session.commit()
    print(">> Colegios y mesas creados correctamente.")


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


def migrate_db():
    try:
        db.session.execute(db.text("ALTER TABLE votos ADD COLUMN IF NOT EXISTS cargo VARCHAR(50) NOT NULL DEFAULT 'regional'"))
        db.session.execute(db.text("ALTER TABLE votos ADD COLUMN IF NOT EXISTS personero_id INTEGER"))
        db.session.execute(db.text("ALTER TABLE votos_especiales ADD COLUMN IF NOT EXISTS cargo VARCHAR(50) NOT NULL DEFAULT 'regional'"))
        db.session.execute(db.text("ALTER TABLE votos_especiales ADD COLUMN IF NOT EXISTS personero_id INTEGER"))
        db.session.commit()
        print(">> Migracion de columnas cargo/personero_id completada.")
    except Exception as e:
        db.session.rollback()
        print(f">> Migracion ya aplicada o no necesaria: {e}")


app = create_app()

with app.app_context():
    db.create_all()
    migrate_db()
    seed_colegios()
    seed_admin()

if __name__ == "__main__":
    print(">> Sistema de Personeros: http://localhost:5050")
    app.run(debug=True, host="0.0.0.0", port=5050)
