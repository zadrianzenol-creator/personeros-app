from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from models.activity import ActivityLog
from database import db, peru_now

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

ROLES_VALIDOS = ("admin", "digitador")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            return render_template("login.html", error="Credenciales incorrectas.")

        if not user.is_active:
            return render_template("login.html", error="Cuenta desactivada.")

        login_user(user, remember=True)

        entry = ActivityLog(
            user_id=user.id,
            tipo="LOGIN",
            detalle=f"Inicio de sesion - {user.full_name}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent", "")[:300],
        )
        db.session.add(entry)
        db.session.commit()

        flash(f"Bienvenido, {user.full_name}.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    entry = ActivityLog(
        user_id=current_user.id,
        tipo="LOGOUT",
        detalle=f"Cierre de sesion - {current_user.full_name}",
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent", "")[:300],
    )
    db.session.add(entry)
    db.session.commit()

    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/usuarios", methods=["GET", "POST"])
@login_required
def usuarios():
    if current_user.role != "admin":
        abort(403)

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "").strip()

        if not username or not full_name or not password:
            flash("Complete usuario, nombre y contrasena.", "error")
            return redirect(url_for("auth.usuarios"))

        if role not in ROLES_VALIDOS:
            flash("Rol invalido.", "error")
            return redirect(url_for("auth.usuarios"))

        if User.query.filter_by(username=username).first():
            flash(f'El usuario "{username}" ya existe.', "error")
            return redirect(url_for("auth.usuarios"))

        nuevo = User(username=username, full_name=full_name, role=role, is_active=True)
        nuevo.set_password(password)
        db.session.add(nuevo)
        db.session.commit()

        flash(f'Usuario "{username}" ({role}) creado correctamente.', "success")
        return redirect(url_for("auth.usuarios"))

    lista_usuarios = User.query.order_by(User.created_at.desc()).all()
    return render_template("usuarios.html", usuarios=lista_usuarios, roles=ROLES_VALIDOS)


@auth_bp.route("/usuarios/<int:user_id>/toggle", methods=["POST"])
@login_required
def toggle_usuario(user_id):
    if current_user.role != "admin":
        abort(403)

    usuario = User.query.get_or_404(user_id)
    if usuario.id == current_user.id:
        flash("No puedes desactivar tu propia cuenta.", "error")
        return redirect(url_for("auth.usuarios"))

    usuario.is_active = not usuario.is_active
    db.session.commit()
    flash(f'Usuario "{usuario.username}" {"activado" if usuario.is_active else "desactivado"}.', "success")
    return redirect(url_for("auth.usuarios"))
