from flask import Blueprint, request
from model.market import Market
from model.seller import Seller
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
        check_market = s.query(Seller).filter(Seller.user_id == request.form['seller']).filter()
        new_market_id = f"M-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"
        if len(check_market > 0):
            seller = check_market.id
        else:
            seller = f"M-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"
            new_category = Seller(
                id = seller,
                name=request.form['seller']
            )
            s.add(new_category)
            s.commit()
        
        market_name = request.form['name']
        market_location = request.form['location']
        market_create_at = ''
        market_created_by = ''
        market_update_at = ''
        market_updated_by = ''
        market_profile = ''
        new_product = Market(
            id=new_market_id,
            seller_id=seller,
            name=market_name,
            location = market_location
        )

        s.add(new_product)
        s.commit()

        return {
            "success": True,
            "message": "Success create product",
            "data": new_product
        }, 201

    except Exception as e:
        s.rollback()
        return {
            "message": "error create product",
            "error": (e)
        }, 500
    finally:
        s.close()

@market_routes.route('/products', methods=['GET'])
@jwt_required()
def markets_all():

    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        market = s.query(Market).filter(Market.is_deleted!=1).all()
        if len(market) < 1: 
            return {
                "message": "Markets is empty"
            }, 404
        
        return {
            "success": True,
            "data": market
        }
    except Exception as e:
        return {
            "message": "error get products",
            "error": (e)
        }
    finally:
        s.close()

@market_routes.route('/market/<id>', methods=['GET'])
@jwt_required()
def markets_by_id(id):
     
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        markets = s.query(Market).filter(Market.is_deleted!=1).filter(Market.id == id).first()
        if len(markets) < 1: 
            return {
                "message": "Markets is empty"
            }, 404
        
        return {
            "success": True,
            "data": markets
        }, 200
    except Exception as e:
        return {
            "message": "error get markets",
            "error": (e)
        }, 500
    finally:
        s.close()
    
    

