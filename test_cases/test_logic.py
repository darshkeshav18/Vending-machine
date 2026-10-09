"""Unit tests for every function in logic.py.

Rules followed by every test:
- no files, no database, no global state (each test builds its own data)
- one function under test per test class
- normal case, edge case and invalid-input case where they make sense
- pure functions must not change the objects passed into them

Run with:  python -m unittest test_logic -v
"""
import copy
import unittest

import logic

NOW = "2026-10-09 10:00:00"
FUTURE = "2099-12-31"
PAST = "2020-01-01"


# ----------------------------------------------------------------------
# Helpers that build fresh test data (nothing shared between tests)
# ----------------------------------------------------------------------

def make_product(pid="P001", name="Cold Coffee", price=60, cost=30, batches=None):
    product = logic.Product(pid, name, "Cold Beverages", price, cost, 2, 2)
    if batches is None:
        batches = [(6, FUTURE, "2026-10-01 00:00:00")]
    for i, (qty, expiry, added) in enumerate(batches, start=1):
        batch_id = f"B{i}"
        product.stock_batches[batch_id] = logic.StockBatch(batch_id, qty, expiry, added)
    return product


def make_customer(phone="9999999999", first_time=False, points=0):
    return logic.Customer(phone, "Test", first_time, points)


def make_coupon(code="SAVE20", percent=20, min_order=500, first_time_only=False,
                enabled=True, limit=5, used_by=None):
    return logic.Coupon(code, percent, min_order, first_time_only, enabled,
                        limit, list(used_by or []))


def make_order(order_id="ORD1000", phone="9999999999", item_qty=5, unit_price=60):
    item = logic.OrderItem("P001", item_qty, unit_price, [])
    return logic.Order(order_id, phone, NOW, [item], "", 0, 0,
                       item_qty * unit_price, 0, item_qty * unit_price)


# ----------------------------------------------------------------------
# 1. get_available_quantity_after_cart
# ----------------------------------------------------------------------

class TestGetAvailableQuantityAfterCart(unittest.TestCase):
    def test_product_not_in_cart_shows_full_stock(self):
        self.assertEqual(logic.get_available_quantity_after_cart(make_product(), {}), 6)

    def test_partial_cart_reduces_available(self):
        cart = {"P001": logic.CartItem("P001", 3, 60)}
        self.assertEqual(logic.get_available_quantity_after_cart(make_product(), cart), 3)

    def test_cart_equal_to_stock_gives_zero(self):
        cart = {"P001": logic.CartItem("P001", 6, 60)}
        self.assertEqual(logic.get_available_quantity_after_cart(make_product(), cart), 0)

    def test_cart_larger_than_stock_never_negative(self):
        cart = {"P001": logic.CartItem("P001", 9, 60)}
        self.assertEqual(logic.get_available_quantity_after_cart(make_product(), cart), 0)

    def test_other_product_in_cart_does_not_matter(self):
        cart = {"P002": logic.CartItem("P002", 4, 40)}
        self.assertEqual(logic.get_available_quantity_after_cart(make_product(), cart), 6)

    def test_inputs_not_changed(self):
        product, cart = make_product(), {"P001": logic.CartItem("P001", 2, 60)}
        product_before, cart_before = copy.deepcopy(product), copy.deepcopy(cart)
        logic.get_available_quantity_after_cart(product, cart)
        self.assertEqual(product, product_before)
        self.assertEqual(cart, cart_before)


# ----------------------------------------------------------------------
# 2. get_line_subtotal
# ----------------------------------------------------------------------

