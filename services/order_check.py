from connectors.mysql_connectors import connection
from sqlalchemy.orm import sessionmaker
from model.product import Product
from model.category import Category
from model.market import Market
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

                for products in self.carts[market]:

                    product = (
                        db.query(Product)
                        .filter(Product.id == products["product_id"])
                        .first()
                    )
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
        tax_percent = 11
        price_fix = 0.0
        shipping_price = 10000
        admin_price = 5000
        Session = sessionmaker(connection)
        db = Session()
        db.begin()

        try:
            product_by_market = {}

            for market in self.carts:
                amount = 0
                total_tax = 0
                order_details = []
                for products in self.carts[market]:

                    id = f"OD-{generate('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ', 6)}"
                    product = (
                        db.query(Product)
                        .filter(Product.id == products["product_id"])
                        .first()
                    )
                    quantity = products["quantity"]
                    price = Decimal(product.price * quantity)
                    price_after_discount = price * Decimal(discount_value / 100)
                    price = price - price_after_discount

                    if price < 0:
                        price = 0.0

                    total_price = price + Decimal(shipping_price) + Decimal(admin_price)
                    tax = total_price * Decimal(tax_percent / 100)
                    price_fix = total_price + tax
                    amount += price_fix

                    order_details.append(
                        {
                            "order_id": id,
                            "product_id": product.id,
                            "total_price": round(price_fix, 2),
                            "quantity": quantity,
                        }
                    )
                    product.stock = product.stock - quantity
                product_by_market[market] = {
                    "amount": round(amount, 2),
                    "order_details": order_details,
                    "tax": total_tax,
                    "shipping_fee": shipping_price,
                    "admin_fee": admin_price,
                }

            db.commit()
            return product_by_market
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
            product_by_market = {}

            for market in self.carts:

                products_on_market = []
                marketQuery = (
                    db.query(Market).filter(Market.market_id == market).first()
                )

                for products in self.carts[market]:
                    product = (
                        db.query(Product)
                        .filter(Product.id == products["product_id"])
                        .first()
                    )
                    category = (
                        db.query(Category)
                        .filter(Category.id == product.category_id)
                        .first()
                    )

                    products_on_market.append(
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "price": product.price,
                            "stock": product.stock,
                            "images": f"{R2_DOMAINS}/{product.images}",
                            "category": category.name,
                        }
                    )

                    print(products_on_market)

                product_by_market[market] = {
                    "market": market,
                    "market_name": marketQuery.name,
                    "product": products_on_market,
                }

            return product_by_market
        except Exception as e:
            db.rollback()
            print(f"Error: {str(e)}")
        finally:
            db.close()
