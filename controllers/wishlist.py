from flask import Blueprint, request
from model.wishllist import Wishlist
from model.product import Product
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user

from connectors.mysql_connectors import connection
from sqlalchemy.orm import sessionmaker
import os

wishlist_routes = Blueprint('wishlist_routes', __name__)
R2_DOMAINS=os.getenv('R2_DOMAINS')
@wishlist_routes.route('/wishlist', methods=['GET'])
@jwt_required()
def show_wishist():
    user_id = current_user.user_id
    
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        wishlist = []
        get_withlist = s.query(Wishlist).filter(Wishlist.user_id==user_id).all()
        if len(get_withlist) < 1:
            return {
                "title": "Fetching wishlist",
                "message": "Wishlist empty"
            }, 404
        
        
       
        for row in get_withlist: 
            products = s.query(Product).filter(Product.id==row.product_id).first()
          
            wishlist.append({
                "name":products.name,
                "price": products.price,
                "stock": products.stock,
                "images": f"{R2_DOMAINS}/{products.images}"
            })

        
        # print(wishlist)
        return {
            "title": "Fetching wishlist",
            "message": "Success get wishlist",
            "wishlist": wishlist
        }, 200
    except Exception as e:
        return {
            "title": "error connection",
            "message": (e)
        },500
    finally:
        s.close()

@wishlist_routes.route('/wishlist', methods=['POST'])
@jwt_required()
def create_wishlist():
    user_id = current_user.user_id
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        
        product_id = request.form['product_id']
        print(user_id)

        check_product = s.query(Product).filter(Product.id==product_id).first()
        print(check_product)
      
        if check_product is None: 
            return {
                "title": "add a new wishlist",
                "message": "Product not found"
            }, 400
        
        check_on_wishlist = s.query(Wishlist).filter(Wishlist.user_id==user_id).filter(Wishlist.product_id==product_id).all()

        if len(check_on_wishlist) > 0 :
            return {
                "title": "adding wishlist",
                "message": "this product already exist on your wishlist"
            }, 400
    
        add_wishlist = Wishlist(
            user_id=user_id,
            product_id=product_id
        )

        s.add(add_wishlist)
        s.commit()
        return {
            "message": "Successfully add new wishlist",
            "title": "add a new wishlist"
        }, 201
    except Exception as e: 
        s.rollback()
        return {
            "title": "Error handling server",
            "message": (e)
        }, 500
    
    finally:
        s.close()

@wishlist_routes.route('/wishlist/<int:id>', methods=['DELETE'])
@jwt_required(id)
def remove_wishlist():
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try: 
        wishlist = s.query(Wishlist).filter(Wishlist.id==id).first()
        s.delete(wishlist)
        s.commit()
        return {
            "message": "wishlist removed"
        }, 200
    except Exception as e:
        s.rollback()
        return {
            "title": "Error handling server",
            "message": (e)
        }, 500
    finally:
        s.close()