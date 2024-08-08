from flask import Blueprint, request
from datetime import datetime, UTC

from model.order import Order, OrderStatus, PaymentStatus
from model.order_details import OrderDetails
from model.promotion import Promotion

from nanoid import generate

from connectors.mysql_connectors import connection
from sqlalchemy.orm import sessionmaker

from flask_jwt_extended import (
    jwt_required,
    current_user,
)


order_routes = Blueprint("order_routes", __name__)


@order_routes.route("/order", methods=["POST"])
@jwt_required()
def create_order():
    Session = sessionmaker(connection)
    s = Session()

    s.begin()
    try:
        user_id = current_user.user_id
        order_details = (
            s.query(OrderDetails)
            .filter(OrderDetails.user_id == user_id, OrderDetails.order_id.is_(None))
            .all()
        )
        if not order_details:
            return {"error": "No item in cart!"}, 400

        new_order_id = f"O-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"

        total_amount = sum(detail.total_price for detail in order_details)

        promotion_code = request.form["code"]
        discount_amount = 0

        if promotion_code:
            promotion = (
                s.query(Promotion).filter(Promotion.code == promotion_code).first()
            )

            if not promotion:
                return {"error": "Invalid promotion code"}, 400

            current_date = datetime.now(UTC)
            if current_date < promotion.start_date or current_date > promotion.end_date:
                return {"error": "Promotion code has expired"}, 400

            discount_amount = total_amount * promotion.discount_value
            total_amount -= discount_amount

        NewOrder = Order(
            user_id=user_id,
            order_id=new_order_id,
            total_amount=total_amount,
            status_order=OrderStatus.pending,
            status_payment=PaymentStatus.pending,
            shipping_address=request.form["shipping_address"],
            promotion_id=promotion.promotion_id if promotion else None,
        )

        s.add(NewOrder)

        for detail in order_details:
            detail.order_id = new_order_id

        s.commit()

        return {"message": "Order created successfully", "order_id": new_order_id}, 201

    except Exception as e:
        s.rollback()
        return {"error": str(e)}, 500

    finally:
        s.close()


@order_routes.route("/order", methods=["GET"])
@jwt_required()
def get_all_orders():
    Session = sessionmaker(connection)
    s = Session()

    try:
        user_id = current_user.user_id
        orders = s.query(Order).filter(Order.user_id == user_id).all()

        orders_data = []
        for order in orders:
            orders_data.append(
                {
                    "order_id": order.order_id,
                    "total_amount": order.total_amount,
                    "status_order": order.status_order.value,
                    "status_payment": order.status_payment.value,
                    "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "shipping_address": order.shipping_address,
                    "promotion_id": order.promotion_id,
                }
            )

        return orders_data, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        s.close()


@order_routes.route("/order", methods=["GET"])
@jwt_required()
def get_all_orders_buyers_only():
    Session = sessionmaker(connection)
    s = Session()

    try:
        role = current_user.role
        user_id = current_user.user_id

        if role is not "buyer":
            return {"error": "Only buyer can access this routes!"}, 400

        orders = s.query(Order).filter(Order.user_id == user_id).all()
        orders_data = []
        for order in orders:
            orders_data.append(
                {
                    "order_id": order.order_id,
                    "total_amount": order.total_amount,
                    "status_order": order.status_order.value,
                    "status_payment": order.status_payment.value,
                    "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "shipping_address": order.shipping_address,
                    "promotion_id": order.promotion_id,
                }
            )

        return orders_data, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        s.close()


@order_routes.route("/order/<string:order_id>", methods=["GET"])
@jwt_required()
def get_order_by_id(order_id):
    Session = sessionmaker(connection)
    s = Session()

    try:
        user_id = current_user.user_id
        order = (
            s.query(Order)
            .filter(Order.user_id == user_id, Order.order_id == order_id)
            .first()
        )

        if not order:
            return {"error": "Order not found"}, 404

        order_details = (
            s.query(OrderDetails).filter(OrderDetails.order_id == order_id).all()
        )

        order_data = {
            "order_id": order.order_id,
            "total_amount": order.total_amount,
            "status_order": order.status_order.value,
            "status_payment": order.status_payment.value,
            "shipping_address": order.shipping_address,
            "created_at": order.created_at.isoformat(),
            "items": [
                {
                    "product_id": detail.product_id,
                    "quantity": detail.quantity,
                    "price": detail.price,
                    "total_price": detail.total_price,
                }
                for detail in order_details
            ],
        }

        return order_data, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        s.close()


@order_routes.route("/orders/<string:order_id>", methods=["PUT"])
@jwt_required()
def update_order(order_id):
    Session = sessionmaker(connection)
    s = Session()

    request_body = {
        "status_payment": request.form["email"],
        "status_order": request.form["password"],
    }

    try:
        user_id = current_user.user_id
        order = (
            s.query(Order)
            .filter(Order.user_id == user_id, Order.order_id == order_id)
            .first()
        )

        if not order:
            return {"error": "Order not found"}, 404

        order.status_order = request_body["status_order"]
        order.status_payment = request_body["status_payment"]

        s.commit()

        return {"message": "Order cancelled successfully"}, 200

    except Exception as e:
        s.rollback()
        return {"error": str(e)}, 500

    finally:
        s.close()


@order_routes.route("/orders/<string:order_id>/cancel", methods=["PUT"])
@jwt_required()
def cancel_order(order_id):
    Session = sessionmaker(connection)
    s = Session()

    try:
        user_id = current_user.user_id
        order = (
            s.query(Order)
            .filter(Order.user_id == user_id, Order.order_id == order_id)
            .first()
        )

        if not order:
            return {"error": "Order not found"}, 404

        if order.status_order != OrderStatus.pending:
            return {"error": "Only pending orders can be cancelled"}, 400

        order.status_order = OrderStatus.cancelled

        s.commit()

        return {"message": "Order cancelled successfully"}, 200

    except Exception as e:
        s.rollback()
        return {"error": str(e)}, 500

    finally:
        s.close()
