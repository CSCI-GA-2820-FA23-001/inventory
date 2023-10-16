"""
My Service

Describe what your service does here
"""

from flask import jsonify, request, url_for, abort
from service.common import status  # HTTP Status Codes
from service.models import Inventory, DataValidationError

# Import Flask application
from . import app


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        "Reminder: return some useful information in json format about the service here",
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


# Place your REST API code here ...


# Create a new item in the inventory
@app.route("/inventory", methods=["POST"])
def create_product():
    """
    Creates a product into the inventory
    This endpoint will create a product based the data in the body that is posted
    """
    app.logger.info("Request to create a product...")
    check_content_type("application/json")
    product = Inventory()
    product.deserialize(request.get_json())
    if Inventory.find(product.id) is not None:
        abort(status.HTTP_409_CONFLICT, f"Product {product.id} already exists")
    product.create()
    message = product.serialize()
    # location_url = url_for("get_products", pet_id=product.id, _external=True)

    app.logger.info("Product with ID [%s] created.", product.id)
    return jsonify(message), status.HTTP_201_CREATED

    # return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


# Retrieve an item from the inventory with a specified ID
@app.route("/inventory/<iid>", methods=["GET"])
def get_product(iid):
    """Gets a product with specified id"""
    app.logger.info("Request to get product with id %d...", iid)
    ans = Inventory.find(iid)
    if ans is None:
        abort(status.HTTP_404_NOT_FOUND, f"Product {iid} does not exist")
    message = ans.serialize()
    app.logger.info("Returning: product %d...", iid)
    return jsonify(message), status.HTTP_200_OK


# Update a product in the inventory with a specified ID
@app.route("/inventory/<iid>", methods=["PUT"])
def update_product(iid):
    """
    Update a product

    This endpoint will update a product based the body that is posted
    """
    app.logger.info("Request to update product with id: %s", iid)
    check_content_type("application/json")

    product = Inventory.find(iid)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Product with id '{iid}' was not found.")

    product.deserialize(request.get_json())
    product.id = iid
    product.update()

    app.logger.info("Product with ID [%s] updated.", product.id)
    return jsonify(product.serialize()), status.HTTP_200_OK


# Error handling for POST method
@app.route("/inventory/<iid>", methods=["POST"])
def post_on_id(iid):
    """Handle invalid method: POST on inventory/<iid>"""
    abort(
        status.HTTP_405_METHOD_NOT_ALLOWED,
        f"Path not allowed, use /inventory to create product {iid}",
    )


# Delete a product in the inventory with a specified ID
@app.route("/inventory/<iid>", methods=["DELETE"])
def delete_product(iid):
    """Delete product based on its id"""
    app.logger.info("Request to delete product with id: %s", iid)

    product = Inventory.find(iid)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Product with id '{iid}' was not found.")

    product.delete()

    app.logger.info("Product with ID [%s] deleted.", iid)
    return jsonify({}), status.HTTP_204_NO_CONTENT


# Retrieve all items in the inventory
@app.route("/inventory", methods=["GET"])
def list_products():
    """Retrieves all products from the inventory"""
    app.logger.info("Request to list all products")
    products = Inventory.all()
    results = [product.serialize() for product in products]
    return jsonify(results), status.HTTP_200_OK


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )
