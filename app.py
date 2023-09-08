import os
from flask import Flask
from flask_jwt_extended import JWTManager
from api import *
from models import Base, engine

base_url = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['static_url_path'] = '/static'
app.config['static_folder'] = ''
jwt = JWTManager(app)
jwt.init_app(app)

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(user_bp, url_prefix='/user')


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    user_id = jwt_data["sub"]
    with Session() as session:
        user = session.query(User).filter_by(id=user_id).first()
    
    return user

if __name__ == '__main__':
    with app.app_context():
        Base.metadata.create_all(engine)
    
    app.run(debug=True)
