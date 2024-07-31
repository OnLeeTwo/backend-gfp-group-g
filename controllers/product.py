from flask import Blueprint, request
from model.product import Product
from model.category import Category

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

# create function to assign category. User



@product_routes.route('/products', methods=['GET'])
@jwt_required()
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
@jwt_required()
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
        check_name = s.query(Category).filter(Category.name == request.form['category']).first()
        new_product_id = f"P-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"
        if len(check_name) > 0:
            category = check_name.id
        else:
            category = f"C-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"
            new_category = Category(
                id = category,
                name=request.form['category']
            )
            s.add(new_category)
            s.commit()
        
        product_name = request.form['name']
        product_price = ''
        product_stock = ''
        product_images = ''
        product_premium = ''
        created_by, updated_by = ''
        new_product = Product(
            id=new_product_id,
            category_id=category,
            name=product_name,
            price=float(product_price),
            stock=int(product_stock),
            images=product_images,
            is_premium=product_premium,
            created_by=created_by,
            updated_by=updated_by

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
        

@product_routes.route('/product/<id>', methods=["PUT"])
def update_product(id):
    return {"message": "this is will update product based on id"}

@product_routes.route('/product/<id>', methods=["DELETE"])
def delete_product(id):
    return {"message": "this is will delete product based on id"}