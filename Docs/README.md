# Vending Machine Management System

A Python-based, command-line Vending Machine Management System that simulates product purchasing while providing inventory control, customer management, order processing, loyalty rewards, coupon management, and business reporting.

The application supports two types of users: **Customers**, who can browse products and make purchases, and **Owners**, who can manage inventory, track sales, configure discounts, and monitor business performance.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [User Roles](#user-roles)
- [Technologies Used](#technologies-used)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Product and Inventory Management](#product-and-inventory-management)
- [Checkout and Loyalty System](#checkout-and-loyalty-system)
- [Coupons and Discounts](#coupons-and-discounts)
- [Returns and Refunds](#returns-and-refunds)
- [Sales and Profit/Loss Reports](#sales-and-profitloss-reports)
- [Data Storage](#data-storage)
- [Validation and Error Handling](#validation-and-error-handling)
- [Future Improvements](#future-improvements)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The Vending Machine Management System is designed to demonstrate how a vending machine can operate through a software-based interface.

Customers can browse available products, add items to a cart, complete purchases, redeem coupons and loyalty points, and request returns for purchased items.

The owner has access to administrative functionality for managing products and stock, tracking orders, handling damaged or expired inventory, managing coupons, and reviewing financial reports.

The application uses Python for business logic and CSV files for persistent data storage. It also includes automated unit tests to verify important business rules and data-handling operations.

### Project Objectives

- Implement a structured vending machine workflow.
- Separate business logic from data management and user interaction.
- Maintain product inventory and expiry information.
- Process customer purchases and returns.
- Implement coupon discounts and customer loyalty rewards.
- Track sales, product costs, and business profitability.
- Validate inputs and handle common errors.
- Test core functionality using Python's testing framework.

---

## Features

### 1. Customer Management

- Register customers using their name and phone number.
- Recognize returning customers.
- Maintain customer loyalty points.
- Identify first-time customers for eligible introductory offers.
- Retrieve customer order history.

### 2. Product Catalogue

- Display products grouped by category.
- Show product IDs, names, prices, and available quantities.
- Display stock availability.
- Warn customers when product quantities are running low.
- Prevent customers from adding quantities beyond available stock.

### 3. Shopping Cart

- Add products to the cart.
- View the current cart and its total value.
- Update item quantities.
- Remove items by setting their quantity to zero.
- Calculate line subtotals and the overall cart total.
- Validate quantities against available inventory.

### 4. Checkout and Payments

- Calculate the final purchase amount.
- Apply eligible coupon discounts.
- Redeem loyalty points when permitted.
- Accept cash tendered by the customer.
- Calculate the change due.
- Generate order records with unique order IDs.
- Update inventory and customer loyalty points after successful checkout.

### 5. Inventory Management

- Add new products.
- Restock existing products.
- Track stock in individual batches.
- Record stock expiry dates.
- Identify expired and depleted batches.
- Remove stock for reasons such as damage, expiry, or packaging damage.
- Generate alerts when stock falls below configured thresholds.

### 6. Coupon Management

- Configure percentage-based discounts.
- Set minimum purchase requirements.
- Restrict coupons to first-time customers where applicable.
- Enable or disable coupons.
- Configure per-customer usage limits.
- Track customer coupon usage.

### 7. Returns and Refunds

- Process eligible returns against existing orders.
- Validate the requested return quantity.
- Record return reasons and descriptions.
- Calculate refund amounts.
- Track return transactions.
- Account for loyalty points awarded through eligible returns.

### 8. Business Reporting

- View recorded sales and orders.
- Calculate sales revenue.
- Calculate product costs.
- Account for refunds and stock removals in profit/loss calculations.
- Generate a net business result.
- Monitor stock levels through restock alerts.

### 9. Data Persistence

- Store application records in a CSV file.
- Save products and stock batches.
- Persist customer details and loyalty points.
- Store coupon configurations and usage records.
- Maintain order, return, and stock-removal history.
- Save owner authentication information.

### 10. Automated Testing

- Test business logic independently.
- Verify cart calculations and quantity validation.
- Test coupon and loyalty calculations.
- Validate checkout and return calculations.
- Test inventory batch allocation.
- Test CSV persistence and handling of malformed records.

---

## User Roles

### Customer

Customers can:

1. Enter their name and phone number.
2. Browse products by category.
3. Add products to a shopping cart.
4. View and edit cart quantities.
5. Apply eligible coupon codes.
6. Redeem available loyalty points.
7. Complete checkout and receive order details.
8. View previous orders.
9. Request returns for eligible purchased items.
10. Return to the main menu.

### Owner

The owner can create an account through the initial setup flow and log in to access administrative functions.

Owner capabilities include:

- Adding new products.
- Restocking existing products.
- Removing stock and recording reasons.
- Viewing current inventory.
- Viewing sales records.
- Generating profit/loss reports.
- Managing coupons.
- Checking low-stock alerts.
- Logging out of the owner menu.

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application development and business logic |
| CSV | Persistent storage of application data |
| `dataclasses` | Structured representation of products, customers, orders, and other entities |
| `hashlib` | Password hashing functionality |
| `unittest` | Automated unit testing |
| `datetime` | Date and timestamp handling |
| `typing` | Type annotations for functions and data structures |

The project primarily uses Python's standard library, so no external package installation should be necessary for the functionality shown in the current source files.

---

## Project Structure

```text
vending-machine/
│
├── main.py
│   └── Application entry point and command-line menus
│
├── logic.py
│   └── Data models, business rules, calculations,
│       validation, checkout, returns and reporting
│
├── store.py
│   └── Product, customer, order, inventory and coupon
│       management, plus CSV loading and saving
│
├── data.csv
│   └── Persistent application data and sample records
│
├── tests/
│   ├── __init__.py
│   ├── test_logic.py
│   │   └── Tests for business logic and calculations
│   │
│   └── test_store.py
│       └── Tests for data persistence and storage
│
└── README.md
    └── Project documentation
```

### Main Components

**`main.py` — Application Interface**

Provides the command-line interface, customer and owner menus, product display, cart interaction, and user input handling.

**`logic.py` — Business Logic**

Contains the data models and reusable functions used to calculate totals, validate inputs, allocate stock batches, calculate discounts, process checkout calculations, handle returns, and generate financial reports.

**`store.py` — Data Management**

Maintains the application's in-memory records and implements operations for loading and saving data, managing products and customers, updating stock, completing orders, and processing returns.

**`data.csv` — Persistent Storage**

Stores application data in a structured CSV format, including products, batches, customers, coupons, orders, returns, stock removals, and owner authentication information.

**`tests/` — Automated Tests**

Contains tests for the application's core calculations and storage operations.

---

## Getting Started

### Prerequisites

- Python 3.10 or later is recommended.
- Git, if you want to clone the repository.
- A terminal, Command Prompt, PowerShell, or an IDE such as VS Code.

To check your Python installation, run:

```bash
python --version
```

If your system uses the `py` launcher on Windows, you can also run:

```bash
py --version
```

### Clone the Repository

Replace `YOUR_USERNAME` with your GitHub username.

```bash
git clone https://github.com/YOUR_USERNAME/vending-machine.git
```

Move into the project directory:

```bash
cd vending-machine
```

If you are running the project locally without cloning it, open the directory containing `main.py`.

### Install Dependencies

The current project uses Python standard-library modules. A separate dependency installation step is not expected to be necessary.

---

## Running the Application

From the project root directory, execute:

```bash
python main.py
```

On Windows, you can alternatively use:

```bash
py main.py
```

The application presents a main menu from which you can choose the customer or owner workflow.

### Customer Workflow

1. Select the customer option.
2. Enter a name and phone number.
3. Browse products and choose product IDs.
4. Enter the quantities you want.
5. Review and modify your cart.
6. Proceed to checkout.
7. Enter the requested payment, coupon, and loyalty information.
8. Review the order summary.
9. View order history or request a return when eligible.

### Owner Workflow

1. Select the owner option.
2. Complete the initial owner setup if necessary, or log in.
3. Select an administrative operation.
4. Manage products, stock, coupons, or reports.
5. Log out when finished.

**Note:** The application is interactive, so follow the prompts displayed in your terminal. Some operations require valid product IDs, dates, quantities, or existing order IDs.

---

## Running Tests

The project uses Python's built-in `unittest` framework.

From the project root, run:

```bash
python -m unittest discover -s tests -v
```

On Windows, you can also run:

```bash
py -m unittest discover -s tests -v
```

The tests cover functionality such as:

- Available quantity calculations.
- Cart totals and subtotals.
- Adding and editing cart items.
- Product, restock, and stock-removal validation.
- Coupon discount calculations and eligibility.
- Loyalty point calculations.
- First-in, first-out stock batch allocation.
- Checkout calculations.
- Return calculations and refunds.
- Profit/loss calculations.
- CSV loading and saving.
- Handling empty or malformed CSV data.

The test suite is intended to help verify that core business rules behave correctly as the project evolves.

---

## Product and Inventory Management

Products contain information such as:

- Product ID.
- Product name.
- Category.
- Selling price.
- Unit cost.
- Restock threshold.
- Low-stock warning threshold.
- Associated stock batches.

Each stock batch tracks its quantity, expiry date, and the date it was added.

### Stock Allocation

The application implements a first-in, first-out (FIFO) allocation approach for stock batches. This helps ensure that older batches are considered before newer ones during allocation.

### Expiry Management

The system checks stock batch expiry dates and records expired stock as a removal. Expired quantities are excluded from normal sellable inventory.

### Stock Removal

Stock can be removed for supported reasons, including:

- Damaged products.
- Expired products.
- Packaging damage.
- Other recorded reasons.

Additional descriptions or expiry details may be required depending on the removal reason.

---

## Checkout and Loyalty System

During checkout, the application calculates the purchase total and determines whether the transaction can be completed.

The calculation can include:

- Item subtotals.
- Eligible coupon discounts.
- Loyalty point redemption.
- Final amount due.
- Cash received.
- Change due.

After a successful checkout, the storage layer updates the relevant stock batches, customer loyalty balance, coupon usage records, and order history.

### Loyalty Points

The application supports earning and redeeming customer loyalty points. The precise number of points earned or redeemed is determined by the business rules implemented in `logic.py`.

### Payment Handling

The current implementation uses cash-tendered input and calculates change. It does not represent an integration with a real payment gateway.

---

## Coupons and Discounts

The coupon system supports percentage-based discounts and configurable eligibility rules.

Coupon properties include:

- Coupon code.
- Percentage discount.
- Minimum order value.
- First-time-customer restriction.
- Enabled or disabled status.
- Maximum uses per customer.
- Customer usage history.

The application includes example coupon codes in its initial data, such as `SAVE20` and `WELCOME40`. Actual availability depends on the current data file and coupon configuration.

---

## Returns and Refunds

Customers can request returns for products associated with existing orders.

The return workflow considers the order, product, quantity being returned, reason, and any required supporting details.

The business logic calculates the refund amount and relevant loyalty adjustment, while the storage layer records the return and associated stock-removal information.

Return quantities are checked against the quantity originally purchased and any previously recorded returns.

---

## Sales and Profit/Loss Reports

The owner can review recorded sales and generate a profit/loss report.

The reporting logic considers categories such as:

- Sales revenue.
- Product costs.
- Refunds.
- Costs associated with stock removals.
- Net business result.

These reports provide a basic view of business performance based on the information stored in the application.

**Accounting note:** The calculated result is a simplified application-level report, not a substitute for formal accounting records or a complete financial statement.

---

## Data Storage

The application stores its records in `data.csv` rather than using a dedicated database server.

The CSV file contains different record types, including:

| Record type | Information stored |
|---|---|
| `PRODUCT` | Product details and pricing |
| `BATCH` | Inventory quantities and expiry dates |
| `CUSTOMER` | Customer information and loyalty points |
| `COUPON` | Discount rules and usage information |
| `ORDER` | Purchase and payment summary |
| `ORDER_ITEM` | Items associated with an order |
| `REMOVAL` | Inventory removal history |
| `RETURN` | Return and refund records |
| `OWNER_AUTH` | Owner authentication information |

### Important Data Handling Considerations

- Run the application from the project directory so it can find the intended CSV file.
- Back up important data before making changes.
- Avoid committing actual customer information or credentials to GitHub.
- Use clean demonstration records for a public repository.
- Keep generated or temporary test files out of version control.

Because the current implementation uses CSV-based persistence, it is best suited to a small local application or demonstration rather than a concurrent, production-scale service.

---

## Validation and Error Handling

The business logic includes validation for several common scenarios:

- Missing product information.
- Negative prices, costs, or quantities.
- Invalid restock quantities.
- Invalid stock-removal reasons.
- Missing descriptions for damaged stock.
- Missing expiry dates for expired stock.
- Invalid cart quantities.
- Insufficient available inventory.
- Coupon eligibility and minimum purchase requirements.
- Return quantities exceeding the remaining returnable quantity.

These checks help prevent invalid operations and make the application's behaviour more predictable.

---

## Future Improvements

Possible enhancements for future versions include:

- A graphical user interface or web-based interface.
- Migration from CSV files to SQLite or PostgreSQL.
- Improved authentication and secure password handling.
- Role-based permissions and session management.
- Digital payment gateway integration.
- Receipt export and downloadable invoices.
- Search and filtering in the product catalogue.
- More detailed inventory and sales analytics.
- Configurable tax calculations.
- Improved automated test coverage.
- Logging and audit trails for administrative operations.
- Automated backups and stronger data validation.

These are potential improvements rather than features that are necessarily implemented in the current version.

---

## Contributing

Contributions, suggestions, and bug reports are welcome.

To contribute:

1. Fork the repository.
2. Create a new branch for your changes.
3. Make your changes and add relevant tests.
4. Run the test suite.
5. Submit a pull request describing your changes.

Please avoid committing sensitive information, real customer records, or credentials.

---

## Team Members

This project was developed collaboratively by the following team members:

- **Darsh Keshav**
- **Chaitanya**
- **Akshay**

---

## Project

**Vending Machine Management System**

A Python-based project demonstrating command-line application development, inventory management, transaction processing, CSV data persistence, and automated testing.
