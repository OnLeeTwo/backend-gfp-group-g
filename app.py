from flask import Flask
from dotenv import load_dotenv
from datetime import timedelta
import os
from flask_jwt_extended import JWTManager
from sqlalchemy.orm import sessionmaker
from connectors.mysql_connectors import connection
from model.market import Market
from controllers.market import market_routes

load_dotenv()

app = Flask(__name__)




@app.route("/")
def hello_world():
    return "Hello World"


if __name__ == "__main__":
    app.run(debug=True)
