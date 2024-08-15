from connectors.mysql_connectors import connection
from sqlalchemy.orm import sessionmaker
from model.product import Product
from model.category import Category
from decimal import Decimal
import json
import os
from nanoid import generate

R2_DOMAINS = os.getenv("R2_DOMAINS")
class OrderCheck:
    def __init__(self, cart):
        self.cart = cart
        self.carts = json.loads(cart)
        Session = sessionmaker(connection)
        db = Session()
        db.begin()
        isOver = 0
        try:
            for market in self.carts:
                product = db.query(Product).filter(Product.id == self.carts[market][0]["product_id"]).first()
           
                quantity = self.carts[market][0]["quantity"]
                if quantity > product.stock:
                    isOver = isOver + 1
        
            return None if isOver == 0 else isOver
        except Exception as e:
            db.rollback()
            print(f"error: {str(e)}")
        finally:
            db.close()
        

    
    def SumOrderDetail(self, discount_value):
        order_details = []
        price_fix = 0.0
        shipping_price = 10000
        admin_price = 5000
        Session = sessionmaker(connection)
        db = Session()
        db.begin()

        try:
            for market in self.carts:
                id = f"OD-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"
                product = db.query(Product).filter(Product.id == self.carts[market][0]["product_id"]).first()
                quantity = self.carts[market][0]["quantity"]
                price = Decimal(product.price * quantity)
                price_after_discount = price * Decimal(discount_value / 100)
                price = price - price_after_discount
                
                if price < 0:
                    price = 0.0
          
                total_price = price + Decimal(shipping_price) + Decimal(admin_price) 
                tax = total_price * Decimal(11/100)
                price_fix = total_price + tax
                order_details.append({
                    "order_id": id,
                   "product_id": product.id,
                   "total_price": round(price_fix, 2),
                   "quantity": quantity,
                })
            return order_details    
        except Exception as e:
            db.rollback()
            print(f"Error: {str(e)}")
        finally:
            db.close()

    def showProductOnCart(self):
        Session = sessionmaker(connection)
        db = Session()
        db.begin()

        try:
            products = []
            for market in self.carts:
                product = db.query(Product).filter(Product.id == self.carts[market][0]["product_id"]).first()
                category = db.query(Category).filter(Category.id==product.category_id).first()
               
                products.append({
                    "id": product.id,
                    "market_id": product.market_id,
                    "product_name": product.name,
                    "description": product.description,
                    "price": product.price,
                    "stock": product.stock,
                    "images": f"{R2_DOMAINS}/{product.images}",
                    "category": category.name,
                    "is_premium": product.is_premium,
                })
            
            return products

        except Exception as e:
            db.rollback()
            print(f"error: {str(e)}")
        finally:
            db.close()
 
        
            



        
