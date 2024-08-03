from flask import Blueprint, request

from model.user import User
from model.seller import Seller
from model.token import TokenBlocklist

from nanoid import generate

from connectors.mysql_connectors import connection
from sqlalchemy.orm import sessionmaker

from cerberus import Validator

from validations.user_register import user_register_schema
from validations.login import login_schema

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt,
    get_jwt_identity,
    current_user,
)

user_routes = Blueprint("user_routes", __name__)


@user_routes.route("/users", methods=["POST"])
def register_user():
    v = Validator(user_register_schema)
    request_body = {
        "email": request.form["email"],
        "password": request.form["password"],
        "role": request.form["role"],
    }

    if not v.validate(request_body):
        return {"error": v.errors}, 400

    Session = sessionmaker(connection)
    s = Session()

    s.begin()
    try:

        email = request.form["email"]
        role = request.form["role"]

        check_email = s.query(User).filter(User.email == email).first()
        if check_email:
            return {"error": "Email already exists"}, 409

        if role not in ["buyer", "seller"]:
            return {"error": "Invalid role. Must be 'buyer' or 'seller'"}, 400

        new_user_id = f"U-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"

        NewUser = User(
            user_id=new_user_id,
            email=email,
            role=role,
        )

        NewUser.set_password(request.form["password"])
        s.add(NewUser)

        if role == "seller":
            new_seller_id = f"S-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"
            NewSeller = Seller(seller_id=new_seller_id, user_id=new_user_id)
            s.add(NewSeller)

        s.commit()
        return {"message": "Register success"}, 201
    except Exception as e:
        print(f"Error during user registration: {e}")
        s.rollback()
        return {
            "error": "Failed to register, please contact admin or try again later"
        }, 500
    finally:
        s.close()


@user_routes.route("/login", methods=["POST"])
def login():
    v = Validator(login_schema)
    request_body = {
        "email": request.form.get("email"),
        "password": request.form.get("password"),
    }

    if not v.validate(request_body):
        return {"error": v.errors}, 400

    Session = sessionmaker(connection)
    s = Session()

    s.begin()
    try:

        user = s.query(User).filter(User.email == request_body["email"]).first()

        if user and user.check_password(request_body["password"]):
            access_token = create_access_token(identity=user.user_id)
            refresh_token = create_refresh_token(identity=user.user_id)

            return {
                "message": "Login successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_id": user.user_id,
                "role": user.role,
            }, 200

        else:
            return {"error": "Invalid email or password"}, 401

    except Exception as e:
        print(f"Error during login: {e}")
        return {"error": "Failed to login, please try again later"}, 500
    finally:
        s.close()


@user_routes.route("/users/", methods=["GET"])
@jwt_required()
def get_user():
    return (
        {
            "user_id": current_user.id,
            "email": current_user.email,
            "role": current_user.role,
            "created_at": current_user.created_at,
            "updated_at": current_user.updated_at,
            "profile_picture": current_user.profile_picture,
        }
    ), 200


@user_routes.get("/refresh")
@jwt_required(refresh=True)
def refresh_access():
    identity = get_jwt_identity()

    new_access_token = create_access_token(identity=identity)

    return {"access_token": new_access_token}


@user_routes.route("/logout", methods=["POST"])
@jwt_required(verify_type=False)
def logout_user():
    Session = sessionmaker(connection)
    s = Session()

    s.begin()

    try:
        jwt = get_jwt()

        jti = jwt["jti"]

        token_b = TokenBlocklist(jti=jti)

        s.add(token_b)
        s.commit()
        return ({"message": "current user has been logged out succesfully"}), 200
    except Exception as e:
        print(e)
        s.rollback()
        return ({"error": "Failed to logout, please try again later"}), 500
    finally:
        s.close()