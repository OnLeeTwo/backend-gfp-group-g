from flask import Flask
from dotenv import load_dotenv
from datetime import timedelta
import os

from flask_jwt_extended import JWTManager
from sqlalchemy.orm import sessionmaker
from connectors.mysql_connectors import connection

from model.user import User
from model.token import TokenBlocklist

from controllers.user import user_routes

load_dotenv()

app = Flask(__name__)
jwt = JWTManager(app)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(hours=8)

username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
database = os.getenv("DB_DATABASE")

app.register_blueprint(user_routes)


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.user_id


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    Session = sessionmaker(connection)
    s = Session()

    user = s.query(User).filter(User.user_id == identity).first()
    return user


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_data):
    return ({"message": "Token has expired", "error": "token_expired"}), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return (
        ({"message": "Signature verification failed", "error": "invalid_token"}),
        401,
    )


@jwt.unauthorized_loader
def missing_token_callback(error):
    return (
        (
            {
                "message": "Request doesnt contain valid token",
                "error": "authorization_header",
            }
        ),
        401,
    )


@jwt.token_in_blocklist_loader
def token_in_blocklist_callback(jwt_header, jwt_data):
    Session = sessionmaker(connection)
    s = Session()

    jti = jwt_data["jti"]

    token = s.query(TokenBlocklist).filter(TokenBlocklist.jti == jti).scalar()

    return token is not None


@app.route("/")
def hello_world():
    return "Hello World"


if __name__ == "__main__":
    app.run(debug=True)
