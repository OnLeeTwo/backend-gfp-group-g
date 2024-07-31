from flask import Blueprint, request
from model.product import Product

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

product_routes = Blueprint("product_routes", __name__)

@product_routes.route('/products', methods=['GET'])

def products_all():

    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        products = s.query(Product).filter(Product.is_deleted!=1).all()
        if len(products) < 1: 
            return {
                "message": "Products is empty"
            }, 404
        
        return {
            "success": True,
            "data": products
        }
    except Exception as e:
        return {
            "message": "error get products",
            "error": (e)
        }
    finally:
        s.close()

@product_routes.route('/product/<id>', methods=['GET'])
def product_by_id(id):
     
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        products = s.query(Product).filter(Product.is_deleted!=1).filter(Product.id == id).first()
        if len(products) < 1: 
            return {
                "message": "Products is empty"
            }, 404
        
        return {
            "success": True,
            "data": products
        }, 200
    except Exception as e:
        return {
            "message": "error get products",
            "error": (e)
        }, 500
    finally:
        s.close()
   

@product_routes.route('/product', methods=['POST'])
def create_product():

    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        new_product_id = f"P-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"
        product_name = request.form['name']
        product_price = request.form['price']
        product_category_id = request.form['category_id']
        product_stock = request.form['stock']
        product_images = request.form['images']
        product_premium = request.form['is_premium']
        created_by, updated_by = ''
        new_product = Product(
            id=new_product_id
        )

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
        

@product_routes.route('/product/<id>', methods=["PUT"])
def update_product(id):
    return {"message": "this is will update product based on id"}

@product_routes.route('/product/<id>', methods=["DELETE"])
def delete_product(id):
    return {"message": "this is will delete product based on id"}