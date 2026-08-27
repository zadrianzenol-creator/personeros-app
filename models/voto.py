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

_PARTIDOS_POR_ID = {p["id"]: p for p in PARTIDOS}

# Orden y presencia de cada partido tal como aparece en la cedula de votacion
# (columna Gobernador = todos; Consejero y Provincia solo incluyen los que
# realmente figuran impresos en esa columna, en el mismo orden de la cedula).
ORDEN_CEDULA = [
    {"id": 3, "regional": True, "consejero": True, "provincia": True},    # Alianza para el Progreso
    {"id": 19, "regional": True, "consejero": False, "provincia": False},  # Salvemos al Peru
    {"id": 1, "regional": True, "consejero": True, "provincia": True},    # Accion Popular
    {"id": 18, "regional": True, "consejero": False, "provincia": False},  # Renovacion Popular
    {"id": 15, "regional": True, "consejero": True, "provincia": True},    # Partido Popular Cristiano
    {"id": 20, "regional": True, "consejero": False, "provincia": True},  # Vision Peru
    {"id": 4, "regional": True, "consejero": True, "provincia": False},   # Frente Popular Agricola
    {"id": 6, "regional": True, "consejero": True, "provincia": True},    # Fuerza Popular
    {"id": 10, "regional": True, "consejero": False, "provincia": False},  # Partido de los Trabajadores
    {"id": 13, "regional": True, "consejero": True, "provincia": True},    # Partido Politico Peru Primero
    {"id": 12, "regional": True, "consejero": True, "provincia": True},    # Partido Patriotico del Peru
    {"id": 5, "regional": True, "consejero": False, "provincia": False},  # Fuerza Ciudadana
    {"id": 11, "regional": True, "consejero": True, "provincia": False},   # Partido Pais para Todos
    {"id": 17, "regional": True, "consejero": True, "provincia": True},    # Progresemos
    {"id": 14, "regional": True, "consejero": False, "provincia": False},  # Pueblo Consciente
    {"id": 9, "regional": True, "consejero": True, "provincia": True},    # Partido Democratico Somos Peru
    {"id": 8, "regional": True, "consejero": False, "provincia": True},   # Partido Aprista Peruano
    {"id": 16, "regional": True, "consejero": True, "provincia": True},    # Podemos Peru
    {"id": 2, "regional": True, "consejero": True, "provincia": True},    # Alianza Electoral Venceremos
    {"id": 7, "regional": True, "consejero": True, "provincia": True},    # Fuerza Regional
]


def _partidos_para(clave):
    partidos = []
    for fila in ORDEN_CEDULA:
        p = dict(_PARTIDOS_POR_ID[fila["id"]])
        p["activo"] = fila[clave]
        partidos.append(p)
    return partidos


CARGOS = [
    {
        "id": "regional",
        "nombre": "Gobernador y Vicegobernador Regional",
        "nombre_corto": "Gobernador",
        "color": "#eab308",
        "color_bg": "rgba(234,179,8,0.12)",
        "color_border": "rgba(234,179,8,0.3)",
        "color_solido": "#f5e011",
        "imagen_folder": "partidos",
        "icono": "landmark",
        "partidos": _partidos_para("regional"),
    },
    {
        "id": "consejero",
        "nombre": "Consejero Regional - Provincia de Piura",
        "nombre_corto": "Consejero",
        "color": "#16a34a",
        "color_bg": "rgba(22,163,74,0.12)",
        "color_border": "rgba(22,163,74,0.3)",
        "color_solido": "#90fe2c",
        "imagen_folder": "partidos_consejero_icon",
        "icono": "chart-bar",
        "partidos": _partidos_para("consejero"),
    },
    {
        "id": "provincia",
        "nombre": "Provincia de Morropon",
        "nombre_corto": "Provincial",
        "color": "#db2777",
        "color_bg": "rgba(219,39,119,0.12)",
        "color_border": "rgba(219,39,119,0.3)",
        "color_solido": "#f6d5f9",
        "imagen_folder": "partidos_provincia_icon",
        "icono": "city",
        "partidos": _partidos_para("provincia"),
    },
]

_CARGOS_POR_ID = {c["id"]: c for c in CARGOS}


class Voto(db.Model):
    __tablename__ = "votos"
    __table_args__ = (
        db.Index("idx_mesa_colegio", "mesa_id", "colegio_id"),
        db.Index("idx_mesa_cargo", "mesa_id", "cargo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey("mesas.id"), nullable=False)
    colegio_id = db.Column(db.Integer, db.ForeignKey("colegios.id"), nullable=False)
    partido_id = db.Column(db.Integer, nullable=False)
    partido_nombre = db.Column(db.String(150), nullable=False)
    partido_sigla = db.Column(db.String(20), nullable=False)
    cargo = db.Column(db.String(50), nullable=False, default="regional")
    votos = db.Column(db.Integer, nullable=False, default=0)
    fecha_registro = db.Column(db.DateTime, default=peru_now)
    registrado_por = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    personero_id = db.Column(db.Integer, db.ForeignKey("personeros.id"), nullable=True)

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
            "cargo": self.cargo,
            "votos": self.votos,
            "fecha": self.fecha_registro.strftime("%d/%m/%Y %H:%M") if self.fecha_registro else "",
        }


class VotoEspecial(db.Model):
    __tablename__ = "votos_especiales"
    __table_args__ = (
        db.Index("idx_vesp_mesa_cargo", "mesa_id", "cargo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey("mesas.id"), nullable=False)
    colegio_id = db.Column(db.Integer, db.ForeignKey("colegios.id"), nullable=False)
    cargo = db.Column(db.String(50), nullable=False, default="regional")
    tipo = db.Column(db.String(50), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    fecha_registro = db.Column(db.DateTime, default=peru_now)
    registrado_por = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    personero_id = db.Column(db.Integer, db.ForeignKey("personeros.id"), nullable=True)

    mesa = db.relationship("Mesa", backref="votos_especiales")
    colegio = db.relationship("Colegio", backref="votos_especiales")

    def to_dict(self):
        return {
            "id": self.id,
            "mesa_id": self.mesa_id,
            "colegio_id": self.colegio_id,
            "colegio_nombre": self.colegio.nombre if self.colegio else "",
            "mesa_numero": self.mesa.numero if self.mesa else 0,
            "cargo": self.cargo,
            "tipo": self.tipo,
            "cantidad": self.cantidad,
            "fecha": self.fecha_registro.strftime("%d/%m/%Y %H:%M") if self.fecha_registro else "",
        }
