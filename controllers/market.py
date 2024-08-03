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


market_routes = Blueprint("market_routes", __name__)

@market_routes.route('/market', methods=['POST'])
@jwt_required()
def create_market():
    
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:

        seller_id = request.form["seller_id"]
        

        check_market = s.query(Market).filter(Market.seller_id == seller_id).filter()
        if len(check_market > 0):
            seller = check_market
            market_name = request.form['name']
            market_location = request.form['location']
            market_create_at = ''
            market_created_by = ''
            market_update_at = ''
            market_updated_by = ''
            market_profile = ''
            new_market = Market(
                seller_id=seller,
                name=market_name,
                location = market_location
            )
        s.add(new_market)
        s.commit()

        return {
            "success": True,
            "message": "Success create market",
            "data": new_market
        }, 201

    except Exception as e:
        s.rollback()
        return {
            "message": "error create market",
            "error": (e)
        }, 500
    finally:
        s.close()

@market_routes.route('/market', methods=['GET'])
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
            "message": "error get market",
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
    
    