class TestGetLineSubtotal(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(logic.get_line_subtotal(3, 60), 180)

    def test_single_item(self):
        self.assertEqual(logic.get_line_subtotal(1, 25), 25)

    def test_zero_quantity(self):
        self.assertEqual(logic.get_line_subtotal(0, 60), 0)

    def test_zero_price(self):
        self.assertEqual(logic.get_line_subtotal(5, 0), 0)


# ----------------------------------------------------------------------
# 3. get_returnable_quantity
# ----------------------------------------------------------------------

class TestGetReturnableQuantity(unittest.TestCase):
    def setUp(self):
        self.item = logic.OrderItem("P001", 5, 60, [])

    def test_nothing_returned_yet(self):
        self.assertEqual(logic.get_returnable_quantity(self.item, 0), 5)

    def test_some_returned(self):
        self.assertEqual(logic.get_returnable_quantity(self.item, 2), 3)

    def test_all_returned(self):
        self.assertEqual(logic.get_returnable_quantity(self.item, 5), 0)

    def test_over_returned_never_negative(self):
        self.assertEqual(logic.get_returnable_quantity(self.item, 8), 0)

    def test_item_not_changed(self):
        logic.get_returnable_quantity(self.item, 2)
        self.assertEqual(self.item.qty, 5)


# ----------------------------------------------------------------------
# 4. get_batch_status_label
# ----------------------------------------------------------------------

class TestGetBatchStatusLabel(unittest.TestCase):
    def test_expired(self):
        batch = logic.StockBatch("B1", 3, PAST, "2019-01-01")
        self.assertEqual(logic.get_batch_status_label(batch, NOW), "EXPIRED")

    def test_sellable(self):
        batch = logic.StockBatch("B1", 3, FUTURE, "2026-10-01")
        self.assertEqual(logic.get_batch_status_label(batch, NOW), "SELLABLE")

    def test_depleted(self):
        batch = logic.StockBatch("B1", 0, FUTURE, "2026-10-01")
        self.assertEqual(logic.get_batch_status_label(batch, NOW), "DEPLETED")

    def test_expired_wins_over_empty(self):
        batch = logic.StockBatch("B1", 0, PAST, "2019-01-01")
        self.assertEqual(logic.get_batch_status_label(batch, NOW), "EXPIRED")

    def test_expiry_equal_to_date_only_today_is_not_expired(self):
        batch = logic.StockBatch("B1", 2, "2026-10-09", "2026-10-01")
        self.assertEqual(logic.get_batch_status_label(batch, "2026-10-09"), "SELLABLE")


# ----------------------------------------------------------------------
# 5. validate_new_product_input
# ----------------------------------------------------------------------

class TestValidateNewProductInput(unittest.TestCase):
    def test_valid(self):
        ok, _ = logic.validate_new_product_input("P009", "Juice", "Cold Beverages", 30, 5, 15, "2027-01-01")
        self.assertTrue(ok)

    def test_empty_id(self):
        ok, _ = logic.validate_new_product_input("", "Juice", "Snacks", 30, 5, 15, "2027-01-01")
        self.assertFalse(ok)

    def test_empty_name(self):
        ok, _ = logic.validate_new_product_input("P009", "", "Snacks", 30, 5, 15, "2027-01-01")
        self.assertFalse(ok)

    def test_missing_category(self):
        ok, _ = logic.validate_new_product_input("P009", "Juice", None, 30, 5, 15, "2027-01-01")
        self.assertFalse(ok)

    def test_empty_expiry(self):
        ok, _ = logic.validate_new_product_input("P009", "Juice", "Snacks", 30, 5, 15, "")
        self.assertFalse(ok)

    def test_negative_price(self):
        ok, _ = logic.validate_new_product_input("P009", "Juice", "Snacks", -1, 5, 15, "2027-01-01")
        self.assertFalse(ok)

    def test_negative_quantity(self):
        ok, _ = logic.validate_new_product_input("P009", "Juice", "Snacks", 30, -5, 15, "2027-01-01")
        self.assertFalse(ok)

    def test_negative_cost(self):
        ok, _ = logic.validate_new_product_input("P009", "Juice", "Snacks", 30, 5, -15, "2027-01-01")
        self.assertFalse(ok)

    def test_wrong_date_separator(self):
        ok, msg = logic.validate_new_product_input("P009", "Juice", "Snacks", 30, 5, 15, "2027/01/01")
        self.assertFalse(ok)
        self.assertIn("YYYY-MM-DD", msg)

    def test_wrong_date_length(self):
        ok, _ = logic.validate_new_product_input("P009", "Juice", "Snacks", 30, 5, 15, "27-1-1")
        self.assertFalse(ok)


# ----------------------------------------------------------------------
# 6. validate_restock_input
# ----------------------------------------------------------------------

class TestValidateRestockInput(unittest.TestCase):
    def test_valid(self):
        ok, _ = logic.validate_restock_input(5, 20, "2027-01-01")
        self.assertTrue(ok)

    def test_zero_cost_is_allowed(self):
        ok, _ = logic.validate_restock_input(5, 0, "2027-01-01")
        self.assertTrue(ok)

    def test_zero_quantity(self):
        ok, _ = logic.validate_restock_input(0, 20, "2027-01-01")
        self.assertFalse(ok)

    def test_negative_quantity(self):
        ok, _ = logic.validate_restock_input(-3, 20, "2027-01-01")
        self.assertFalse(ok)

    def test_negative_cost(self):
        ok, _ = logic.validate_restock_input(5, -1, "2027-01-01")
        self.assertFalse(ok)

    def test_bad_date_format(self):
        ok, _ = logic.validate_restock_input(5, 20, "01-01-2027x")
        self.assertFalse(ok)

    def test_empty_date(self):
        ok, _ = logic.validate_restock_input(5, 20, "")
        self.assertFalse(ok)


# ----------------------------------------------------------------------
# 7. validate_removal_input
# ----------------------------------------------------------------------

class TestValidateRemovalInput(unittest.TestCase):
    def test_damaged_with_description(self):
        ok, _ = logic.validate_removal_input(2, "Damaged", None, "Torn")
        self.assertTrue(ok)

    def test_package_damage_with_description(self):
        ok, _ = logic.validate_removal_input(2, "Package Damage", None, "Crushed box")
        self.assertTrue(ok)

    def test_expired_with_expiry_date(self):
        ok, _ = logic.validate_removal_input(2, "Expired", "2026-10-01", None)
        self.assertTrue(ok)

    def test_other_needs_nothing_extra(self):
        ok, _ = logic.validate_removal_input(1, "Other", None, None)
        self.assertTrue(ok)

    def test_zero_quantity(self):
        ok, _ = logic.validate_removal_input(0, "Other", None, None)
        self.assertFalse(ok)

    def test_negative_quantity(self):
        ok, _ = logic.validate_removal_input(-1, "Other", None, None)
        self.assertFalse(ok)

    def test_invalid_reason(self):
        ok, msg = logic.validate_removal_input(1, "Stolen", None, None)
        self.assertFalse(ok)
        self.assertIn("Invalid reason", msg)

    def test_damaged_without_description(self):
        ok, _ = logic.validate_removal_input(1, "Damaged", None, "")
        self.assertFalse(ok)

    def test_package_damage_without_description(self):
        ok, _ = logic.validate_removal_input(1, "Package Damage", None, None)
        self.assertFalse(ok)

    def test_expired_without_expiry_date(self):
        ok, _ = logic.validate_removal_input(1, "Expired", "", None)
        self.assertFalse(ok)


# ----------------------------------------------------------------------
# 8. hash_password
# ----------------------------------------------------------------------

class TestHashPassword(unittest.TestCase):
    SALT = b"0123456789abcdef"

    def test_format_is_salt_colon_hash(self):
        hashed = logic.hash_password("secret", self.SALT)
        self.assertTrue(hashed.startswith(self.SALT.hex() + ":"))
        self.assertEqual(hashed.count(":"), 1)

    def test_same_input_same_output(self):
        self.assertEqual(logic.hash_password("secret", self.SALT),
                         logic.hash_password("secret", self.SALT))

    def test_different_password_different_hash(self):
        self.assertNotEqual(logic.hash_password("secret", self.SALT),
                            logic.hash_password("Secret", self.SALT))

    def test_different_salt_different_hash(self):
        self.assertNotEqual(logic.hash_password("secret", self.SALT),
                            logic.hash_password("secret", b"fedcba9876543210"))

    def test_plain_password_not_visible_in_hash(self):
        self.assertNotIn("secret", logic.hash_password("secret", self.SALT))


# ----------------------------------------------------------------------
# 9. verify_password
# ----------------------------------------------------------------------

class TestVerifyPassword(unittest.TestCase):
    SALT = b"0123456789abcdef"

    def test_correct_password(self):
        hashed = logic.hash_password("secret", self.SALT)
        self.assertTrue(logic.verify_password("secret", hashed))

    def test_wrong_password(self):
        hashed = logic.hash_password("secret", self.SALT)
        self.assertFalse(logic.verify_password("wrong", hashed))

    def test_empty_password_rejected(self):
        hashed = logic.hash_password("secret", self.SALT)
        self.assertFalse(logic.verify_password("", hashed))

    def test_legacy_plain_text_match(self):
        self.assertTrue(logic.verify_password("plainpass", "plainpass"))

    def test_legacy_plain_text_mismatch(self):
        self.assertFalse(logic.verify_password("other", "plainpass"))

    def test_malformed_hash_does_not_crash(self):
        self.assertFalse(logic.verify_password("secret", "abc:def"))


# ----------------------------------------------------------------------
# 10. check_stock_available
# ----------------------------------------------------------------------

class TestCheckStockAvailable(unittest.TestCase):
    def test_within_stock(self):
        self.assertEqual(logic.check_stock_available(make_product(), 3), (True, 6))

    def test_exactly_all_stock(self):
        self.assertEqual(logic.check_stock_available(make_product(), 6), (True, 6))

    def test_more_than_stock(self):
        self.assertEqual(logic.check_stock_available(make_product(), 7), (False, 6))

    def test_no_stock(self):
        product = make_product(batches=[(0, FUTURE, "2026-10-01")])
        self.assertEqual(logic.check_stock_available(product, 1), (False, 0))

    def test_stock_adds_up_across_batches(self):
        product = make_product(batches=[(2, FUTURE, "a"), (3, FUTURE, "b")])
        self.assertEqual(logic.check_stock_available(product, 5), (True, 5))


# ----------------------------------------------------------------------
# 11. get_cart_total
# ----------------------------------------------------------------------

class TestGetCartTotal(unittest.TestCase):
    def test_empty_cart(self):
        self.assertEqual(logic.get_cart_total({}), 0)

    def test_single_item(self):
        self.assertEqual(logic.get_cart_total({"P001": logic.CartItem("P001", 2, 60)}), 120)

    def test_multiple_items(self):
        cart = {"P001": logic.CartItem("P001", 2, 60), "P002": logic.CartItem("P002", 3, 40)}
        self.assertEqual(logic.get_cart_total(cart), 240)

    def test_cart_not_changed(self):
        cart = {"P001": logic.CartItem("P001", 2, 60)}
        before = copy.deepcopy(cart)
        logic.get_cart_total(cart)
        self.assertEqual(cart, before)


# ----------------------------------------------------------------------
# 12. add_to_cart
# ----------------------------------------------------------------------

class TestAddToCart(unittest.TestCase):
    def test_add_new_item(self):
        ok, msg, cart = logic.add_to_cart({}, make_product(), 2)
        self.assertTrue(ok)
        self.assertEqual(cart["P001"].qty, 2)
        self.assertEqual(cart["P001"].unit_price, 60)

    def test_adding_same_product_increases_quantity(self):
        _, _, cart = logic.add_to_cart({}, make_product(), 2)
        ok, _, cart = logic.add_to_cart(cart, make_product(), 3)
        self.assertTrue(ok)
        self.assertEqual(cart["P001"].qty, 5)

    def test_can_add_up_to_exact_stock(self):
        ok, _, cart = logic.add_to_cart({}, make_product(), 6)
        self.assertTrue(ok)
        self.assertEqual(cart["P001"].qty, 6)

    def test_more_than_stock_rejected(self):
        ok, msg, cart = logic.add_to_cart({}, make_product(), 7)
        self.assertFalse(ok)
        self.assertEqual(cart, {})
        self.assertIn("Only 6", msg)

    def test_total_in_cart_cannot_pass_stock(self):
        _, _, cart = logic.add_to_cart({}, make_product(), 5)
        ok, _, cart = logic.add_to_cart(cart, make_product(), 2)
        self.assertFalse(ok)
        self.assertEqual(cart["P001"].qty, 5)

    def test_zero_quantity_rejected(self):
        ok, _, cart = logic.add_to_cart({}, make_product(), 0)
        self.assertFalse(ok)
        self.assertEqual(cart, {})

    def test_negative_quantity_rejected(self):
        ok, _, _ = logic.add_to_cart({}, make_product(), -2)
        self.assertFalse(ok)

    def test_original_cart_is_not_mutated(self):
        original = {"P001": logic.CartItem("P001", 1, 60)}
        before = copy.deepcopy(original)
        logic.add_to_cart(original, make_product(), 2)
        self.assertEqual(original, before)

    def test_product_is_not_mutated(self):
        product = make_product()
        before = copy.deepcopy(product)
        logic.add_to_cart({}, product, 2)
        self.assertEqual(product, before)


# ----------------------------------------------------------------------
# 13. edit_cart_item
# ----------------------------------------------------------------------

class TestEditCartItem(unittest.TestCase):
    def setUp(self):
        self.cart = {"P001": logic.CartItem("P001", 3, 60)}

    def test_update_quantity(self):
        ok, msg, cart = logic.edit_cart_item(self.cart, make_product(), 5)
        self.assertTrue(ok)
        self.assertEqual(cart["P001"].qty, 5)

    def test_reduce_quantity(self):
        ok, _, cart = logic.edit_cart_item(self.cart, make_product(), 1)
        self.assertTrue(ok)
        self.assertEqual(cart["P001"].qty, 1)

    def test_zero_removes_item(self):
        ok, _, cart = logic.edit_cart_item(self.cart, make_product(), 0)
        self.assertTrue(ok)
        self.assertNotIn("P001", cart)

    def test_negative_rejected(self):
        ok, _, cart = logic.edit_cart_item(self.cart, make_product(), -1)
        self.assertFalse(ok)
        self.assertEqual(cart["P001"].qty, 3)

    def test_more_than_stock_rejected(self):
        ok, _, cart = logic.edit_cart_item(self.cart, make_product(), 7)
        self.assertFalse(ok)
        self.assertEqual(cart["P001"].qty, 3)

    def test_exact_stock_allowed(self):
        ok, _, cart = logic.edit_cart_item(self.cart, make_product(), 6)
        self.assertTrue(ok)
        self.assertEqual(cart["P001"].qty, 6)

    def test_product_not_in_cart_rejected(self):
        ok, msg, cart = logic.edit_cart_item({}, make_product(), 2)
        self.assertFalse(ok)
        self.assertEqual(cart, {})

    def test_original_cart_is_not_mutated(self):
        before = copy.deepcopy(self.cart)
        logic.edit_cart_item(self.cart, make_product(), 0)
        self.assertEqual(self.cart, before)


# ----------------------------------------------------------------------
# 14. calculate_coupon_discount
# ----------------------------------------------------------------------

class TestCalculateCouponDiscount(unittest.TestCase):
    def test_twenty_percent(self):
        self.assertEqual(logic.calculate_coupon_discount(600, make_coupon(percent=20)), 120)

    def test_forty_percent(self):
        self.assertEqual(logic.calculate_coupon_discount(100, make_coupon(percent=40)), 40)

    def test_fraction_is_cut_down(self):
        self.assertEqual(logic.calculate_coupon_discount(99, make_coupon(percent=10)), 9)

    def test_zero_total(self):
        self.assertEqual(logic.calculate_coupon_discount(0, make_coupon()), 0)

    def test_coupon_not_changed(self):
        coupon = make_coupon()
        before = copy.deepcopy(coupon)
        logic.calculate_coupon_discount(600, coupon)
        self.assertEqual(coupon, before)


# ----------------------------------------------------------------------
# 15. validate_and_apply_coupon
# ----------------------------------------------------------------------

class TestValidateAndApplyCoupon(unittest.TestCase):
    def test_valid_coupon(self):
        ok, discount, _ = logic.validate_and_apply_coupon(600, make_coupon(), make_customer())
        self.assertTrue(ok)
        self.assertEqual(discount, 120)

    def test_disabled_coupon(self):
        ok, discount, msg = logic.validate_and_apply_coupon(600, make_coupon(enabled=False), make_customer())
        self.assertFalse(ok)
        self.assertEqual(discount, 0)
        self.assertIn("disabled", msg)

    def test_below_minimum_order(self):
        ok, discount, msg = logic.validate_and_apply_coupon(499, make_coupon(), make_customer())
        self.assertFalse(ok)
        self.assertEqual(discount, 0)
        self.assertIn("500", msg)

    def test_exactly_minimum_order(self):
        ok, discount, _ = logic.validate_and_apply_coupon(500, make_coupon(), make_customer())
        self.assertTrue(ok)
        self.assertEqual(discount, 100)

    def test_first_time_coupon_for_returning_customer(self):
        coupon = make_coupon(code="WELCOME40", percent=40, min_order=0, first_time_only=True, limit=1)
        ok, _, msg = logic.validate_and_apply_coupon(100, coupon, make_customer(first_time=False))
        self.assertFalse(ok)
        self.assertIn("first-time", msg)

    def test_first_time_coupon_for_new_customer(self):
        coupon = make_coupon(code="WELCOME40", percent=40, min_order=0, first_time_only=True, limit=1)
        ok, discount, _ = logic.validate_and_apply_coupon(100, coupon, make_customer(first_time=True))
        self.assertTrue(ok)
        self.assertEqual(discount, 40)

    def test_usage_limit_reached(self):
        coupon = make_coupon(limit=1, used_by=["9999999999"])
        ok, _, msg = logic.validate_and_apply_coupon(600, coupon, make_customer())
        self.assertFalse(ok)
        self.assertIn("limit", msg)

    def test_usage_below_limit_still_allowed(self):
        coupon = make_coupon(limit=2, used_by=["9999999999"])
        ok, _, _ = logic.validate_and_apply_coupon(600, coupon, make_customer())
        self.assertTrue(ok)

    def test_other_customers_usage_does_not_count(self):
        coupon = make_coupon(limit=1, used_by=["1111111111"])
        ok, _, _ = logic.validate_and_apply_coupon(600, coupon, make_customer())
        self.assertTrue(ok)

    def test_coupon_and_customer_not_changed(self):
        coupon, customer = make_coupon(), make_customer()
        coupon_before, customer_before = copy.deepcopy(coupon), copy.deepcopy(customer)
        logic.validate_and_apply_coupon(600, coupon, customer)
        self.assertEqual(coupon, coupon_before)
        self.assertEqual(customer, customer_before)


# ----------------------------------------------------------------------
# 16. calculate_loyalty_earned
# ----------------------------------------------------------------------

class TestCalculateLoyaltyEarned(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(logic.calculate_loyalty_earned(0), 0)

    def test_below_ten_earns_nothing(self):
        self.assertEqual(logic.calculate_loyalty_earned(9), 0)

    def test_exactly_ten(self):
        self.assertEqual(logic.calculate_loyalty_earned(10), 1)

    def test_rounds_down(self):
        self.assertEqual(logic.calculate_loyalty_earned(159), 15)

    def test_round_amount(self):
        self.assertEqual(logic.calculate_loyalty_earned(160), 16)


# ----------------------------------------------------------------------
# 17. calculate_loyalty_redemption
# ----------------------------------------------------------------------

class TestCalculateLoyaltyRedemption(unittest.TestCase):
    def test_zero_points(self):
        self.assertEqual(logic.calculate_loyalty_redemption(0), 0)

    def test_one_point_is_one_rupee(self):
        self.assertEqual(logic.calculate_loyalty_redemption(1), 1)

    def test_many_points(self):
        self.assertEqual(logic.calculate_loyalty_redemption(33), 33)


# ----------------------------------------------------------------------
# 18. resolve_loyalty_coupon_combination
# ----------------------------------------------------------------------

class TestResolveLoyaltyCouponCombination(unittest.TestCase):
    def test_coupon_and_points_not_allowed_together(self):
        self.assertEqual(logic.resolve_loyalty_coupon_combination(True, 10), 0)

    def test_coupon_without_points(self):
        self.assertEqual(logic.resolve_loyalty_coupon_combination(True, 0), 0)

    def test_points_without_coupon(self):
        self.assertEqual(logic.resolve_loyalty_coupon_combination(False, 10), 10)

    def test_neither(self):
        self.assertEqual(logic.resolve_loyalty_coupon_combination(False, 0), 0)


# ----------------------------------------------------------------------
# 19. allocate_fifo_batches
# ----------------------------------------------------------------------

class TestAllocateFifoBatches(unittest.TestCase):
    def test_single_batch(self):
        ok, _, plan = logic.allocate_fifo_batches(make_product(), 2, NOW)
        self.assertTrue(ok)
        self.assertEqual([(a.batch_id, a.qty) for a in plan], [("B1", 2)])

    def test_takes_from_oldest_batch_first_and_spans_batches(self):
        product = make_product(batches=[(2, FUTURE, "2026-10-01 00:00:00"),
                                        (5, FUTURE, "2026-10-02 00:00:00")])
        ok, _, plan = logic.allocate_fifo_batches(product, 4, NOW)
        self.assertTrue(ok)
        self.assertEqual([(a.batch_id, a.qty) for a in plan], [("B1", 2), ("B2", 2)])

    def test_order_is_by_added_time_not_by_dictionary_order(self):
        product = make_product(batches=[(5, FUTURE, "2026-10-05 00:00:00"),
                                        (5, FUTURE, "2026-10-01 00:00:00")])
        ok, _, plan = logic.allocate_fifo_batches(product, 3, NOW)
        self.assertEqual(plan[0].batch_id, "B2")

    def test_skips_expired_batch(self):
        product = make_product(batches=[(5, PAST, "2026-09-01 00:00:00"),
                                        (5, FUTURE, "2026-10-01 00:00:00")])
        ok, _, plan = logic.allocate_fifo_batches(product, 3, NOW)
        self.assertTrue(ok)
        self.assertEqual([(a.batch_id, a.qty) for a in plan], [("B2", 3)])

    def test_skips_empty_batch(self):
        product = make_product(batches=[(0, FUTURE, "2026-09-01 00:00:00"),
                                        (4, FUTURE, "2026-10-01 00:00:00")])
        ok, _, plan = logic.allocate_fifo_batches(product, 4, NOW)
        self.assertTrue(ok)
        self.assertEqual([(a.batch_id, a.qty) for a in plan], [("B2", 4)])

    def test_exactly_all_stock(self):
        ok, _, plan = logic.allocate_fifo_batches(make_product(), 6, NOW)
        self.assertTrue(ok)
        self.assertEqual(sum(a.qty for a in plan), 6)

    def test_not_enough_stock(self):
        ok, msg, plan = logic.allocate_fifo_batches(make_product(), 7, NOW)
        self.assertFalse(ok)
        self.assertEqual(plan, [])
        self.assertIn("Cold Coffee", msg)

    def test_only_expired_stock_fails(self):
        product = make_product(batches=[(5, PAST, "2026-09-01 00:00:00")])
        ok, _, _ = logic.allocate_fifo_batches(product, 1, NOW)
        self.assertFalse(ok)

    def test_plan_records_expiry_date(self):
        ok, _, plan = logic.allocate_fifo_batches(make_product(), 1, NOW)
        self.assertEqual(plan[0].expiry_date, FUTURE)

    def test_does_not_change_stock(self):
        product = make_product()
        before = copy.deepcopy(product)
        logic.allocate_fifo_batches(product, 3, NOW)
        self.assertEqual(product, before)


# ----------------------------------------------------------------------
# 20. calculate_checkout
# ----------------------------------------------------------------------

class TestCalculateCheckout(unittest.TestCase):
    def run_checkout(self, qty=2, points=0, cash=120, coupon=None, customer=None,
                     products=None, cart=None):
        products = products if products is not None else {"P001": make_product(batches=[(20, FUTURE, "2026-10-01 00:00:00")])}
        cart = cart if cart is not None else {"P001": logic.CartItem("P001", qty, 60)}
        customer = customer or make_customer()
        return logic.calculate_checkout(cart, products, coupon, customer, points, cash, NOW, "ORD1000")

    def test_empty_cart(self):
        res = self.run_checkout(cart={})
        self.assertFalse(res.success)
        self.assertIn("empty", res.error_msg)

    def test_simple_success_with_change(self):
        res = self.run_checkout(qty=2, cash=150)
        self.assertTrue(res.success)
        self.assertEqual(res.order.final_total, 120)
        self.assertEqual(res.order.change, 30)
        self.assertEqual(res.order.amount_paid, 150)
        self.assertEqual(res.points_earned, 12)

    def test_exact_payment_has_zero_change(self):
        res = self.run_checkout(qty=2, cash=120)
        self.assertTrue(res.success)
        self.assertEqual(res.order.change, 0)

    def test_order_details(self):
        res = self.run_checkout(qty=2, cash=120)
        self.assertEqual(res.order.order_id, "ORD1000")
        self.assertEqual(res.order.customer_phone, "9999999999")
        self.assertEqual(res.order.timestamp, NOW)
        self.assertEqual(res.order.items[0].product_id, "P001")
        self.assertEqual(res.order.items[0].qty, 2)

    def test_underpayment_rejected(self):
        res = self.run_checkout(qty=2, cash=50)
        self.assertFalse(res.success)
        self.assertIn("short by Rs 70", res.error_msg)
        self.assertIsNone(res.order)

    def test_valid_coupon_reduces_total(self):
        res = self.run_checkout(qty=10, cash=500, coupon=make_coupon())
        self.assertTrue(res.success)
        self.assertEqual(res.order.coupon_discount, 120)
        self.assertEqual(res.order.coupon_code, "SAVE20")
        self.assertEqual(res.order.final_total, 480)
        self.assertEqual(res.order.change, 20)
        self.assertEqual(res.points_earned, 48)

    def test_invalid_coupon_rejected(self):
        res = self.run_checkout(qty=2, cash=120, coupon=make_coupon())
        self.assertFalse(res.success)
        self.assertIn("500", res.error_msg)

    def test_points_reduce_total(self):
        res = self.run_checkout(qty=2, points=20, cash=100, customer=make_customer(points=30))
        self.assertTrue(res.success)
        self.assertEqual(res.order.loyalty_redeemed, 20)
        self.assertEqual(res.order.final_total, 100)
        self.assertEqual(res.points_earned, 10)

    def test_more_points_than_owned_rejected(self):
        res = self.run_checkout(qty=2, points=10, cash=120, customer=make_customer(points=5))
        self.assertFalse(res.success)
        self.assertIn("Insufficient loyalty points", res.error_msg)

    def test_coupon_and_points_together_rejected(self):
        res = self.run_checkout(qty=10, points=10, cash=600, coupon=make_coupon(),
                                customer=make_customer(points=50))
        self.assertFalse(res.success)
        self.assertIn("Cannot combine", res.error_msg)

    def test_points_larger_than_bill_gives_zero_total(self):
        res = self.run_checkout(qty=1, points=100, cash=0, customer=make_customer(points=100))
        self.assertTrue(res.success)
        self.assertEqual(res.order.final_total, 0)
        self.assertEqual(res.order.change, 0)
        self.assertEqual(res.points_earned, 0)

    def test_not_enough_stock(self):
        products = {"P001": make_product(batches=[(1, FUTURE, "2026-10-01 00:00:00")])}
        res = self.run_checkout(qty=2, cash=120, products=products)
        self.assertFalse(res.success)
        self.assertIn("Insufficient", res.error_msg)

    def test_only_expired_stock(self):
        products = {"P001": make_product(batches=[(10, PAST, "2026-09-01 00:00:00")])}
        res = self.run_checkout(qty=2, cash=120, products=products)
        self.assertFalse(res.success)

    def test_unknown_product_in_cart(self):
        res = self.run_checkout(qty=2, cash=120, products={})
        self.assertFalse(res.success)
        self.assertIn("not found", res.error_msg)

    def test_allocation_plan_matches_order(self):
        res = self.run_checkout(qty=2, cash=120)
        self.assertEqual(res.allocations_plan["P001"][0].qty, 2)
        self.assertEqual(res.order.items[0].allocations[0].batch_id, "B1")
        self.assertEqual(res.order.items[0].allocations[0].expiry_date, FUTURE)

    def test_nothing_is_changed(self):
        products = {"P001": make_product(batches=[(20, FUTURE, "2026-10-01 00:00:00")])}
        cart = {"P001": logic.CartItem("P001", 2, 60)}
        customer = make_customer(points=30)
        coupon = make_coupon()
        before = copy.deepcopy((products, cart, customer, coupon))
        logic.calculate_checkout(cart, products, coupon, customer, 0, 120, NOW, "ORD1000")
        self.assertEqual((products, cart, customer, coupon), before)


# ----------------------------------------------------------------------
# 21. calculate_process_return
# ----------------------------------------------------------------------

class TestCalculateProcessReturn(unittest.TestCase):
    def request(self, qty=2, reason="Damaged", expiry=None, desc="Torn", pid="P001", oid="ORD1000"):
        return logic.ReturnRequest(oid, pid, qty, reason, expiry, desc)

    def test_order_not_found(self):
        res = logic.calculate_process_return(self.request(), None, 0)
        self.assertFalse(res.success)
        self.assertIn("Order not found", res.error_msg)

    def test_product_not_in_order(self):
        res = logic.calculate_process_return(self.request(pid="P009"), make_order(), 0)
        self.assertFalse(res.success)
        self.assertIn("not in order", res.error_msg)

    def test_quantity_above_what_was_bought(self):
        res = logic.calculate_process_return(self.request(qty=6), make_order(item_qty=5), 0)
        self.assertFalse(res.success)
        self.assertIn("5 remains", res.error_msg)

    def test_earlier_returns_reduce_eligible_quantity(self):
        res = logic.calculate_process_return(self.request(qty=2), make_order(item_qty=5), 4)
        self.assertFalse(res.success)
        self.assertIn("1 remains", res.error_msg)

    def test_exactly_the_remaining_quantity_is_allowed(self):
        res = logic.calculate_process_return(self.request(qty=1), make_order(item_qty=5), 4)
        self.assertTrue(res.success)

    def test_invalid_reason(self):
        res = logic.calculate_process_return(self.request(reason="Other"), make_order(), 0)
        self.assertFalse(res.success)
        self.assertIn("Invalid return reason", res.error_msg)

    def test_expired_needs_expiry_date(self):
        res = logic.calculate_process_return(self.request(reason="Expired", expiry=None, desc=None), make_order(), 0)
        self.assertFalse(res.success)
        self.assertIn("Expiry date", res.error_msg)

    def test_damaged_needs_description(self):
        res = logic.calculate_process_return(self.request(reason="Damaged", desc=""), make_order(), 0)
        self.assertFalse(res.success)
        self.assertIn("Description", res.error_msg)

    def test_valid_damaged_return(self):
        res = logic.calculate_process_return(self.request(qty=2), make_order(unit_price=60), 0)
        self.assertTrue(res.success)
        self.assertEqual(res.refund_amount, 120)
        self.assertEqual(res.points_awarded, 12)

    def test_valid_expired_return(self):
        res = logic.calculate_process_return(
            self.request(qty=1, reason="Expired", expiry="2026-10-01", desc=None), make_order(unit_price=60), 0)
        self.assertTrue(res.success)
        self.assertEqual(res.refund_amount, 60)
        self.assertEqual(res.points_awarded, 6)

    def test_small_refund_gives_no_points(self):
        res = logic.calculate_process_return(self.request(qty=1), make_order(unit_price=5), 0)
        self.assertTrue(res.success)
        self.assertEqual(res.points_awarded, 0)

    def test_order_not_changed(self):
        order = make_order()
        before = copy.deepcopy(order)
        logic.calculate_process_return(self.request(), order, 0)
        self.assertEqual(order, before)


# ----------------------------------------------------------------------
# 22. calculate_profit_loss
# ----------------------------------------------------------------------

class TestCalculateProfitLoss(unittest.TestCase):
    def setUp(self):
        self.products = {"P001": make_product(price=60, cost=30)}

    def order(self, qty, total):
        item = logic.OrderItem("P001", qty, 60, [])
        return logic.Order("ORD1", "999", NOW, [item], "", 0, 0, total, 0, total)

    def test_empty_everything_is_zero(self):
        result = logic.calculate_profit_loss([], {}, [], [])
        self.assertEqual(result, {"Sales Revenue": 0, "Product Costs": 0, "Refunds": 0,
                                  "Stock Losses": 0, "Net Result": 0})

    def test_profit(self):
        result = logic.calculate_profit_loss([self.order(2, 120)], self.products, [], [])
        self.assertEqual(result["Sales Revenue"], 120)
        self.assertEqual(result["Product Costs"], 60)
        self.assertEqual(result["Net Result"], 60)

    def test_loss_from_refund(self):
        refund = logic.Return("RET1", "ORD1", "P001", 1, "Damaged", None, "Torn", 60, NOW)
        result = logic.calculate_profit_loss([self.order(1, 60)], self.products, [refund], [])
        self.assertEqual(result["Refunds"], 60)
        self.assertEqual(result["Net Result"], -30)

    def test_stock_loss_is_counted_at_cost(self):
        removal = logic.StockRemoval("REM1", "P001", 2, "Damaged", None, "Dropped", NOW)
        result = logic.calculate_profit_loss([], self.products, [], [removal])
        self.assertEqual(result["Stock Losses"], 60)
        self.assertEqual(result["Net Result"], -60)

    def test_return_removals_are_not_double_counted(self):
        removal = logic.StockRemoval("REM2", "P001", 2, "Return - Damaged", None, "Torn", NOW)
        result = logic.calculate_profit_loss([], self.products, [], [removal])
        self.assertEqual(result["Stock Losses"], 0)

    def test_break_even(self):
        result = logic.calculate_profit_loss([self.order(1, 30)], self.products, [], [])
        self.assertEqual(result["Net Result"], 0)

    def test_unknown_product_cost_is_ignored(self):
        result = logic.calculate_profit_loss([self.order(1, 60)], {}, [], [])
        self.assertEqual(result["Product Costs"], 0)
        self.assertEqual(result["Net Result"], 60)

    def test_inputs_not_changed(self):
        orders = [self.order(2, 120)]
        before = copy.deepcopy((orders, self.products))
        logic.calculate_profit_loss(orders, self.products, [], [])
        self.assertEqual((orders, self.products), before)


# ----------------------------------------------------------------------
# Product.sellable_qty (property used by many functions above)
# ----------------------------------------------------------------------

class TestProductSellableQty(unittest.TestCase):
    def test_adds_all_batches(self):
        product = make_product(batches=[(2, FUTURE, "a"), (3, FUTURE, "b")])
        self.assertEqual(product.sellable_qty, 5)

    def test_no_batches(self):
        self.assertEqual(make_product(batches=[]).sellable_qty, 0)


if __name__ == "__main__":
    unittest.main()
