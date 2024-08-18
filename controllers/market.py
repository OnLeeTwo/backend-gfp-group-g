from flask import Blueprint, request, jsonify
from model.market import Market
from model.seller import Seller
from nanoid import generate
from connectors.mysql_connectors import connection
from sqlalchemy.orm import sessionmaker
from services.logActions import LogManager
from services.upload import UploadService
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    current_user
)  

import os
from datetime import datetime
upload_service = UploadService()
R2_DOMAINS=os.getenv('R2_DOMAINS')
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
market_routes = Blueprint("market_routes", __name__)

@market_routes.route('/markets', methods=['POST'])
@jwt_required()
def create_market():
    
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        user_id=current_user.user_id
        market_name = request.form["name"]
        market_seller = request.form["seller_id"]
        market_location = request.form["location"]
        # Pastikan bahwa user tersebut adalah seller. cara ceknya adalah mengecek di table seller
        check_market = s.query(Seller).filter(Seller.user_id == user_id).first()
        
        if check_market is None:
            return {
                "error": "Seller not found"
                }, 404
         
        id=f"M-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"

        new_filename=""
        if "images" in request.files:
            file = request.files["images"]
            if file.filename == "":
                return {"error": "No selected file"}, 400
            if file and allowed_file(file.filename):
                filename = file.filename
                ext_name = os.path.splitext(filename)[1]
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                new_filename = f"{id}-{timestamp}{ext_name}"
                try:    
                    upload_service.upload_file(file, new_filename)
                except Exception as e:
                    return {"error": str(e)}, 500
            else:
                return {"error": "file type not allowed"}, 415


        newMarket = Market(
            market_id = id,
            name = market_name,
            seller_id = market_seller,
            profile_picture=new_filename,
            location = market_location,
            created_by = user_id,
            updated_by = user_id
        )

        market_dict = newMarket.__dict__
        market_dict = {key: value for key, value in market_dict.items() if not key.startswith('_')}
        s.add(newMarket)
        s.commit()
        log_manager = LogManager(user_id=user_id, action='CREATE_MARKET')
        log_manager.set_after(after_data=str(market_dict))
        log_manager.save()
        return {
            "success": True,
            "message": "Success create market",
            "market": market_dict
        }, 201
    except Exception as e:
        s.rollback()
        return {
            "message": "error create market",
            "error": str(e)
        }, 500
    finally:
        s.close()

@market_routes.route('/markets', methods=['GET'])
def markets_all():
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        markets = []
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        name = request.args.get('name', '', type=str)
        offset = (page - 1) * per_page
        query = s.query(Market)
        if name != '':
            query = query.filter(Market.name.ilike(f'%{name}%'))

            
        
        query_all = query.offset(offset).limit(per_page)
        data = query_all.all()
        total_market = query.count()
        total_pages =(total_market + per_page - 1) // per_page
        for row in data:
            seller = s.query(Seller).filter(Seller.seller_id == row.seller_id).first()
            if seller:
                markets.append({
                    "market_id": row.market_id,
                    "seller_id": seller.seller_id,
                    "market_name": row.name,
                    "profile_pict": f"{R2_DOMAINS}/{row.profile_picture}",
                    "location": row.location,
                })
        if len(markets) < 1: 
            return {
                "message": "Market is empty"
            }, 404
        
        return {
            "success": True,
            "data": markets,
            'total_pages': total_pages,
            'current_page': page,
            'per_page': per_page,
            'total_items': total_market,
        }, 200
    except Exception as e:
        s.rollback()
        return jsonify({
            "message": "error get markets",
            "error": str(e)  # Convert exception to string
        }), 500
    finally:
        s.close()

@market_routes.route('/markets/<id>', methods=['GET'])
def market_by_id(id):
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        market = s.query(Market).filter(Market.market_id == id).first()
        if market:
            seller = s.query(Seller).filter(Seller.seller_id == market.seller_id).first()
            if seller:
                return jsonify({
                    "market_id": market.market_id,
                    "seller_id": seller.seller_id,
                    "market_name": market.name,
                    "location": market.location,
                }), 200
            else:
                return {
                    "message": "Seller not found"
                }, 404
        else:
            return {
                "message": "Market not found"
            }, 404
    except Exception as e:
        s.rollback()
        return {
            "message": "Error getting market",
            "error": str(e)  # Convert exception to string
        }, 500
    finally:
        s.close()

@market_routes.route('/markets/<id>', methods=["PUT"])
@jwt_required()
def market_product(id):
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try: 
        user_id=current_user.user_id
        log_manager = LogManager(user_id=user_id, action='UPDATE_MARKET')
        market = s.query(Market).filter(Market.market_id == id).first()
        market_dict = vars(market)
        market_str = str({key: value for key, value in market_dict.items() if not key.startswith('_')})
     
        if market is None:
            return {
                "message": "product not found"
            }, 404
        
        current_user_id = get_jwt_identity()
        name=request.form['name']
        location=request.form['location']

        
        market.name=name
        market.location=location
        market.updated_by=current_user_id

        new_filename = market.profile_picture
        if "images" in request.files:
            file = request.files["images"]
            if file.filename == "":
                return {"error": "No selected file"}, 400
            if file and allowed_file(file.filename):

                filename = file.filename
                ext_name = os.path.splitext(filename)[1]
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                new_filename = f"{id}-{timestamp}{ext_name}"

                try:
                    upload_service.upload_file(file, new_filename)
                except Exception as e:
                    return {"error": str(e)}, 500
            else:
                return {"error": "file type not allowed"}, 415
        

        market_dict = market.__dict__
        market_dict = {key: value for key, value in market_dict.items() if not key.startswith('_')}
        s.commit()
        log_manager.set_before(before_data=market_str)
        log_manager.set_after(after_data=str(market_dict))
        log_manager.save()
        return {
            "message": "Updated product success",
            "success": True
        },201
    except Exception as e:
        s.rollback()
        return {
            "message": "error update product",
            "error": str(e)
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
        log_manager = LogManager(user_id=current_user.user_id, action="DELETE_MARKET")
        market = s.query(Market).filter(Market.market_id == id).first()
        if market is None:
            return jsonify({
                "message": "Market not found"
            }), 404
        market_dict = vars(market)
        market_str = str({key: value for key, value in market_dict.items() if not key.startswith('_')})
        s.delete(market)
        s.commit()

        log_manager.set_before(before_data=market_str)
        log_manager.save()
        return jsonify({
            "success": True,
            "message": "Success delete market"
        }), 200


     
    except Exception as e:
        s.rollback()
        return jsonify({
            "message": "Error deleting market",
            "error": str(e)  # Convert exception to string
        }), 500
    finally:
        s.close()