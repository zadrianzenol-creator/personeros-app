from database import db, peru_now


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"
    __table_args__ = (
        db.Index("idx_log_personero", "personero_id"),
        db.Index("idx_log_fecha", "fecha"),
        db.Index("idx_log_tipo", "tipo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    personero_id = db.Column(db.Integer, db.ForeignKey("personeros.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    tipo = db.Column(db.String(50), nullable=False)
    detalle = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(300), nullable=True)
    fecha = db.Column(db.DateTime, default=peru_now)

    personero = db.relationship("Personero", backref="actividades")
    user = db.relationship("User", backref="actividades")

    def to_dict(self):
        return {
            "id": self.id,
            "personero_id": self.personero_id,
            "personero_nombre": self.personero.nombre_completo if self.personero else None,
            "personero_dni": self.personero.dni if self.personero else None,
            "user_id": self.user_id,
            "user_nombre": self.user.full_name if self.user else None,
            "tipo": self.tipo,
            "detalle": self.detalle or "",
            "ip_address": self.ip_address or "",
            "fecha": self.fecha.strftime("%d/%m/%Y %H:%M:%S") if self.fecha else "",
            "fecha_iso": self.fecha.isoformat() if self.fecha else "",
        }
