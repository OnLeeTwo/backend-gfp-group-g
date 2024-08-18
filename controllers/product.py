from flask import Blueprint, request
from model.product import Product
from model.category import Category
from model.seller import Seller
from nanoid import generate
from connectors.mysql_connectors import connection
from services.order_check import OrderCheck
from sqlalchemy.orm import sessionmaker
from model.market import Market
import os
from services.upload import UploadService
from services.logActions import LogManager
from datetime import datetime
from sqlalchemy import func
from flask_jwt_extended import jwt_required, get_jwt_identity


upload_service = UploadService()

product_routes = Blueprint("product_routes", __name__)
R2_DOMAINS=os.getenv('R2_DOMAINS')
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@product_routes.route("/products", methods=["GET"])
def products_all():

    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        products = []
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        name = request.args.get('name', '', type=str)
        offset = (page - 1) * per_page
        query = s.query(Product).filter(Product.is_deleted == 0)

        if name != '':
            query = query.filter(Product.name.ilike(f'%{name}'))

        
        query_all = query.offset(offset).limit(per_page)
        data = query_all.all()
        total_product = query.count()
        print(total_product)
        total_pages = (total_product + per_page - 1) // per_page
        # result = s.execute(data)
        for row in data:
            category = s.query(Category).filter(Category.id == row.category_id).first()
            MarketName = s.query(Market).filter(Market.market_id == row.market_id).first()
            products.append(
                {
                    "id": row.id,
                    "product_name": row.name,
                    "description": row.description,
                    "market_id": row.market_id,
                    "market_name": MarketName.name,
                    "price": row.price,
                    "images": f"{R2_DOMAINS}/{row.images}",
                    "stock": row.stock,
                    "category": category.name,
                    "is_premium": row.is_premium,
                }
            )
        if len(products) < 1:
            return {"message": "Products is empty"}, 404

        return {
            "success": True, 
            "data": products,
            'total_pages': total_pages,
            'current_page': page,
            'per_page': per_page,
            'total_items': total_product,
        }, 200
    except Exception as e:
        s.rollback()
        return {"message": "error get products", "error": (e)}
    finally:
        s.close()


@product_routes.route("/product/<id>", methods=["GET"])
def product_by_id(id):

    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        product = []
        products = (
            s.query(Product)
            .filter(Product.id == id)
            .filter(Product.is_deleted == 0)
            .first()
        )
        if products is None:
            return {"message": "product not found"}, 404
        category = s.query(Category).filter(Category.id == products.category_id).first()
        product.append(
            {
                "id": products.id,
                "market_id": products.market_id,
                "product_name": products.name,
                "description": products.description,
                "price": products.price,
                "stock": products.stock,
                "images": f"{R2_DOMAINS}/{products.images}",
                "category": category.name,
                "is_premium": products.is_premium,
            }
        )

        return {"success": True, "data": product}, 200
    except Exception as e:
        s.rollback()
        return {"message": "error get products", "error": (e)}, 500
    finally:
        s.close()


@product_routes.route("/products_market/<id>", methods=["GET"])
def product_by_market_id(id):
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        name = request.args.get('name', '', type=str)
        offset = (page - 1) * per_page
        query = s.query(Product).filter(Product.is_deleted == 0, Product.market_id == id)
        
        if name != '':
            query = query.filter(Product.name.ilike(f'%{name}%'))

        query_all = query.offset(offset).limit(per_page)
        data = query_all.all()
        total_product = query.count()
        total_pages = (total_product + per_page - 1 ) // per_page
        # result = s.execute(data)
        products = []
        for row in data:
            category = s.query(Category).filter(Category.id == row.category_id).first()
            products.append(
                {
                    "id": row.id,
                    "product_name": row.name,
                    "market_id": row.market_id,
                    "price": row.price,
                    "description": row.description,
                    "images": f"{R2_DOMAINS}/{row.images}",
                    "stock": row.stock,
                    "category": category.name,
                    "is_premium": row.is_premium,
                }
            )
        if len(products) < 1:
            return {"message": "Products is empty"}, 404

        return {
            "success": True,
            "data": products,
            'total_pages': total_pages,
            'current_page': page,
            'per_page': per_page,
            'total_items': total_product,
        }, 200
    except Exception as e:
        return {"message": "Error handling server", "error": str(e)}, 500


