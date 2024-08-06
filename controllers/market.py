from flask import Blueprint, request
from model.market import Market
from model.seller import Seller
from model.user import User
from sqlalchemy import func
from nanoid import generate
from connectors.mysql_connectors import connection
from sqlalchemy.orm import sessionmaker

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)  


market_routes = Blueprint("market_routes", __name__)

@market_routes.route('/markets', methods=['POST'])
@jwt_required()
def create_market():
    
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        current_user_id = get_jwt_identity()
        market_name = request.form["name"]
        market_seller = request.form["seller_id"]
        market_location = request.form["location"]

        check_market = s.query(Seller).filter(Seller.seller_id == market_seller).first()
        user_market = s.query(User).filter(User.user_id == Seller.user_id).first()
        if check_market:
            newMarket = Market(
                market_id = f"M-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}",
                name = market_name,
                seller_id = market_seller,
                location = market_location,
                created_by = current_user_id,
                updated_by = current_user_id
            )
        elif user_market:
            newMarket = Market(
                market_id = f"M-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}",
                name = market_name,
                seller_id = market_seller,
                location = market_location,
                created_by = current_user_id,
                updated_by = current_user_id
            )
        else:
            return {
                "error": "Seller not found"
                }
        s.add(newMarket)
        s.commit()
        return {
            "success": True,
            "message": "Success create market"
        }, 201
    except Exception as e:
        s.rollback()
        return {
            "message": "error create market",
            "error": e
        }, 500
    finally:
        s.close()

@market_routes.route('/markets', methods=['GET'])
def markets_all():
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        markets =[]
        print(markets)
        data = s.query(Market).filter(Market.is_deleted==0).all()
        for row in data:
            seller = s.query(Seller).filter(Seller.seller_id == row.seller_id).first()
            markets.append({
                "market_id": row.market_id,
                "seller_id": seller.seller_id,
                "market_name": row.name,
                "location": row.location,
            })
        if len(markets) < 1: 
            return {
                "message": "Market is empty"
            }, 404
        
        return {
            "success": True,
            "data": markets
        }, 200
    except Exception as e:
        s.rollback()
        return {
            "message": "error get market",
            "error": (e)
        }
    finally:
        s.close()

@market_routes.route('/markets/<id>', methods=['GET'])
def market_by_id(id):
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        market = []
        markets = s.query(market_routes).filter(Market.market_id== id).filter(Market.is_deleted==0).first()
        if markets is None:
            return {
                "message": "market not found"
            }, 404
        category = s.query(Seller).filter(Seller.seller_id==markets.seller_id).first()
        market.append({
            "market_id": markets.market_id,
            "seller_id": markets.seller_id,
            "name" : markets.name,
            "location": markets.location,
        })
        
        return {
            "success": True,
            "data": market
        }, 200
    except Exception as e:
        s.rollback()
        return {
            "message": "error get markets",
            "error": (e)
        }, 500
    finally:
        s.close()

@market_routes.route('/markets/<id>', methods=["DELETE"])
@jwt_required()
def delete_product(id):
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        market = s.query(Market).filter(Market.market_id==id).filter(Market.is_deleted==0).first()
        if market is None:
            return {
                "message": "market not found"
            }, 404
        market.is_deleted = 1
        market.time_deleted = func.now()
        s.commit()
        return {
            "success": True,
            "message": "Success delete market"
        }, 200
        
    except Exception as e:
        s.rollback()
        return {
            "message": "error delete market",
            "error": (e)
        }, 500
    finally:
        s.close()