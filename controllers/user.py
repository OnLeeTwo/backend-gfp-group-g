from flask import Blueprint, request, json, make_response
from datetime import datetime, UTC, timedelta
import os

from model.user import User
from model.seller import Seller
from model.token import TokenBlocklist

from validations.user_register import user_register_schema
from validations.login import login_schema
from validations.user_update import user_update_schema

from services.upload import UploadService

from connectors.mysql_connectors import connection
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from nanoid import generate
from cerberus import Validator
import os
import os
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt,
    get_jwt_identity,
    current_user,
    decode_token,
)

user_routes = Blueprint("user_routes", __name__)
R2_DOMAINS = os.getenv("R2_DOMAINS")
upload_service = UploadService()

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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

        new_user_id = f"U-{generate(' 1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"

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
        "email": request.form["email"],
        "password": request.form["password"],
    }

    if not v.validate(request_body):
        return {"error": v.errors}, 400

    Session = sessionmaker(connection)
    s = Session()

    s.begin()
    try:
        user = (
            s.query(User)
            .filter(User.email == request_body["email"])
            .filter(User.is_deleted != True)
            .first()
        )

        if user is None:

            return {"error": "Email not found"}, 404
        if user and user.check_password(request_body["password"]):
            access_token = create_access_token(
                identity=user,
                additional_claims={
                    "email": user.email,
                    "user_id": user.user_id,
                    "role": user.role,
                },
            )
            refresh_token = create_refresh_token(identity=user)

            return {
                "message": "Login successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_id": user.user_id,
                "role": user.role,
            }, 200

        else:
            s.rollback()
            return {"error": "Invalid email or password"}, 401

    except Exception as e:
        s.rollback()
        print(f"Error during login: {e}")
        return {"error": "Failed to login, please try again later"}, 500
    finally:
        s.close()


@user_routes.route("/users", methods=["GET"])
@jwt_required()
def get_user():

    data = {
        "user_id": current_user.user_id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "profile_picture": f"{R2_DOMAINS}/{current_user.profile_picture}",
        "address": current_user.address,
    }
    return {"success": "data fetched successfully", "data": data}, 200


@user_routes.route("/users", methods=["PUT"])
@jwt_required()
def update_user():
    v = Validator(user_update_schema, allow_unknown=True)

    request_body = {}

    if "email" in request.form:
        request_body["email"] = request.form["email"]

    if "password" in request.form:
        request_body["password"] = request.form["password"]

    if "name" in request.form:
        request_body["name"] = request.form["name"]

    if "address" in request.form:
        try:
            address_data = json.loads(request.form["address"])
            request_body["address"] = address_data
        except json.JSONDecodeError:
            return {"error": "Invalid address format"}, 400

    if not v.validate(request_body):
        return {"error": v.errors}, 400

    current_user_id = get_jwt_identity()
    Session = sessionmaker(connection)
    s = Session()

    s.begin()

    try:
        user = s.query(User).filter(User.user_id == current_user_id).first()
        if not user:
            return {"error": "User not found"}, 404

        if "email" in request_body:
            user.email = request_body["email"]
        if "password" in request_body:
            user.set_password(request_body["password"])
        if "name" in request_body:
            user.name = request_body["name"]
        if "address" in request_body:
            user.address = request_body["address"]

        user.updated_at = func.now()

        if "profile_picture" in request.files:
            file = request.files["profile_picture"]
            if file.filename == "":
                return {"error": "No selected file"}, 400
            if file and allowed_file(file.filename):

                filename = file.filename
                ext_name = os.path.splitext(filename)[1]
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                new_filename = f"{user.user_id}-{timestamp}{ext_name}"

                try:
                    upload_service.upload_file(file, new_filename)
                except Exception as e:
                    return {"error": str(e)}, 500
            else:
                return {"error": "file type not allowed"}, 415

        s.commit()
        return {"message": "User updated successfully"}, 200
    except Exception as e:
        s.rollback()
        print(f"Error updating user: {e}")
        return {"error": "Failed to update user"}, 500
    finally:
        s.close()


@user_routes.route("/users", methods=["DELETE"])
@jwt_required()
def delete_user():
    current_user_id = get_jwt_identity()
    Session = sessionmaker(connection)
    s = Session()

    s.begin()
    try:
        user = s.query(User).filter(User.user_id == current_user_id).first()
        if not user:
            return {"error": "User not found"}, 404

        user.is_deleted = True
        user.time_deleted = datetime.now(UTC)

        s.commit()
        return {"message": "User deleted successfully"}, 200
    except Exception as e:
        s.rollback()
        print(f"Error deleting user: {e}")
        return {"error": "Failed to delete user"}, 500
    finally:
        s.close()


@user_routes.route("/refresh", methods=["POST"])
def refresh_token():
    data = request.get_json()
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return {"error": "Refresh token is required"}, 400

    try:
        decode_token(refresh_token, options={"verify_exp": True})

        current_user = get_jwt_identity()
        access_token = create_access_token(
            identity=current_user, expires_delta=timedelta(hours=1)
        )

        return {"access_token": access_token}, 200

    except Exception as e:
        return {"error": str(e)}, 401


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
