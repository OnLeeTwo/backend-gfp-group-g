from flask import Blueprint, request, json, make_response
from datetime import datetime, UTC, timedelta
import os

from model.seller import Seller

from connectors.mysql_connectors import connection
from sqlalchemy.orm import sessionmaker

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)

seller_routes = Blueprint("seller_routes", __name__)

@seller_routes.route("/seller", methods=["GET"])
@jwt_required()
def get_seller():
    current_user_id = get_jwt_identity()
    Session = sessionmaker(connection)
    s = Session()

    s.begin()

    try:
        seller = s.query(Seller).filter(Seller.user_id == current_user_id).first()

        if seller:
            return ({"seller_id": seller.seller_id}), 200

        else:
            return {"message": "Seller not found"}, 404
    except:
        s.rollback()
    finally:
        s.close()
