from flask import Blueprint, request
from datetime import datetime

from model.promotion import Promotion

from nanoid import generate

from connectors.mysql_connectors import connection
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from flask_jwt_extended import (
    jwt_required,
    current_user,
)

promotion_routes = Blueprint("promotion_routes", __name__)


@promotion_routes.route("/promotion", methods=["POST"])
@jwt_required()
def create_promotion():
    Session = sessionmaker(connection)
    s = Session()

    try:
        new_promotion_id = f"PR-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"

        new_promotion = Promotion(
            market_id=request.form["market_id"],
            promotion_id=new_promotion_id,
            code=request.form["code"],
            discount_value=request.form["discount_value"],
            created_by=current_user.user_id,
            start_date=datetime.fromisoformat(request.form["start_date"]),
            end_date=datetime.fromisoformat(request.form["end_date"]),
        )

        s.add(new_promotion)
        s.commit()

        return {
            "message": "Promotion created successfully",
            "promotion_id": new_promotion.promotion_id,
        }, 201

    except Exception as e:
        s.rollback()
        return {"error": str(e)}, 400

    finally:
        s.close()


@promotion_routes.route("/promotion", methods=["GET"])
@jwt_required()
def get_all_promotions():
    Session = sessionmaker(connection)
    s = Session()

    try:
        market_id = request.form["market_id"]
        promotions = s.query(Promotion).filter(Promotion.market_id == market_id).all()

        promotions_data = [
            {
                "promotion_id": promo.promotion_id,
                "code": promo.code,
                "discount_value": promo.discount_value,
                "start_date": promo.start_date.isoformat(),
                "end_date": promo.end_date.isoformat(),
                "created_at": promo.created_at.isoformat(),
                "updated_at": promo.updated_at.isoformat(),
            }
            for promo in promotions
        ]

        if len(promotions_data) < 1:
            return {"error": "promotion not found"}, 404

        return promotions_data, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        s.close()


@promotion_routes.route("/promotion/<string:promotion_id>", methods=["GET"])
@jwt_required()
def get_promotion(promotion_id):
    Session = sessionmaker(connection)
    s = Session()

    try:
        market_id = request.form["market_id"]
        promotion = (
            s.query(Promotion)
            .filter(
                Promotion.promotion_id == promotion_id,
                Promotion.market_id == market_id,
            )
            .first()
        )

        if not promotion:
            return {"error": "Promotion not found"}, 404

        promotion_data = {
            "id": promotion.promotion_id,
            "code": promotion.code,
            "discount_value": promotion.discount_value,
            "start_date": promotion.start_date.isoformat(),
            "end_date": promotion.end_date.isoformat(),
            "created_at": promotion.created_at.isoformat(),
            "updated_at": promotion.updated_at.isoformat(),
        }

        return promotion_data, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        s.close()


@promotion_routes.route("/promotions/<string:promotion_id>", methods=["PUT"])
@jwt_required()
def update_promotion(promotion_id):
    Session = sessionmaker(connection)
    s = Session()

    try:
        market_id = request.form["market_id"]
        promotion = (
            s.query(Promotion)
            .filter(
                Promotion.promotion_id == promotion_id,
                Promotion.market_id == market_id,
            )
            .first()
        )

        if not promotion:
            return {"error": "Promotion not found"}, 404

        if "code" in request.form:
            promotion.code = request.form["code"]

        if "discount_value" in request.form:
            promotion.discount_value = float(request.form["discount_value"])

        if "start_date" in request.form:
            promotion.start_date = datetime.fromisoformat(request.form["start_date"])

        if "end_date" in request.form:
            promotion.end_date = datetime.fromisoformat(request.form["end_date"])

        s.commit()

        return {"message": "Promotion updated successfully"}, 200

    except ValueError as ve:
        s.rollback()
        return {"error": f"Invalid data format: {str(ve)}"}, 400

    except Exception as e:
        s.rollback()
        return {"error": str(e)}, 500

    finally:
        s.close()


@promotion_routes.route("/promotions/<string:promotion_id>", methods=["DELETE"])
@jwt_required()
def delete_promotion(promotion_id):
    Session = sessionmaker(connection)
    s = Session()

    try:
        promotion = (
            s.query(Promotion)
            .filter(
                Promotion.id == promotion_id,
                Promotion.market_id == current_user.market_id,
            )
            .first()
        )

        if not promotion:
            return {"error": "Promotion not found"}, 404

        s.delete(promotion)
        s.commit()

        return {"message": "Promotion deleted successfully"}, 200

    except Exception as e:
        s.rollback()
        return {"error": str(e)}, 400

    finally:
        s.close()
