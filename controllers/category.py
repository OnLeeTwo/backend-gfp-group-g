from flask import Blueprint
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Select
from connectors.mysql_connectors import connection
from model.category import Category

category_routes = Blueprint("category_routes", __name__)

@category_routes.route('/categories', methods=['GET'])
def category_all():
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        category = []
        categories = Select(Category)
        result = s.execute(categories)
        for row in result.scalars():
            category.append({
                'id': row.id,
                'name': row.name
            })
        if len(category) < 1: 
            return {
                "message": "Categories is empty"
            }, 404
        return {
            "success": True,
            "data": category
        }
    except Exception as e: 
        return {
            "message": "Error handling category",
            "error": str(e)
        }, 500
    finally:
        s.close()

@category_routes.route('/category/<id>', methods=['GET'])
def category_by_id(id):
    Session = sessionmaker(connection)
    s = Session()
    s.begin()
    try:
        category = []
        categories = s.query(Category).filter(Category.id==id).first()
        if categories is not None:
            category.append({
                "id": categories.id,
                "name": categories.name
            })
            return {
                "message": "success get data",
                "data": category
            }, 200
        else: 
            return {
                "message": "category not found"
            }, 404
    except Exception as e: 
        return {
            "message": "Error handling category",
            "error": str(e)
        }, 500
    finally:
        s.close()
