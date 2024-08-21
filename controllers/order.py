from flask import Blueprint, request
from datetime import datetime, UTC

from model.order import Order, OrderStatus, PaymentStatus
from model.order_details import OrderDetails
from model.promotion import Promotion
from model.seller import Seller
from model.market import Market
from services.logActions import LogManager
from nanoid import generate

from connectors.mysql_connectors import connection
from sqlalchemy.orm import sessionmaker
from services.order_check import OrderCheck


from flask_jwt_extended import (
    jwt_required,
    current_user,
)


order_routes = Blueprint("order_routes", __name__)


@order_routes.route("/order", methods=["POST"])
@jwt_required()
def create_order():
    # pertama cek dulu apakah stock yang dari cart masih ada
    # Kedua Cek voucher valid
    # Ketiga hitung total (nilai pada product - voucher + ongkir )

    Session = sessionmaker(connection)
    s = Session()

    s.begin()
    try:
        user_id = current_user.user_id
        carts = request.form.get("cart")

        # Check Product in cart have an enough stock
        if carts is None or carts == "":
            return {"message": "cart is empty"}, 400
        check_cart = OrderCheck(carts)

        if check_cart is None:
            return {"message": "Quantities more than stock "}, 400

        # Check if code promotion is valid
        promotion_code = request.form.get("code")
        promotion_id = None
        discount_value = 0.0
        if promotion_code is not None:
            promotion = (
                s.query(Promotion).filter(Promotion.code == promotion_code).first()
            )
            if promotion is None:
                return {"message": "Promotion code not found"}, 404
            current_date = datetime.now(UTC).date()

            if current_date < promotion.start_date or current_date > promotion.end_date:
                return {"error": "Promotion code has expired"}, 400

            discount_value = promotion.discount_value
            promotion_id = promotion.promotion_id

        data = check_cart.SumOrderDetail(discount_value)
        log_manager = LogManager(user_id=user_id, action="CREATE_ORDER")

        for market_id, details in data.items():
            amount = details["amount"]
            order_details = details["order_details"]
            tax = details["tax"]
            shipping_fee = details["shipping_fee"]
            admin_fee = details["admin_fee"]
            discount_fee = details["discount_fee"]

            # Generate the order ID for the market
            id = f"O-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"

            print(f"Market ID: {market_id}")
            print(f"Amount: {amount}")
            print(f"Order id:{id}")

            # Create the new order
            NewOrder = Order(
                user_id=user_id,
                order_id=id,
                market_id=market_id,
                total_amount=amount,
                tax=tax,
                shipping_fee=shipping_fee,
                admin_fee=admin_fee,
                discount_fee=discount_fee,
                status_order=OrderStatus.pending,
                status_payment=PaymentStatus.pending,
                shipping_address=request.form["shipping_address"],
                promotion_id=promotion_id,
                created_by=user_id,
            )

            s.add(NewOrder)
            transformed_data = [
                {
                    "order_details_id": item["order_id"],
                    "order_id": id,
                    "product_id": item["product_id"],
                    "quantity": item["quantity"],
                    "total_price": item["total_price"],
                    "user_id": user_id,
                }
                for item in order_details
            ]
            s.bulk_insert_mappings(OrderDetails, transformed_data)

        # Update product qty
        order_dict = NewOrder.__dict__
        order_dict = str(
            {key: value for key, value in order_dict.items() if not key.startswith("_")}
        )
        log_manager.set_after(after_data=order_dict)

        s.commit()
        log_manager.save()

        return {"success": True, "order_id": id, "total_amount": amount}, 201

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


@order_routes.route("/order/buyer", methods=["GET"])
@jwt_required()
def get_all_orders_buyers_only():
    Session = sessionmaker(connection)
    s = Session()

    try:
        role = current_user.role
        user_id = current_user.user_id

        if role != "buyer":
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
                    "shipping_fee": order.shipping_fee,
                    "admin_fee": order.admin_fee,
                    "tax": order.tax,
                }
            )

        return orders_data, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        s.close()


@order_routes.route("/order/seller", methods=["GET"])
@jwt_required()
def get_all_orders_seller_only():
    Session = sessionmaker(connection)
    s = Session()

    try:
        role = current_user.role
        user_id = current_user.user_id

        if role != "seller":
            return {"error": "Only seller can access this routes!"}, 400

        seller_id = s.query(Seller).filter(Seller.user_id == user_id).first().seller_id

        markets = s.query(Market).filter(Market.seller_id == seller_id).all()

        for market in markets:
            orders = s.query(Order).filter(Order.market_id == market.market_id).all()
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
                        "shipping_fee": order.shipping_fee,
                        "admin_fee": order.admin_fee,
                        "tax": order.tax,
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

    try:
        user_id = current_user.user_id
        order = (
            s.query(Order)
            .filter(Order.user_id == user_id, Order.order_id == order_id)
            .first()
        )

        if not order:
            return {"error": "Order not found"}, 404
        log_manager = LogManager(user_id=user_id, action="UPDATE_ORDER")
        order_dict = vars(order)
        order_dict = str(
            {key: value for key, value in order_dict.items() if not key.startswith("_")}
        )
        log_manager.set_before(before_data=order_dict)

        if "status_payment" in request.form:
            order.status_payment = request.form["status_payment"]

        if "status_order" in request.form:
            order.status_order = request.form["status_order"]

        order_dict = vars(order)
        order_dict = str(
            {key: value for key, value in order_dict.items() if not key.startswith("_")}
        )
        log_manager.set_after(after_data=order_dict)
        s.commit()
        log_manager.save()
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
        log_manager = LogManager(user_id=user_id, action="CANCEL_ORDER")
        order = (
            s.query(Order)
            .filter(Order.user_id == user_id, Order.order_id == order_id)
            .first()
        )

        if not order:
            return {"error": "Order not found"}, 404
        order_dict = vars(order)
        order_dict = str(
            {key: value for key, value in order_dict.items() if not key.startswith("_")}
        )
        log_manager.set_before(before_data=order_dict)
        if order.status_order != OrderStatus.pending:
            return {"error": "Only pending orders can be cancelled"}, 400

        order.status_order = OrderStatus.cancelled

        order_dict = vars(order)
        order_dict = str(
            {key: value for key, value in order_dict.items() if not key.startswith("_")}
        )
        log_manager.set_after(after_data=order_dict)
        s.commit()
        log_manager.save()
        return {"message": "Order cancelled successfully"}, 200

    except Exception as e:
        s.rollback()
        return {"error": str(e)}, 500

    finally:
        s.close()
