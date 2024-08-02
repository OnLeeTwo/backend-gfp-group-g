from flask import Blueprint, request
from model.product import Product
from model.category import Category

from nanoid import generate
from connectors.mysql_connectors import connection
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Select
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
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
        products =[]
        data = Select(Product)
        result = s.execute(data)
        for row in result.scalars():
            products.append({
                "id": row.id,
                "product_name": row.name,
                "price": row.price,
                "stock": row.stock,
                "category": row.category_id,
                "is_premium": row.is_premium
            })
        if len(products) < 1: 
            return {
                "message": "Products is empty"
            }, 404
        
        return {
            "success": True,
            "data": products
        }, 200
    except Exception as e:
        s.rollback()
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
        product = []
        products = s.query(Product).filter(Product.id==id).first()
        if products is None:
            return {
                "message": "product not found"
            }, 404
        
        product.append({
            "id": products.id,
            "product_name": products.name,
            "price": products.price,
            "stock": products.stock,
            "category": products.category_id,
            "is_premium": products.is_premium
        })
        
        return {
            "success": True,
            "data": product
        }, 200
    except Exception as e:
        s.rollback()
        return {
            "message": "error get products",
            "error": (e)
        }, 500
    finally:
        s.close()
   

@product_routes.route('/product', methods=['POST'])
@jwt_required()
def create_product():

    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        current_user_id = get_jwt_identity()
        product_name=request.form['product_name']
        price=request.form['price']
        stock=request.form['stock']
        category=request.form['category']
        images=request.form['images']
        is_premium=request.form['is_premium']
        market_id=request.form['market_id']
        # Kurang validasi untuk market. Dibuat jika market sudah ada
    
        check_category = s.query(Category).filter(Category.name == category).first()
        if check_category is None:
            category_id = f"C-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"
            newCategory = Category(
                id=category_id,
                name=category
            )
            s.add(newCategory)
            s.flush()
        else:
            category_id = check_category.id

        newProduct = Product(
            id=f"P-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}",
            name=product_name,
            price=float(price),
            stock=int(stock),
            category_id=category_id,
            images=images,
            is_premium=int(is_premium),
            market_id=market_id,
            is_deleted=0,
            time_deleted='',
            created_by=current_user_id,
            updated_by=current_user_id
        )
        s.add(newProduct)
        s.commit()
        return {
            "success": True,
            "message": "Success create product"
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