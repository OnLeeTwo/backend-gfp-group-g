from flask import Blueprint, request
from models.market import Market
from nanoid import generate
from cerberus import Validator
from connectors.mysql_connectors import connection
from sqlalchemy.orm import sessionmaker


market_routes = Blueprint("market_routes", __name__)