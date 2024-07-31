from flask import Blueprint
from sqlalchemy.orm import sessionmaker
from connectors.mysql_connectors import connection
from model.category import Category
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt,
    get_jwt_identity,
    current_user,
)

category_routes = Blueprint("category_routes", __name__)

@category_routes.route('/categories', methods=['GET'])
@jwt_required()
def category_all():
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        categories = s.query(Category).all()
        if len(categories) < 1: 
            return {
                "message": "Categories is empty"
            }, 404
        return {
            "success": True,
            "data": categories
        }
    except Exception as e: 
        return {
            "message": "Error handling category",
            "error": (e)
        }, 500
    finally:
        s.close()

@category_routes.route('/category/<id>', methods=['GET'])
@jwt_required()
def category_by_id(id):
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        categories = s.query(Category).filter(Category.id==id).first()
        if len(categories) < 1: 
            return {
                "message": "Categories not found"
            }, 404
        return {
            "success": True,
            "data": categories
        }
    except Exception as e: 
        return {
            "message": "Error handling category",
            "error": (e)
        }, 500
    finally:
        s.close()
