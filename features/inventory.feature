Feature: The inventory service back-end
    As a Inventory Owner
    I need a RESTful catalog service
    So that I can keep track of all my products

Background:
    Given the following products
        | id    | name     | quantity| restock_level | restock_count|condition| first_entry_date | last_restock_date |
        | 12    | computer | 12      | 8             | 2            | NEW     | 2019-11-18       |  2019-12-18       |
        | 321   | phone    | 32      | 50            | 11           | OPEN_BOX| 2020-08-13       |  2020-08-15       |
        | 712   | table    | 43      | 100           | 3            | USED    | 2021-04-01       |  2021-04-05       |
        | 322   | pen      | 12      | 12            | 1            | USED    | 2018-06-04       |  2018-12-02       |
        | 127   | monitor  | 25      | 10            | 5            | NEW     | 2017-01-01       |  2023-01-01       |

Scenario: The server is running
    When I visit the "Home Page"
    Then I should see "Inventory RESTful Service" in the title
    And I should not see "404 Not Found"


Scenario: Create a Product
    When I visit the "Home Page"
    And I set the "id" to "66"
    And I set the "name" to "newname"
    And I set the "quantity" to "10"
    And I set the "restock_level" to "20"
    And I set the "restock_count" to "0"
    And I select "NEW" in the "condition" dropdown
    And I set the "first_entry_date" to "11-11-2023"
    And I set the "last_restock_date" to "11-15-2023"
    And I press the "Create" button
    Then I should see the message "Success"
    When I copy the "id" field
    And I press the "Clear" button
    Then the "id" field should be empty
    And the "name" field should be empty
    And the "quantity" field should be empty
    When I paste the "id" field
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "newname" in the "name" field
    And I should see "NEW" in the "condition" dropdown
    And I should see "10" in the "quantity" field
    And I should see "2023-11-11" in the "first_entry_date" field


Scenario: List all Products
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "fido" in the results
    And I should see "kitty" in the results
    And I should not see "leo" in the results

Scenario: Read a product
    When I visit the "Home Page"
    And I set the "id" to "12"
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "computer" in the "name" field
    And I should see "12" in the "quantity" field
    And I should see "2019-12-18" in the "last_restock_date" field
    And I should see "NEW" in the "condition" field
    

Scenario: Search for available
    When I visit the "Home Page"
    And I select "True" in the "Available" dropdown
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "fido" in the results
    And I should see "kitty" in the results
    And I should see "sammy" in the results
    And I should not see "leo" in the results

Scenario: Update a Product
    When I visit the "Home Page"
    And I set the "Name" to "fido"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "fido" in the "Name" field
    And I should see "dog" in the "Category" field
    When I change "Name" to "Loki"
    And I press the "Update" button
    Then I should see the message "Success"
    When I copy the "Id" field
    And I press the "Clear" button
    And I paste the "Id" field
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "Loki" in the "Name" field
    When I press the "Clear" button
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Loki" in the results
    And I should not see "fido" in the results

Scenario: Delete a Product
    When I visit the "Home Page"
    And I set the "id" to "127"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "monitor" in the "name" field
    And I should see "25" in the "quantity" field
    And I should see "10" in the "restock_level" field
    And I should see "5" in the "restock_count" field
    And I should see "NEW" in the "condition" field
    And I should see "2017-01-01" in the "condition" field
    And I should see "2023-01-01" in the "last_restock_date" field
    When I press the "Delete" button
    Then I should see the message "Product has been Deleted!"
