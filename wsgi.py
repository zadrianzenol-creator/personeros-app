from app import app as application  # noqa: N883  (entry point WSGI para hosting)

if __name__ == "__main__":
    application.run(host="127.0.0.1", port=5050)