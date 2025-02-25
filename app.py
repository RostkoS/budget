from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from models import db
from utils import get_user
from config import Config

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    @app.context_processor
    def inject_user():
        return dict(get_user=get_user)
    db.init_app(app)
    mail.init_app(app)
    from routes.auth import auth
    from routes.records import records
    from routes.family import family

    app.register_blueprint(auth)
    app.register_blueprint(records)
    app.register_blueprint(family)
    with app.app_context():
        db.create_all()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
