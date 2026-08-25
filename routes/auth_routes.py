from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from models.activity import ActivityLog
from database import db, peru_now

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


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
