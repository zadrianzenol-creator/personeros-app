from database import db, peru_now


PARTIDOS = [
    {"id": 1, "nombre": "Accion Popular", "sigla": "AP", "imagen": "accion_popular.png"},
    {"id": 2, "nombre": "Alianza Electoral Venceremos", "sigla": "VE", "imagen": "alianza_electoral_venceremos.png"},
    {"id": 3, "nombre": "Alianza para el Progreso", "sigla": "APP", "imagen": "alianza_para_el_progreso.png"},
    {"id": 4, "nombre": "Frente Popular Agricola del Peru", "sigla": "FREPAP", "imagen": "frente_popular_agricola_fia_del_peru.png"},
    {"id": 5, "nombre": "Fuerza Ciudadana", "sigla": "FC", "imagen": "fuerza_ciudadana.png"},
    {"id": 6, "nombre": "Fuerza Popular", "sigla": "FP", "imagen": "fuerza_popular.png"},
    {"id": 7, "nombre": "Fuerza Regional", "sigla": "FR", "imagen": "fuerza_regional.png"},
    {"id": 8, "nombre": "Partido Aprista Peruano", "sigla": "APRA", "imagen": "partido_aprista_peruano.png"},
    {"id": 9, "nombre": "Partido Democratico Somos Peru", "sigla": "SP", "imagen": "partido_democratico_somos_peru.png"},
    {"id": 10, "nombre": "Partido de los Trabajadores y Emprendedores", "sigla": "PTE", "imagen": "partido_de_los_trabajadores_y_emprendedores_del_peru.png"},
    {"id": 11, "nombre": "Partido Pais para Todos", "sigla": "PPT", "imagen": "partido_pais_para_todos.png"},
    {"id": 12, "nombre": "Partido Patriotico del Peru", "sigla": "PPP", "imagen": "partido_patriotico_del_peru.png"},
    {"id": 13, "nombre": "Partido Politico Peru Primero", "sigla": "PP", "imagen": "partido_politico_peru_primero.png"},
    {"id": 14, "nombre": "Partido Politico Pueblo Consciente", "sigla": "PPC", "imagen": "partido_politico_pueblo_consciente.png"},
    {"id": 15, "nombre": "Partido Popular Cristiano", "sigla": "PPK", "imagen": "partido_popular_cristiano.png"},
    {"id": 16, "nombre": "Podemos Peru", "sigla": "PodP", "imagen": "podemos_peru.png"},
    {"id": 17, "nombre": "Progresemos", "sigla": "PRO", "imagen": "progresemos.png"},
    {"id": 18, "nombre": "Renovacion Popular", "sigla": "RP", "imagen": "renovacion_popular.png"},
    {"id": 19, "nombre": "Salvemos al Peru", "sigla": "SP", "imagen": "salvemos_al_peru.png"},
    {"id": 20, "nombre": "Vision Peru", "sigla": "VP", "imagen": "vision_peru.png"},
]


class Voto(db.Model):
    __tablename__ = "votos"
    __table_args__ = (
        db.Index("idx_mesa_colegio", "mesa_id", "colegio_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey("mesas.id"), nullable=False)
    colegio_id = db.Column(db.Integer, db.ForeignKey("colegios.id"), nullable=False)
    partido_id = db.Column(db.Integer, nullable=False)
    partido_nombre = db.Column(db.String(150), nullable=False)
    partido_sigla = db.Column(db.String(20), nullable=False)
    votos = db.Column(db.Integer, nullable=False, default=0)
    fecha_registro = db.Column(db.DateTime, default=peru_now)
    registrado_por = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    mesa = db.relationship("Mesa", backref="votos_registrados")
    colegio = db.relationship("Colegio", backref="votos_registrados")

    def to_dict(self):
        return {
            "id": self.id,
            "mesa_id": self.mesa_id,
            "colegio_id": self.colegio_id,
            "colegio_nombre": self.colegio.nombre if self.colegio else "",
            "mesa_numero": self.mesa.numero if self.mesa else 0,
            "partido_id": self.partido_id,
            "partido_nombre": self.partido_nombre,
            "partido_sigla": self.partido_sigla,
            "votos": self.votos,
            "fecha": self.fecha_registro.strftime("%d/%m/%Y %H:%M") if self.fecha_registro else "",
        }


class VotoEspecial(db.Model):
    __tablename__ = "votos_especiales"

    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey("mesas.id"), nullable=False)
    colegio_id = db.Column(db.Integer, db.ForeignKey("colegios.id"), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    fecha_registro = db.Column(db.DateTime, default=peru_now)
    registrado_por = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    mesa = db.relationship("Mesa", backref="votos_especiales")
    colegio = db.relationship("Colegio", backref="votos_especiales")

    def to_dict(self):
        return {
            "id": self.id,
            "mesa_id": self.mesa_id,
            "colegio_id": self.colegio_id,
            "colegio_nombre": self.colegio.nombre if self.colegio else "",
            "mesa_numero": self.mesa.numero if self.mesa else 0,
            "tipo": self.tipo,
            "cantidad": self.cantidad,
            "fecha": self.fecha_registro.strftime("%d/%m/%Y %H:%M") if self.fecha_registro else "",
        }
