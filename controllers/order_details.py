from flask import Blueprint, request
from sqlalchemy.orm import sessionmaker

from model.order_details import OrderDetails
from model.product import Product

from connectors.mysql_connectors import connection

from flask_jwt_extended import jwt_required, get_jwt_identity

order_details_routes = Blueprint("order_details_routes", __name__)


@order_details_routes.route("/order_details", methods=["POST"])
@jwt_required()
def create_order_details():
    Session = sessionmaker(connection)
    s = Session()
    s.begin()

    try:
        product_id = request.form["product_id"]
        product = s.query(Product).filter(Product.id == product_id).first()

        if not product:
            return {"error": "Product not found"}, 404

        product_price = product.price
        quantity = int(request.form["quantity"])

        total_price = quantity * product_price

        new_order = OrderDetails(
            order_id=request.form["order_id"],
            user_id=request.form["user_id"],
            product_id=product_id,
            quantity=quantity,
            total_price=total_price,
        )

        s.add(new_order)
        s.commit()
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


@order_details_routes.route("/order_details/<int:order_details_id>", methods=["GET"])
def get_order_details_by_id(order_details_id):
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        order = (
            s.query(OrderDetails).filter_by(order_details_id=order_details_id).first()
        )

        if not order:
            return {"message": "Order not found"}, 404

        order_details = {
            "order_details_id": order.order_details_id,
            "order_id": order.order_id,
            "user_id": order.user_id,
            "product_id": order.product_id,
            "quantity": order.quantity,
            "total_price": order.total_price,
        }
        return order_details, 200
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

        s.commit()
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
        if not order:
            return {"message": "Order not found"}, 404

        s.delete(order)
        s.commit()
        return {"message": "Order details deleted"}, 200
    except Exception as e:
        s.rollback()
        return {"error": str(e)}, 500
