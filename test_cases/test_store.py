import unittest
import os
import store
import logic

class TestStore(unittest.TestCase):
    def test_csv_persistence(self):
        test_file = "test_data.csv"
        
        c = store.get_or_create_customer("999", "Tester")
        store.OWNER_AUTH.name = "Admin"
        store.OWNER_AUTH.password_hash = "fakehash"
        store.OWNER_AUTH.is_set = True
        store.PRODUCTS["P001"].cost = 25
        
        cart = {"P001": logic.CartItem("P001", 2, store.PRODUCTS["P001"].price)}
        req = logic.CheckoutRequest(0, 120, None)
        res = store.checkout(c, cart, req, "2026-01-01")
        
        store.remove_stock("P002", 1, "Damaged", None, "Desc", "2026-01-01")
        
        ret_req = logic.ReturnRequest(res.order.order_id, "P001", 1, "Damaged", None, "Torn")
        store.process_return(ret_req, "2026-01-02")
        
        store.save_data(test_file)
        
        store.PRODUCTS.clear()
        store.CUSTOMERS.clear()
        store.ORDERS.clear()
        store.STOCK_REMOVALS.clear()
        store.RETURNS.clear()
        store.OWNER_AUTH.name = ""
        store.OWNER_AUTH.password_hash = ""
        store.OWNER_AUTH.is_set = False
        
        store.load_data(test_file)
        
        self.assertIn("999", store.CUSTOMERS)
        self.assertEqual(store.CUSTOMERS["999"].name, "Tester")
        self.assertTrue(store.OWNER_AUTH.is_set)
        self.assertEqual(store.OWNER_AUTH.name, "Admin")
        self.assertEqual(store.PRODUCTS["P001"].cost, 25)
        self.assertEqual(len(store.ORDERS), 1)
        self.assertEqual(len(store.STOCK_REMOVALS), 2) 
        self.assertEqual(len(store.RETURNS), 1)
        
        if os.path.exists(test_file):
            os.remove(test_file)

    def test_csv_edge_cases(self):
        test_file = "test_data_edge.csv"
        
        open(test_file, 'w').close()
        store.load_data(test_file)
        self.assertIn("P001", store.PRODUCTS) 
        
        with open(test_file, 'w', newline='', encoding='utf-8') as f:
            f.write("RecordType,Col1,Col2\n")
            f.write("PRODUCT,P99,BadProduct,Snacks\n") 
            f.write("CUSTOMER,888,Bob,True,0\n") 
            f.write("CUSTOMER,888,DuplicateBob,False,10\n") 
        
        store.load_data(test_file)
        self.assertNotIn("P99", store.PRODUCTS) 
        self.assertIn("888", store.CUSTOMERS)
        self.assertEqual(store.CUSTOMERS["888"].name, "Bob") 
        
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == '__main__':
    unittest.main()
