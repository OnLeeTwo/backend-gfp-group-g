from flask import Blueprint, request
from model.wishllist import Wishlist
from model.product import Product
from flask_jwt_extended import jwt_required, current_user
from services.logActions import LogManager

from nanoid import generate

from connectors.mysql_connectors import connection
from sqlalchemy.orm import sessionmaker
import os

wishlist_routes = Blueprint("wishlist_routes", __name__)


R2_DOMAINS = os.getenv("R2_DOMAINS")


@wishlist_routes.route("/wishlist", methods=["GET"])
@jwt_required()
def show_wishlist():
    user_id = current_user.user_id

    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        wishlist = []
        get_withlist = s.query(Wishlist).filter(Wishlist.user_id == user_id).all()
        if len(get_withlist) < 1:
            return {"title": "Fetching wishlist", "message": "Wishlist empty"}, 404

        for row in get_withlist:
            products = s.query(Product).filter(Product.id == row.product_id).first()

            wishlist.append(
                {
                    "name": products.name,
                    "price": products.price,
                    "stock": products.stock,
                    "images": f"{R2_DOMAINS}/{products.images}",
                }
            )

        # print(wishlist)
        return {
            "title": "Fetching wishlist",
            "message": "Success get wishlist",
            "wishlist": wishlist,
        }, 200
    except Exception as e:
        return {"title": "error connection", "message": (e)}, 500
    finally:
        s.close()


@wishlist_routes.route("/wishlist/<string:product_id>", methods=["GET"])
@jwt_required()
def check_wishlist(product_id):
    user_id = current_user.user_id

    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        wishlist_item = (
            s.query(Wishlist)
            .filter(Wishlist.user_id == user_id, Wishlist.product_id == product_id)
            .first()
        )

        if wishlist_item:
            return {
                "title": "Checking wishlist",
                "message": "Product is in your wishlist",
                "in_wishlist": True,
            }, 200
        else:
            return {
                "title": "Checking wishlist",
                "message": "Product is not in your wishlist",
                "in_wishlist": False,
            }, 404
    except Exception as e:
        return {"title": "Error handling request", "message": str(e)}, 500
    finally:
        s.close()


@wishlist_routes.route("/wishlist", methods=["POST"])
@jwt_required()
def create_wishlist():
    user_id = current_user.user_id
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:

        product_id = request.form["product_id"]
        print(user_id)
        log_manager = LogManager(user_id=current_user.user_id, action="CREATE_WISHLIST")
        check_product = (
            s.query(Product)
            .filter(Product.id == product_id, Product.is_deleted == 0)
            .first()
        )
        print(check_product)

        if check_product is None:
            return {"title": "add a new wishlist", "message": "Product not found"}, 400

        check_on_wishlist = (
            s.query(Wishlist)
            .filter(Wishlist.user_id == user_id)
            .filter(Wishlist.product_id == product_id)
            .all()
        )

        if len(check_on_wishlist) > 0:
            return {
                "title": "adding wishlist",
                "message": "this product already exist on your wishlist",
            }, 400

        new_id = f"W-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"

        add_wishlist = Wishlist(id=new_id, user_id=user_id, product_id=product_id)

        s.add(add_wishlist)
        wishlist_dict = add_wishlist.__dict__
        wishlist_dict = str(
            {
                key: value
                for key, value in wishlist_dict.items()
                if not key.startswith("_")
            }
        )
        log_manager.set_after(after_data=wishlist_dict)
        s.commit()
        log_manager.save()
        return {
            "message": "Successfully add new wishlist",
            "title": "add a new wishlist",
        }, 201
    except Exception as e:
        s.rollback()
        return {"title": "Error handling server", "message": str(e)}, 500

    finally:
        s.close()


@wishlist_routes.route("/wishlist/<string:product_id>", methods=["DELETE"])
@jwt_required()
def remove_wishlist(product_id):
    user_id = current_user.user_id

    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        Log_manager = LogManager(user_id, action="DELETE_WISHLIST")
        wishlist = (
            s.query(Wishlist)
            .filter(Wishlist.product_id == product_id, Wishlist.user_id == user_id)
            .first()
        )
        wishlist_dict = vars(wishlist)
        wishlist_dict = str(
            {
                key: value
                for key, value in wishlist_dict.items()
                if not key.startswith("_")
            }
        )
        s.delete(wishlist)
        Log_manager.set_before(before_data=wishlist_dict)
        s.commit()
        Log_manager.save()
        return {"message": "wishlist removed"}, 200
    except Exception as e:
        s.rollback()
        return {"title": "Error handling server", "message": str(e)}, 500
    finally:
        s.close()
