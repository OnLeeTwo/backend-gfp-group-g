from flask import Blueprint, request
from model.market import Market
from nanoid import generate
from connectors.mysql_connectors import connection
from sqlalchemy.orm import sessionmaker

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt,
    get_jwt_identity,
    current_user,
)

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt,
    get_jwt_identity,
    current_user,
)


market_routes = Blueprint("market_routes", __name__)

@market_routes.route('/market', methods=['POST'])
@jwt_required
def create_market():
    
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        new_market_id = f"M-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"
        market_name = request.form["name"]
        market_create_at = request.form["created_at"]
        market_update_at = request.form["updated_at"]
        market_created_by = request.form["created_by"]
        market_updated_by = request.form["updated_by"]
        market_location = request.form["location"]
        market_profile = request.form["profile_picture"]
        new_market = Market(
            id=new_market_id
        )
        return{
            "success": True,
            "message": "Market created successfully",
            "name": market_name,
            "location": market_location
        }
    except Exception as e:
        s.rollback()
        return {"message": "Error creating market"}, 500
    
    

