import os

APP_PREFIX = os.getenv("APP_PREFIX", "/personeros")


class PrefixMiddleware(object):
    """Mueve la app bajo APP_PREFIX: ajusta SCRIPT_NAME/PATH_INFO para que url_for
    genere rutas con /personeros y las cookies de sesion queden en la subruta."""

    def __init__(self, app, prefix=APP_PREFIX):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        script = environ.get("SCRIPT_NAME", "") or ""
        path = environ.get("PATH_INFO", "") or ""
        if not script.startswith(self.prefix):
            script = self.prefix + script
        if path.startswith(self.prefix):
            path = path[len(self.prefix):] or "/"
        environ["SCRIPT_NAME"] = script
        environ["PATH_INFO"] = path
        return self.app(environ, start_response)


def create_app():
    from app import app as application
    application.wsgi_app = PrefixMiddleware(application.wsgi_app)
    return application


application = create_app()

if __name__ == "__main__":
    application.run(host="127.0.0.1", port=5050)