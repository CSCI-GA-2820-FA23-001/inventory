"""
My Service

Describe what your service does here
"""

from flask import jsonify, request, url_for, abort
from service.common import status  # HTTP Status Codes
from service.models import Inventory

# Import Flask application
from . import app


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return {"status": "OK"}, status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Inventory Demo REST API Service",
            version="1.0",
            paths=url_for("list_products", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


# Place your REST API code here ...
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
    location_url = url_for("get_product", iid=product.id, _external=True)

    app.logger.info("Product with ID [%s] created.", product.id)
    # return jsonify(message), status.HTTP_201_CREATED

    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


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
    product.id = iid  # to undo deserialize's id field, so update won't change id
    product.update()

    app.logger.info("Product with ID [%s] updated.", product.id)
    return jsonify(product.serialize()), status.HTTP_200_OK


@app.route("/inventory/<iid>", methods=["POST"])
def post_on_id(iid):
    """Handle invalid method: POST on inventory/<iid>"""
    abort(
        status.HTTP_405_METHOD_NOT_ALLOWED,
        f"Path not allowed, use /inventory to create product {iid}",
    )


@app.route("/inventory/<iid>", methods=["DELETE"])
def delete_product(iid):
    """Delete a product from the inventory"""
    app.logger.info("Request to delete product with id: %s", iid)

    product = Inventory.find(iid)
    if not product:
        return jsonify({}), status.HTTP_204_NO_CONTENT

    product.delete()

    app.logger.info("Product with ID [%s] deleted.", iid)
    return jsonify({}), status.HTTP_204_NO_CONTENT


@app.route("/inventory", methods=["GET"])
def list_products():
    """Retrieves all products from the inventory"""
    app.logger.info("Request to list all products")
    products = []
    condition = request.args.get("condition")
    name = request.args.get("name")
    quantity = request.args.get("quantity")
    if condition:
        products = Inventory.find_by_condition(condition)
    elif name:
        products = Inventory.find_by_name(name)
    elif quantity:
        products = Inventory.find_by_quantity(quantity)
    else:
        products = Inventory.all()
    results = [product.serialize() for product in products]
    app.logger.info("Returning %d products", len(results))
    return jsonify(results), status.HTTP_200_OK


@app.route("/inventory/<iid>/restock", methods=["PUT"])
def restock_product(iid):
    """Restocks product with certain id to its restock level"""
    app.logger.info("Request to restock product with id %d...", iid)
    ans = Inventory.find(iid)
    if ans is None:
        abort(status.HTTP_404_NOT_FOUND, f"Product {iid} does not exist")
    cur = ans.quantity
    need = ans.restock_level
    if cur < need:
        added = need - cur
        ans.quantity = need
        ans.restock_count += 1
        app.logger.info("Restock %d units of product %d", added, need)
        ans.update()
    return (f"Product {iid} restocked. Current quantity {need}", status.HTTP_200_OK)


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
