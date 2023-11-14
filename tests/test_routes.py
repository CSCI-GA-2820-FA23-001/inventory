"""
TestYourResourceModel API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from service import app
from service.models import db, init_db, Inventory
from service.common import status  # HTTP Status Codes
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/inventory"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestYourResourceServer(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        self.client = app.test_client()
        db.session.query(Inventory).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    def _create_products(self, count):
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_pet = ProductFactory()
            response = self.client.post(BASE_URL, json=test_pet.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test pet",
            )
            new_pet = response.get_json()
            test_pet.id = new_pet["id"]
            products.append(test_pet)
        return products

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(
            BASE_URL, json=test_product.serialize(), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["quantity"], test_product.quantity)
        self.assertEqual(new_product["restock_level"], test_product.restock_level)
        self.assertEqual(new_product["restock_count"], test_product.restock_count)
        self.assertEqual(new_product["condition"], test_product.condition.name)
        self.assertEqual(
            new_product["first_entry_date"], test_product.first_entry_date.isoformat()
        )
        self.assertEqual(
            new_product["last_restock_date"], test_product.last_restock_date.isoformat()
        )

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["quantity"], test_product.quantity)
        self.assertEqual(new_product["restock_level"], test_product.restock_level)
        self.assertEqual(new_product["restock_count"], test_product.restock_count)
        self.assertEqual(new_product["condition"], test_product.condition.name)
        self.assertEqual(
            new_product["first_entry_date"], test_product.first_entry_date.isoformat()
        )
        self.assertEqual(
            new_product["last_restock_date"], test_product.last_restock_date.isoformat()
        )

    def test_not_json(self):
        """Test create product with content type not being json, should raise error 415"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(
            BASE_URL, json=test_product.serialize(), content_type="application/not-json"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_conflict(self):
        """Test create a product with an id that already exists, should raise error 409"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(
            BASE_URL, json=test_product.serialize(), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        conf_product = ProductFactory()
        conf_product.id = test_product.id
        logging.debug("Conflict Product: %s", conf_product.serialize())
        response = self.client.post(
            BASE_URL, json=conf_product.serialize(), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_create_bad_data(self):
        """Create an item with bad data, missing fields or wrong types, should raise error 400"""
        not_integer = {
            "id": "not an integer",
            "quantity": 1,
            "restock_level": "not an integer",
            "restock_count": 1,
            "condition": "NEW",
            "first_entry_date": "2011-01-01",
            "last_restock_date": "2011-01-03",
        }
        logging.debug("Test Product: %s", not_integer)
        response = self.client.post(
            BASE_URL, data=not_integer, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        missing_field = {
            "id": 25,
            "quantity": 3,
            "restock_count": 10,
        }  # missing other fields
        logging.debug("Test Product: %s", missing_field)
        response = self.client.post(
            BASE_URL, data=missing_field, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_product(self):
        """Get a product from db, should return the item with id or 404 if not exist"""
        test_item = ProductFactory()
        logging.debug("Test Product: %s", test_item.serialize())
        response = self.client.post(
            BASE_URL, json=test_item.serialize(), content_type="application/json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED
        )  # has to be created

        # get the item back
        iid = test_item.id
        response = self.client.get(f"{BASE_URL}/{iid}", content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        got_item = response.get_json()
        self.assertEqual(got_item["name"], test_item.name)
        self.assertEqual(got_item["quantity"], test_item.quantity)
        self.assertEqual(got_item["restock_level"], test_item.restock_level)
        self.assertEqual(got_item["restock_count"], test_item.restock_count)
        self.assertEqual(got_item["condition"], test_item.condition.name)

        # try to get a nonexistent item
        iid += 1
        response = self.client.get(f"{BASE_URL}/{iid}", content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product(self):
        """It should Update an existing product"""

        # create a product to update
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the product
        new_product = response.get_json()
        logging.debug(new_product)
        new_product["name"] = "newname"
        new_product["quantity"] = 0
        new_product["restock_level"] = 0
        new_product["restock_count"] = 0
        new_product["condition"] = "USED"

        response = self.client.put(f"{BASE_URL}/{new_product['id']}", json=new_product)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_product = response.get_json()
        self.assertEqual(updated_product["name"], "newname")
        self.assertEqual(updated_product["quantity"], 0)
        self.assertEqual(updated_product["restock_level"], 0)
        self.assertEqual(updated_product["restock_count"], 0)
        self.assertEqual(updated_product["condition"], "USED")

    def test_bad_update(self):
        """Update nonexistent product and bad data, should raise 404 and 415"""
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the product
        new_product = response.get_json()
        logging.debug(new_product)
        new_product["id"] += 1  # invalid ID
        new_product["name"] = "newname"
        response = self.client.put(f"{BASE_URL}/{new_product['id']}", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        new_product["id"] -= 1
        new_product["condition"] = "bad condition"
        response = self.client.put(f"{BASE_URL}/{new_product['id']}", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_method_not_allowed(self):
        """Call not-allowed methods on url, should raise 405"""
        post_product = ProductFactory()

        # call POST on /inventory/<iid>
        response = self.client.post(
            f"{BASE_URL}/{post_product.id}", json=post_product.serialize()
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_product(self):
        """Delete a product"""
        test_product = ProductFactory()
        test_product.create()
        iid = test_product.id

        self.assertIsNotNone(Inventory.find(iid))
        resp = self.client.delete(f"{BASE_URL}/{iid}", content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(Inventory.find(iid))

    def test_delete_nonexistent_product(self):
        """Delete a product that doesn't exist"""
        resp = self.client.delete(f"{BASE_URL}/999999", content_type="application/json")

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_list_products_empty(self):
        """Get products when empty"""
        resp = self.client.get(BASE_URL)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 0)

    def test_list_products_with_data(self):
        """Get products with some data in the database"""
        self._create_products(5)

        resp = self.client.get(BASE_URL)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 5)

    def test_query_by_condition(self):
        """It should Query inventory items by Condition"""
        products = self._create_products(3)
        test_condition = products[0].condition
        condition_product = [
            item for item in products if item.condition == test_condition
        ]

        # by condition number
        response = self.client.get(
            BASE_URL, query_string=f"condition={str(test_condition.value)}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), len(condition_product))

        if str(test_condition.value) == "0":
            for item in data:
                self.assertEqual(item["condition"], "NEW")
        if str(test_condition.value) == "1":
            for item in data:
                self.assertEqual(item["condition"], "OPEN_BOX")
        if str(test_condition.value) == "2":
            for item in data:
                self.assertEqual(item["condition"], "USED")

        # by condition string
        string_query = str.upper(test_condition.name)
        response = self.client.get(BASE_URL, query_string=f"condition={string_query}")
        data = response.get_json()
        self.assertEqual(len(data), len(condition_product))

        for products in data:
            self.assertEqual(products["condition"], test_condition.name)

    def test_restock(self):
        """
        Restock a product whose quantity is below restock level
        one whose is above, and one nonexistent
        """
        # prod 1: quantity below level
        prod_1 = ProductFactory()
        prod_1.restock_level = 100
        prod_1.quantity = 14
        cur_count_1 = prod_1.restock_count
        id_1 = prod_1.id
        prod_1.create()

        # restock and check new quantity
        response = self.client.put(f"{BASE_URL}/{id_1}/restock")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f"{BASE_URL}/{id_1}")
        data = response.get_json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["quantity"], 100)
        self.assertEqual(data["restock_count"], cur_count_1 + 1)

        # prod 2: quantity above level
        prod_2 = ProductFactory()
        prod_2.restock_level = 100
        prod_2.quantity = 136
        cur_count_2 = prod_2.restock_count
        id_2 = prod_2.id
        prod_2.create()

        # check current quantity

        # after restock
        response = self.client.put(f"{BASE_URL}/{id_2}/restock")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f"{BASE_URL}/{id_2}")
        data = response.get_json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["quantity"], 136)
        self.assertEqual(data["restock_count"], cur_count_2)

        # restock nonexistent
        id_bad = id_2 + id_1
        response = self.client.put(f"{BASE_URL}/{id_bad}/restock")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_query_by_quantity(self):
        """It should Query inventory items by quantity"""

        products = self._create_products(3)
        test_quantity = products[0].quantity
        quantity_product = [item for item in products if item.quantity == test_quantity]
        response = self.client.get(
            BASE_URL, query_string=f"quantity={str(test_quantity)}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), len(quantity_product))
        for item in data:
            self.assertEqual(item["quantity"], test_quantity)

    def test_query_by_name(self):
        """Get product by name and nonexistent name, should return 200"""
        products = [ProductFactory() for i in range(0, 4)]
        products[0].name = "dog_whistle"
        products[1].name = "bear_mace"
        products[2].name = "dog_whistle"
        products[3].name = "dog_whistle"
        for i in range(0, 4):
            products[i].create()

        response = self.client.get(BASE_URL, query_string="name=dog_whistle")
        data = response.get_json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 3)

        response = self.client.get(BASE_URL, query_string="name=dog_collar")
        data = response.get_json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 0)

    def test_health(self):
        """It should Get the health endpoint"""
        resp = self.app.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")
