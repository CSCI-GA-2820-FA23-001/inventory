"""
Models for Inventory

All of the models are stored in this module
"""
import logging
from enum import Enum
from datetime import date
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


# Function to initialize the database
def init_db(app):
    """Initializes the SQLAlchemy app"""
    Inventory.init_db(app)


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class Condition(Enum):
    """Enumeration of valid product Conditions"""

    NEW = 0
    OPEN_BOX = 1
    USED = 2


class Inventory(db.Model):
    """
    Class that represents a Product
    """

    app = None

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    # default name is product_id
    name = db.Column(db.String(63))  # allow unnamed products
    quantity = db.Column(db.Integer, nullable=False, default=0)
    restock_level = db.Column(db.Integer, nullable=False, default=0)
    restock_count = db.Column(db.Integer, nullable=False, default=0)
    condition = db.Column(
        db.Enum(Condition), nullable=False, server_default=(Condition.NEW.name)
    )
    first_entry_date = db.Column(db.Date(), nullable=False, default=date.today())
    last_restock_date = db.Column(db.Date(), nullable=False, default=date.today())

    def __repr__(self):
        return f"<Product {self.id} id=[{self.id}]>"

    def create(self):
        """
        Creates a Product to the database
        """
        logger.info("Creating %s", self.id)
        # self.id = None  # pylint: disable=invalid-name
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Updates a Product to the database
        """
        logger.info("Saving %s", self.id)
        db.session.commit()

    def delete(self):
        """Removes a Product from the data store"""
        logger.info("Deleting %s", self.id)
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        """Serializes a Product into a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "quantity": self.quantity,
            "restock_level": self.restock_level,
            "restock_count": self.restock_count,
            "condition": self.condition.name,
            "first_entry_date": self.first_entry_date.isoformat(),
            "last_restock_date": self.last_restock_date.isoformat(),
        }

    def deserialize(self, data):
        """
        Deserializes a Product from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.id = data["id"]
            if "name" in data:
                self.name = data["name"]
            else:
                self.name = None  # product name can be none
            self.quantity = data["quantity"]
            self.restock_level = data["restock_level"]
            self.restock_count = data["restock_count"]
            self.condition = getattr(Condition, data["condition"])
            self.first_entry_date = date.fromisoformat(data["first_entry_date"])
            self.last_restock_date = date.fromisoformat(data["last_restock_date"])

        except KeyError as error:
            raise DataValidationError(
                "Invalid Product: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Product: body of request contained bad or no data - "
                "Error message: " + error
            ) from error
        except AttributeError as error:
            raise DataValidationError(
                "Invalid Product: body of request contained bad or no data - "
            ) from error
        return self

    @classmethod
    def init_db(cls, app):
        """Initializes the database session"""
        logger.info("Initializing database")
        cls.app = app
        # This is where we initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push()
        db.create_all()  # make our sqlalchemy tables

    @classmethod
    def all(cls):
        """Returns all of the Products in the database"""
        logger.info("Processing all Products")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """Finds a Product by it's ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        return db.session.get(cls, by_id)

    @classmethod
    def find_by_name(cls, name):
        """Returns all Products with the given name

        Args:
            name (string): the name of the Product you want to match
        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name)
