"""Servidor de producción para Windows (gunicorn no corre en Windows).

Se usa junto con el Programador de servicios de Windows (NSSM) para que el
sistema quede siempre activo, y con cloudflared para exponerlo con URL pública.
"""

import logging

from waitress import serve

from app import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

if __name__ == "__main__":
    # Solo localhost: cloudflared es el único que debe hablar con este puerto.
    serve(app, host="127.0.0.1", port=8001, threads=8, channel_timeout=120)
