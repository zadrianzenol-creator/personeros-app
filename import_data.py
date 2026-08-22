#!/usr/bin/env python3
"""Import data from Excel file into the database."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import openpyxl
from app import create_app
from database import db
from models.personero import Colegio, Mesa, Personero
from models.voto import Voto, VotoEspecial
from models.user import User

EXCEL_PATH = r"C:\Users\ZURIEL\Downloads\locales de votaciones (2) - copia.xlsx"


def clean_db():
    print("Limpiando base de datos...")
    db.drop_all()
    db.create_all()
    print("  Tablas recreadas.")


def import_data():
    print("Importando datos desde Excel...")
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb["mesas"]

    locales = {}
    mesas_map = {}
    personeros_data = []

    for row in ws.iter_rows(min_row=2, values_only=True):
        id_mesa = row[0]
        id_local = row[1]
        nombre_local = row[2]
        num_mesa = row[3]
        dni = row[4]
        nombres = row[5]
        apellidos = row[6]
        celular = row[7]

        if not id_local or not nombre_local:
            continue

        nombre_local = str(nombre_local).strip()

        if id_local not in locales:
            locales[id_local] = {
                "codigo": f"LOC-{id_local}",
                "nombre": nombre_local,
                "distrito": "Chulucanas",
            }

        mesa_key = (id_local, num_mesa)
        if mesa_key not in mesas_map and num_mesa:
            mesas_map[mesa_key] = {
                "numero": int(num_mesa) if num_mesa else 0,
                "colegio_id_ref": id_local,
            }

        if dni and nombres and apellidos:
            personeros_data.append({
                "id_local": id_local,
                "num_mesa": str(num_mesa).strip() if num_mesa else "",
                "dni": str(dni).strip(),
                "nombres": str(nombres).strip(),
                "apellidos": str(apellidos).strip(),
                "celular": str(celular).strip() if celular else "",
            })

    print(f"  {len(locales)} locales encontrados")
    print(f"  {len(mesas_map)} mesas encontradas")
    print(f"  {len(personeros_data)} personeros con datos")

    colegio_db_map = {}
    for id_local, data in locales.items():
        colegio = Colegio(
            codigo=data["codigo"],
            nombre=data["nombre"],
            distrito=data["distrito"],
            num_mesas=0,
        )
        db.session.add(colegio)
        db.session.flush()
        colegio_db_map[id_local] = colegio

    mesa_db_map = {}
    mesa_count_per_colegio = {}
    for (id_local, num_mesa), data in mesas_map.items():
        if id_local not in colegio_db_map:
            continue
        colegio = colegio_db_map[id_local]
        mesa = Mesa(
            numero=data["numero"],
            colegio_id=colegio.id,
            capacidad=400,
        )
        db.session.add(mesa)
        db.session.flush()
        mesa_db_map[(id_local, data["numero"])] = mesa
        mesa_count_per_colegio[id_local] = mesa_count_per_colegio.get(id_local, 0) + 1

    for id_local, count in mesa_count_per_colegio.items():
        if id_local in colegio_db_map:
            colegio_db_map[id_local].num_mesas = count

    contador = 0
    for i, p in enumerate(personeros_data, 1):
        id_local = p["id_local"]
        if id_local not in colegio_db_map:
            continue

        try:
            num_mesa = int(p["num_mesa"]) if p["num_mesa"] else 0
        except ValueError:
            num_mesa = 0

        mesa = mesa_db_map.get((id_local, num_mesa))
        if not mesa:
            continue

        nombre_completo = f"{p['nombres']} {p['apellidos']}".strip()
        codigo = f"PER-{i:06d}"

        personero = Personero(
            codigo=codigo,
            nombre_completo=nombre_completo,
            dni=p["dni"],
            telefono=p["celular"],
            rol="Personero",
            colegio_id=colegio_db_map[id_local].id,
            mesa_id=mesa.id,
            numero_mesa=num_mesa,
            estado="PENDIENTE",
            incidente="NINGUNO",
        )
        db.session.add(personero)
        contador += 1

    db.session.commit()
    print(f"  {contador} personeros importados correctamente.")


def seed_admin():
    admin = User(
        username="admin",
        full_name="Administrador",
        role="admin",
        is_active=True,
    )
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    print("  Admin creado (admin / admin123)")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        clean_db()
        import_data()
        seed_admin()
        print("\nImportacion completada.")
