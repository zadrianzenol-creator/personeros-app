from database import db, peru_now


class Colegio(db.Model):
    __tablename__ = "colegios"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(200), nullable=False)
    direccion = db.Column(db.String(300), nullable=True)
    distrito = db.Column(db.String(100), nullable=True)
    num_mesas = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=peru_now)

    mesas = db.relationship("Mesa", backref="colegio", lazy="dynamic", cascade="all, delete-orphan")
    personeros = db.relationship("Personero", backref="colegio", lazy="dynamic")

    def __repr__(self):
        return f"<Colegio {self.nombre}>"

    def to_dict(self):
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "direccion": self.direccion,
            "distrito": self.distrito,
            "num_mesas": self.num_mesas,
        }


class Mesa(db.Model):
    __tablename__ = "mesas"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, nullable=False)
    colegio_id = db.Column(db.Integer, db.ForeignKey("colegios.id"), nullable=False)
    capacidad = db.Column(db.Integer, default=400)
    is_active = db.Column(db.Boolean, default=True)

    personeros = db.relationship("Personero", backref="mesa", lazy="dynamic")

    def __repr__(self):
        return f"<Mesa {self.numero} - {self.colegio.nombre}>"

    def to_dict(self):
        return {
            "id": self.id,
            "numero": self.numero,
            "colegio_id": self.colegio_id,
            "colegio_nombre": self.colegio.nombre,
            "capacidad": self.capacidad,
        }


class Personero(db.Model):
    __tablename__ = "personeros"
    __table_args__ = (
        db.Index("idx_fecha_estado", "fecha_registro", "estado"),
        db.Index("idx_colegio_fecha", "colegio_id", "fecha_registro"),
    )

    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(200), nullable=False)
    dni = db.Column(db.String(12), nullable=False, index=True)
    telefono = db.Column(db.String(20), nullable=True)
    rol = db.Column(db.String(50), nullable=False, default="Personero")
    colegio_id = db.Column(db.Integer, db.ForeignKey("colegios.id"), nullable=False)
    mesa_id = db.Column(db.Integer, db.ForeignKey("mesas.id"), nullable=False)
    numero_mesa = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="PENDIENTE")
    incidente = db.Column(db.String(200), nullable=True, default="NINGUNO")
    fecha_registro = db.Column(db.DateTime, default=peru_now)
    hora_llegada = db.Column(db.String(10), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

    def __repr__(self):
        return f"<Personero {self.dni} - {self.nombre_completo}>"

    def to_dict(self):
        return {
            "id": self.id,
            "nombre_completo": self.nombre_completo,
            "dni": self.dni,
            "telefono": self.telefono,
            "rol": self.rol,
            "colegio": self.colegio.nombre if self.colegio else "",
            "colegio_codigo": self.colegio.codigo if self.colegio else "",
            "mesa_id": self.mesa_id,
            "numero_mesa": self.numero_mesa,
            "estado": self.estado,
            "incidente": self.incidente,
            "fecha_registro": self.fecha_registro.strftime("%d/%m/%Y") if self.fecha_registro else "",
            "hora_llegada": self.hora_llegada or "",
            "ip_address": self.ip_address,
        }
