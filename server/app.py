"""Application entry point.

`flask run` and `flask db ...` discover the `app` object here because
FLASK_APP points at this module (see .flaskenv / README).
"""

from server.config import create_app

app = create_app()


if __name__ == "__main__":
    app.run(port=5555, debug=True)
