from flask import Blueprint, request
from sqlalchemy.orm import sessionmaker
import os


from model.order_details import OrderDetails
from model.product import Product
from model.market import Market
from services.logActions import LogManager

from connectors.mysql_connectors import connection

from flask_jwt_extended import jwt_required, get_jwt_identity

from nanoid import generate

R2_DOMAINS = os.getenv("R2_DOMAINS")

order_details_routes = Blueprint("order_details_routes", __name__)


@order_details_routes.route("/order_details", methods=["POST"])
@jwt_required()
def create_order_details():
    Session = sessionmaker(connection)
    s = Session()
    s.begin()

    try:
        user_id = get_jwt_identity()
        product_id = request.form["product_id"]
        product = s.query(Product).filter(Product.id == product_id).first()
        log_manager = LogManager(
            user_id=get_jwt_identity(), action="CREATE_ORDER_DETAIL"
        )

        if not product:
            return {"error": "Product not found"}, 404

        product_price = product.price
        quantity = int(request.form["quantity"])

        if quantity <= 0:
            return {"error": "Quantity must be greater than 0"}, 400

        if quantity > product.stock:
            return {"error": "Not enough stock"}, 400

        total_price = quantity * product_price

        new_order_details_id = (
            f"OD-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"
        )

        new_order = OrderDetails(
            order_details_id=new_order_details_id,
            order_id=request.form["order_id"],
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            total_price=total_price,
        )

        s.add(new_order)
        s.commit()
        order_dict = new_order.__dict__
        order_dict = str(
            {key: value for key, value in order_dict.items() if not key.startswith("_")}
        )
        log_manager.set_after(after_data=order_dict)
        return {
            "message": "Order details created",
            "order_details_id": new_order.order_details_id,
        }, 201
    except ValueError as ve:
        s.rollback()
        return {"error": f"Invalid data format: {str(ve)}"}, 400
    except Exception as e:
        s.rollback()
        return {"error": str(e)}, 500
    finally:
        s.close()


@order_details_routes.route("/order_details/", methods=["GET"])
def get_order_details():
    Session = sessionmaker(connection)
    s = Session()
    s.begin()

    try:
        user_id = get_jwt_identity()
        orders = s.query(OrderDetails).filter_by(user_id=user_id).all()
        if not orders:
            return {"message": "No orders found for this user ID"}, 404

        orders_list = [
            {
                "order_details_id": order.order_details_id,
                "order_id": order.order_id,
                "user_id": order.user_id,
                "product_id": order.product_id,
                "quantity": order.quantity,
                "total_price": order.total_price,
            }
            for order in orders
        ]
        return orders_list, 200
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        s.close()


@order_details_routes.route("/order_details/order/<string:order_id>", methods=["GET"])
@jwt_required()
def get_order_details_by_order_id(order_id):
    Session = sessionmaker(connection)
    s = Session()

    s.begin()
    try:
        user_id = get_jwt_identity()
        orders = (
            s.query(OrderDetails).filter_by(order_id=order_id, user_id=user_id).all()
        )

        if not orders:
            return {"message": "Order details not found for this order ID"}, 404

        order_details_list = []

        for order in orders:
            product = s.query(Product).filter_by(id=order.product_id).first()

            if product:
                product_name = product.name
                product_price = product.price
                product_images = f"{R2_DOMAINS}/{product.images}"
            else:
                product_name = None
                product_price = None
                product_images = None

            market = s.query(Market).filter_by(market_id=product.market_id).first()

            if market:
                market_name = market.name
            else:
                market_name = None

            order_details_list.append(
                {
                    "order_id": order.order_id,
                    "product_id": order.product_id,
                    "quantity": order.quantity,
                    "total_price": order.total_price,
                    "product_name": product_name,
                    "product_price": product_price,
                    "product_images": product_images,
                    "market_name": market_name,
                }
            )

        return {"order_details": order_details_list}, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        s.close()


@order_details_routes.route("/order_details/<string:order_id>", methods=["GET"])
def get_order_details_by_order_id_seller(order_id):
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        orders = s.query(OrderDetails).filter_by(order_id=order_id).all()

        if not orders:
            return {"message": "Order details not found for this order ID"}, 404

        order_details_list = []

        for order in orders:
            product = s.query(Product).filter_by(id=order.product_id).first()

            if product:
                product_name = product.name
                product_price = product.price
                product_images = f"{R2_DOMAINS}/{product.images}"
            else:
                product_name = None
                product_price = None
                product_images = None

            market = s.query(Market).filter_by(market_id=product.market_id).first()

            if market:
                market_name = market.name
            else:
                market_name = None

            order_details_list.append(
                {
                    "order_id": order.order_id,
                    "product_id": order.product_id,
                    "quantity": order.quantity,
                    "total_price": order.total_price,
                    "product_name": product_name,
                    "product_price": product_price,
                    "product_images": product_images,
                    "market_name": market_name,
                }
            )

        return {"order_details": order_details_list}, 200
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        s.close()


@order_details_routes.route("/order_details/<int:order_details_id>", methods=["PUT"])
def update_order_details(order_details_id):
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        user_id = get_jwt_identity()
        order = (
            s.query(OrderDetails)
            .filter(
                OrderDetails.order_details_id == order_details_id,
                OrderDetails.user_id == user_id,
            )
            .first()
        )
        log_manager = LogManager(user_id=user_id, action="UPDATE_ORDER_DETAIL")
        order_dict = vars(order)
        order_dict = str(
            {key: value for key, value in order_dict.items() if not key.startswith("_")}
        )
        log_manager.set_before(before_data=order_dict)
        order.order_id = request.form["order_id"]

        if "quantity" in request.form:
            try:
                order.quantity = int(request.form["quantity"])
                product_id = order.product_id
                product = s.query(Product).filter(Product.id == product_id).first()
                total_price = order.quantity * product.price
                order.total_price = total_price
            except ValueError:
                return {"error": "Invalid value for quantity"}, 400

        order_dict = vars(order)
        order_dict = str(
            {key: value for key, value in order_dict.items() if not key.startswith("_")}
        )
        log_manager.set_after(after_data=order_dict)
        s.commit()
        log_manager.save()
        return {"message": "Order details updated successfully"}, 200

    except Exception as e:
        s.rollback()
        return {"error": str(e)}, 500

    finally:
        s.close()


@order_details_routes.route("/order_details/<int:order_details_id>", methods=["DELETE"])
def delete_order_details(order_details_id):
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        order = s.query(OrderDetails).get(order_details_id)
        log_manager = LogManager(
            user_id=get_jwt_identity(), action="DELETE_ORDER_DETAIL"
        )
        if not order:
            return {"message": "Order not found"}, 404
        order_dict = vars(order)
        order_dict = str(
            {key: value for key, value in order_dict.items() if not key.startwith("_")}
        )
        log_manager.set_before(before_data=order_dict)
        s.delete(order)
        s.commit()
        log_manager.save()
        return {"message": "Order details deleted"}, 200
    except Exception as e:
        s.rollback()
        return {"error": str(e)}, 500
