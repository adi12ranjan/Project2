from flask import Flask, send_from_directory
from flask_cors import CORS
from .db import init_db


def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config['JSON_SORT_KEYS'] = False
    CORS(app, resources={r'/api/*': {'origins': '*'}})
    init_db(app)

    from .routes import api
    app.register_blueprint(api, url_prefix='/api')

    @app.get('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    return app
