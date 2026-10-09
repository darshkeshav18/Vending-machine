import unittest
import copy
import logic

class TestPureLogic(unittest.TestCase):
    
    def setUp(self):
        self.p1 = logic.Product("P001", "Coffee", "Hot", 60, 30, 2, 2)
        self.p1.stock_batches["B1"] = logic.StockBatch("B1", 5, "2099-01-01", "2026-01-01")
        self.c1 = logic.Customer("1", "A", True, 0)
        
    def test_get_available_quantity_after_cart(self):
        cart = {"P001": logic.CartItem("P001", 2, 60)}
        p_copy = copy.deepcopy(self.p1)
        cart_copy = copy.deepcopy(cart)
        
        self.assertEqual(logic.get_available_quantity_after_cart(self.p1, cart), 3)
        self.assertEqual(logic.get_available_quantity_after_cart(self.p1, {}), 5) # Edge case: empty cart
        
        # Check purity
        self.assertEqual(self.p1, p_copy)
        self.assertEqual(cart, cart_copy)

    def test_get_line_subtotal(self):
        self.assertEqual(logic.get_line_subtotal(3, 60), 180)
        self.assertEqual(logic.get_line_subtotal(0, 60), 0)

    def test_get_returnable_quantity(self):
        oi = logic.OrderItem("P001", 5, 60)
        oi_copy = copy.deepcopy(oi)
        
        self.assertEqual(logic.get_returnable_quantity(oi, 2), 3)
        self.assertEqual(logic.get_returnable_quantity(oi, 5), 0) # Edge: full return
        self.assertEqual(logic.get_returnable_quantity(oi, 6), 0) # Edge: over returned?
        
        self.assertEqual(oi, oi_copy)

    def test_get_batch_status_label(self):
        b = logic.StockBatch("B1", 5, "2025-01-01", "2024-01-01")
        b_copy = copy.deepcopy(b)
        
        self.assertEqual(logic.get_batch_status_label(b, "2024-06-01"), "SELLABLE")
        self.assertEqual(logic.get_batch_status_label(b, "2026-01-01"), "EXPIRED")
        
        b2 = logic.StockBatch("B1", 0, "2099-01-01", "2024-01-01")
        self.assertEqual(logic.get_batch_status_label(b2, "2024-06-01"), "DEPLETED")
        
        self.assertEqual(b, b_copy)

    def test_validate_new_product_input(self):
        valid, msg = logic.validate_new_product_input("P", "N", "C", 10, 5, 5, "2099-01-01")
        self.assertTrue(valid)
        valid, msg = logic.validate_new_product_input("", "N", "C", 10, 5, 5, "2099-01-01") # Invalid empty string
        self.assertFalse(valid)
        valid, msg = logic.validate_new_product_input("P", "N", "C", -1, 5, 5, "2099-01-01") # Invalid neg
        self.assertFalse(valid)
        valid, msg = logic.validate_new_product_input("P", "N", "C", 10, 5, 5, "2099-1-1") # Invalid date format
        self.assertFalse(valid)

    def test_validate_restock_input(self):
        valid, msg = logic.validate_restock_input(5, 10, "2099-01-01")
        self.assertTrue(valid)
        valid, msg = logic.validate_restock_input(0, 10, "2099-01-01")
        self.assertFalse(valid)
        valid, msg = logic.validate_restock_input(5, -1, "2099-01-01")
        self.assertFalse(valid)
        valid, msg = logic.validate_restock_input(5, 10, "99-01-01")
        self.assertFalse(valid)

    def test_validate_removal_input(self):
        valid, msg = logic.validate_removal_input(1, "Damaged", None, "Broken")
        self.assertTrue(valid)
        valid, msg = logic.validate_removal_input(1, "Expired", None, None)
        self.assertFalse(valid) # Missing date
        valid, msg = logic.validate_removal_input(1, "Damaged", None, "")
        self.assertFalse(valid) # Missing desc
        valid, msg = logic.validate_removal_input(0, "Damaged", None, "Desc")
        self.assertFalse(valid) # Zero qty

    def test_hash_password(self):
        salt = b"salt123"
        hashed = logic.hash_password("mypass", salt)
        self.assertTrue(":" in hashed)
        self.assertEqual(hashed.split(":")[0], salt.hex())
        
    def test_verify_password(self):
        salt = b"salt123"
        hashed = logic.hash_password("mypass", salt)
        self.assertTrue(logic.verify_password("mypass", hashed))
        self.assertFalse(logic.verify_password("wrong", hashed))
        self.assertTrue(logic.verify_password("plain", "plain")) # legacy fallback

    def test_check_stock_available(self):
        p_copy = copy.deepcopy(self.p1)
        avail, max_qty = logic.check_stock_available(self.p1, 3)
        self.assertTrue(avail)
        self.assertEqual(max_qty, 5)
        
        avail, max_qty = logic.check_stock_available(self.p1, 10)
        self.assertFalse(avail)
        self.assertEqual(self.p1, p_copy)

    def test_get_cart_total(self):
        cart = {"P1": logic.CartItem("P1", 2, 50), "P2": logic.CartItem("P2", 1, 100)}
        cart_copy = copy.deepcopy(cart)
        self.assertEqual(logic.get_cart_total(cart), 200)
        self.assertEqual(cart, cart_copy)

    def test_add_to_cart(self):
        cart = {}
        cart_copy = copy.deepcopy(cart)
        p_copy = copy.deepcopy(self.p1)
        
        success, msg, new_cart = logic.add_to_cart(cart, self.p1, 3)
        self.assertTrue(success)
        self.assertIn("P001", new_cart)
        self.assertEqual(new_cart["P001"].qty, 3)
        
        success, msg, new_cart2 = logic.add_to_cart(new_cart, self.p1, 5) # 3+5=8 > 5 limit
        self.assertFalse(success)
        
        success, msg, new_cart3 = logic.add_to_cart(cart, self.p1, 0)
        self.assertFalse(success)
        
        # Original inputs strictly unchanged
        self.assertEqual(cart, cart_copy)
        self.assertEqual(self.p1, p_copy)

    def test_edit_cart_item(self):
        cart = {"P001": logic.CartItem("P001", 2, 60)}
        cart_copy = copy.deepcopy(cart)
        p_copy = copy.deepcopy(self.p1)
        
        success, msg, new_cart = logic.edit_cart_item(cart, self.p1, 1)
        self.assertTrue(success)
        self.assertEqual(new_cart["P001"].qty, 1)
        
        success, msg, new_cart2 = logic.edit_cart_item(cart, self.p1, 0)
        self.assertTrue(success)
        self.assertNotIn("P001", new_cart2)
        
        success, msg, new_cart3 = logic.edit_cart_item(cart, self.p1, -1)
        self.assertFalse(success)
        
        # Purity check
        self.assertEqual(cart, cart_copy)
        self.assertEqual(self.p1, p_copy)
        
    def test_calculate_coupon_discount(self):
        cpn = logic.Coupon("S20", 20, 100, False, True, 1, [])
        cpn_copy = copy.deepcopy(cpn)
        self.assertEqual(logic.calculate_coupon_discount(200, cpn), 40)
        self.assertEqual(cpn, cpn_copy)

    def test_validate_and_apply_coupon(self):
        cpn = logic.Coupon("S20", 20, 100, False, True, 1, [])
        cpn_copy = copy.deepcopy(cpn)
        c_copy = copy.deepcopy(self.c1)
        
        valid, discount, msg = logic.validate_and_apply_coupon(50, cpn, self.c1) # Below min
        self.assertFalse(valid)
        
        valid, discount, msg = logic.validate_and_apply_coupon(200, cpn, self.c1)
        self.assertTrue(valid)
        self.assertEqual(discount, 40)
        
        # Purity checks
        self.assertEqual(cpn, cpn_copy)
        self.assertEqual(self.c1, c_copy)

    def test_calculate_loyalty_earned(self):
        self.assertEqual(logic.calculate_loyalty_earned(120), 12)
        self.assertEqual(logic.calculate_loyalty_earned(0), 0)

    def test_calculate_loyalty_redemption(self):
        self.assertEqual(logic.calculate_loyalty_redemption(15), 15)
        self.assertEqual(logic.calculate_loyalty_redemption(0), 0)

    def test_resolve_loyalty_coupon_combination(self):
        self.assertEqual(logic.resolve_loyalty_coupon_combination(True, 5), 0)
        self.assertEqual(logic.resolve_loyalty_coupon_combination(False, 5), 5)
        
    def test_allocate_fifo_batches(self):
        p_copy = copy.deepcopy(self.p1)
        
        # Normal allocation
        success, msg, allocs = logic.allocate_fifo_batches(self.p1, 3, "2026-01-01")
        self.assertTrue(success)
        self.assertEqual(len(allocs), 1)
        self.assertEqual(allocs[0].qty, 3)
        
        # Allocation failure
        success, msg, allocs2 = logic.allocate_fifo_batches(self.p1, 10, "2026-01-01")
        self.assertFalse(success)
        
        # Purity check
        self.assertEqual(self.p1, p_copy)

    def test_calculate_checkout(self):
        cart = {"P001": logic.CartItem("P001", 2, 60)}
        products = {"P001": self.p1}
        
        cart_copy = copy.deepcopy(cart)
        products_copy = copy.deepcopy(products)
        c_copy = copy.deepcopy(self.c1)
        
        calc = logic.calculate_checkout(cart, products, None, self.c1, 0, 120, "2026-01-01", "ORD1")
        
        self.assertTrue(calc.success)
        self.assertIsNotNone(calc.order)
        self.assertEqual(calc.order.change, 0)
        
        # Purity checks - no input structures modified!
        self.assertEqual(cart, cart_copy)
        self.assertEqual(products, products_copy)
        self.assertEqual(self.c1, c_copy)

    def test_calculate_process_return(self):
        oi = logic.OrderItem("P001", 2, 60, [])
        order = logic.Order("ORD1", "1", "2026-01-01", [oi], "", 0, 0, 120, 0, 120)
        
        order_copy = copy.deepcopy(order)
        
        req = logic.ReturnRequest("ORD1", "P001", 1, "Damaged", None, "Torn")
        calc = logic.calculate_process_return(req, order, 0)
        
        self.assertTrue(calc.success)
        self.assertEqual(calc.refund_amount, 60)
        self.assertEqual(calc.points_awarded, 6)
        
        # Check purity
        self.assertEqual(order, order_copy)

    def test_calculate_profit_loss(self):
        oi = logic.OrderItem("P001", 2, 60, [])
        order = logic.Order("ORD1", "1", "2026-01-01", [oi], "", 0, 0, 120, 0, 120)
        orders = [order]
        products = {"P001": self.p1}
        returns = []
        removals = []
        
        orders_copy = copy.deepcopy(orders)
        products_copy = copy.deepcopy(products)
        returns_copy = copy.deepcopy(returns)
        removals_copy = copy.deepcopy(removals)
        
        report = logic.calculate_profit_loss(orders, products, returns, removals)
        self.assertEqual(report["Sales Revenue"], 120)
        self.assertEqual(report["Product Costs"], 60) # 2 * 30
        self.assertEqual(report["Net Result"], 60)
        
        # Check purity
        self.assertEqual(orders, orders_copy)
        self.assertEqual(products, products_copy)
        self.assertEqual(returns, returns_copy)
        self.assertEqual(removals, removals_copy)

if __name__ == '__main__':
    unittest.main()