@product_routes.route("/product", methods=["POST"])
@jwt_required()
def create_product():

    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        current_user_id = get_jwt_identity()

        is_seller = s.query(Seller).filter(Seller.user_id == current_user_id).first()
        if is_seller is None:
            return {"message": "You are not seller"}, 403

        log_manager = LogManager(user_id=current_user_id, action="CREATE_PRODUCT")
        product_name = request.form["product_name"]
        description = request.form['description']
        price = request.form["price"]
        stock = request.form["stock"]
        category = request.form["category"]
        is_premium = request.form["is_premium"]
        market_id = request.form["market_id"]
        new_filename = ""

        market = s.query(Market).filter(Market.market_id == market_id).first()
        if market is None:
            return {"message": "Market not found, please check again"}, 404

        check_category = s.query(Category).filter(Category.name == category).first()
        if check_category is None:
            category_id = f"C-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"
            newCategory = Category(id=category_id, name=category)
            s.add(newCategory)
            s.flush()
        else:
            category_id = check_category.id

        product_id = f"P-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"
        if "images" in request.files:
            file = request.files["images"]
            if file.filename == "":
                return {"error": "No selected file"}, 400
            if file and allowed_file(file.filename):

                filename = file.filename
                ext_name = os.path.splitext(filename)[1]
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                new_filename = f"{product_id}-{timestamp}{ext_name}"

                try:
                    upload_service.upload_file(file, new_filename)
                except Exception as e:
                    return {"error": str(e)}, 500
            else:
                return {"error": "file type not allowed"}, 415

        newProduct = Product(
            id=product_id,
            name=product_name,
            price=float(price),
            description=description,
            stock=int(stock),
            category_id=category_id,
            images=new_filename,
            is_premium=int(is_premium),
            market_id=market_id,
            is_deleted=0,
            created_by=current_user_id,
            updated_by=current_user_id,
        )

        product_dict = newProduct.__dict__
        product_dict = {
            key: value for key, value in product_dict.items() if not key.startswith("_")
        }
        s.add(newProduct)
        s.commit()
        log_manager.set_after(after_data=str(product_dict))
        log_manager.save()
        return {"success": True, "message": "Success create product"}, 201

    except Exception as e:
        s.rollback()
        return {"message": "error create product", "error": str(e)}, 500
    finally:
        s.close()


@product_routes.route("/product/<id>", methods=["PUT"])
@jwt_required()
def update_product(id):
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        product = s.query(Product).filter(Product.id == id).first()

        if product is None:
            return {"message": "product not found"}, 404
        category_id = ""
        current_user_id = get_jwt_identity()
        log_manager = LogManager(user_id=current_user_id, action="UPDATE_PRODUCT")
        product_dict = vars(product)
        product_str = str(
            {
                key: value
                for key, value in product_dict.items()
                if not key.startswith("_")
            }
        )
        log_manager.set_before(before_data=product_str)
        product_name = request.form["product_name"]
        price = request.form["price"]
        stock = request.form["stock"]
        description = request.form['description']
        category = request.form["category"]
        is_premium = request.form["is_premium"]
        market_id = request.form["market_id"]

        new_filename = product.images
        market = s.query(Market).filter(Market.market_id == market_id).first()
        if market is None:
            return {"message": "Market not found, please check again"}, 404

        check_category = s.query(Category).filter(Category.name == category).first()
        if check_category is None:
            category_id = f"C-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"
            newCategory = Category(id=category_id, name=category)
            s.add(newCategory)
            s.flush()
        else:
            category_id = check_category.id

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

        product.name = product_name
        product.description = description
        product.price = float(price)
        product.stock = int(stock)
        product.category_id = category_id
        product.images = new_filename
        product.is_premium = int(is_premium)
        product.market_id = market_id
        product.updated_by = current_user_id

        product_dict = product.__dict__
        product_dict = str(
            {
                key: value
                for key, value in product_dict.items()
                if not key.startswith("_")
            }
        )
        log_manager.set_after(after_data=product_dict)
        s.commit()
        log_manager.save()
        return {"message": "Updated product success", "success": True}, 201
    except Exception as e:
        s.rollback()
        return {"message": "error update product", "error": str(e)}, 500
    finally:
        s.close()


@product_routes.route("/product/<id>", methods=["DELETE"])
@jwt_required()
def delete_product(id):
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        log_manager = LogManager(user_id=get_jwt_identity(), action="DELETE_PRODUCT")
        product = (
            s.query(Product)
            .filter(Product.id == id)
            .filter(Product.is_deleted == 0)
            .first()
        )
        if product is None:
            return {"message": "product not found"}, 404
        product_dict = vars(product)
        product_str = str(
            {
                key: value
                for key, value in product_dict.items()
                if not key.startswith("_")
            }
        )

        log_manager.set_before(before_data=product_str)
        product.is_deleted = 1
        product.time_deleted = func.now()

        product_dict = product.__dict__
        product_dict = str(
            {
                key: value
                for key, value in product_dict.items()
                if not key.startswith("_")
            }
        )
        log_manager.set_after(after_data=product_dict)
        s.commit()
        log_manager.save()
        return {"success": True, "message": "Success delete product"}, 200

    except Exception as e:
        s.rollback()
        return {"message": "error delete product", "error": str(e)}, 500
    finally:
        s.close()


@product_routes.route("/product/cart", methods=["GET"])
@jwt_required()
def show_cart():
   
    try:
        carts = request.args.get('carts', '')
        check_cart = OrderCheck(carts)
       
        if check_cart is None: 
            return {
                "message": "Quantities more than stock "
            }, 400
        cart = check_cart.showProductOnCart()
      
        return {
            "product_on_cart": cart
        }, 200

    except Exception as e:
        return {"error": str(e)}, 500
    
    