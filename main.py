import sys
import os
from datetime import datetime
from typing import Dict, Optional

import logic
import store

def get_current_date() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def ask_continue(prompt: str) -> bool:
    while True:
        ans = input(f"{prompt} (Y/N): ").strip().upper()
        if ans == 'Y':
            return True
        elif ans == 'N':
            return False
        display_error("Please enter Y or N.")

def display_error(msg: str):
    print(f"\nError: {msg}")


def display_cart(cart: Dict[str, logic.CartItem]):
    print("\n--- Current Cart ---")
    print(f"{'ID':<6} | {'Name':<15} | {'Qty':<5} | {'Subtotal'}")
    print("-" * 45)
    
    for item in cart.values():
        p = store.get_product(item.product_id)
        if p:
            sub = logic.get_line_subtotal(item.qty, p.price)
            print(f"{item.product_id:<6} | {p.name:<15} | {item.qty:<5} | Rs {sub}")
            
    total = logic.get_cart_total(cart)
    print("-" * 45)
    print(f"Total: Rs {total}")

def customer_flow():
    phone = input("\nEnter your phone number: ").strip()
    name = input("Enter your name: ").strip()
    
    customer = store.get_or_create_customer(phone, name)
    print(f"\nWelcome, {customer.name}!")
    if customer.is_first_time:
        print("As a first-time customer, you can use coupon WELCOME40!")
    
    cart: Dict[str, logic.CartItem] = {}
    active_selected_product_id: Optional[str] = None
    active_coupon_code: Optional[str] = None
    
    while True:
        print("\n--- Customer Menu ---")
        print("1. View Products")
        print("2. Select Product")
        print("3. Add to Cart")
        print("4. View Cart")
        print("5. Edit Cart Item")
        print("6. Apply / Remove Coupon")
        print("7. View Loyalty Points")
        print("8. Make Payment")
        print("9. View Receipt")
        print("10. View Order History")
        print("11. View Customer Report")
        print("12. Exit")
        
        choice = input("Select an option: ").strip()
        
        if choice == "1":
            print("\n--- Product Catalogue ---")
            print(f"{'ID':<6} | {'Name':<15} | {'Price':<7} | {'Available':<9} | {'Status'}")
            print("-" * 65)
            categories = store.get_categories()
            for cat in categories:
                prods = store.get_all_products(get_current_date(), cat)
                if not prods: continue
                print(f"\n[{cat}]")
                for p in prods:
                    effective_qty = logic.get_available_quantity_after_cart(p, cart)
                    status = "In Stock" if effective_qty > 0 else "Out of Stock"
                    print(f"{p.product_id:<6} | {p.name:<15} | Rs {p.price:<4} | {effective_qty:<9} | {status}")
                    
        elif choice == "2":
            pid = input("\nEnter Product ID to select: ").strip().upper()
            p = store.get_product(pid)
            if not p:
                display_error("Product not found.")
            else:
                active_selected_product_id = p.product_id
                effective_qty = logic.get_available_quantity_after_cart(p, cart)
                print(f"\nSelected: {p.name} ({p.product_id})")
                print(f"Price: Rs {p.price}")
                print(f"Category: {p.category}")
                print(f"Available Quantity: {effective_qty}")
                if effective_qty <= p.warning_threshold and effective_qty > 0:
                    print(f"Only {effective_qty} left!")
                if effective_qty <= 0:
                    print("Currently Out of Stock.")
                    
        elif choice == "3":
            if not active_selected_product_id:
                display_error("Please select a product first (Option 2).")
                continue
            
            p = store.get_product(active_selected_product_id)
            if not p:
                display_error("Previously selected product no longer exists.")
                active_selected_product_id = None
                continue
                
            print(f"\nAdding {p.name} to cart...")
            try:
                qty = int(input("Enter quantity to add: ").strip())
            except ValueError:
                display_error("Quantity must be a number.")
                continue
                
            success, msg, cart = logic.add_to_cart(cart, p, qty)
            if success:
                print(msg)
                active_selected_product_id = None # Clear selection after adding
            else:
                display_error(msg)
                
        elif choice == "4":
            if not cart:
                print("\nYour cart is empty.")
            else:
                display_cart(cart)
                
        elif choice == "5":
            if not cart:
                display_error("Your cart is empty.")
                continue
            display_cart(cart)
            pid = input("\nEnter Product ID to edit: ").strip().upper()
            if pid not in cart:
                display_error("Product not in cart.")
            else:
                p = store.get_product(pid)
                if p:
                    try:
                        qty = int(input("Enter new quantity (0 to remove): ").strip())
                    except ValueError:
                        display_error("Quantity must be a number.")
                        continue
                        
                    success, msg, cart = logic.edit_cart_item(cart, p, qty)
                    if success:
                        print(msg)
                    else:
                        display_error(msg)
                        
        elif choice == "6":
            print("\n1. Apply Coupon")
            print("2. Remove Coupon")
            sub = input("Select option: ").strip()
            if sub == "1":
                code = input("Enter coupon code: ").strip().upper()
                cpn = store.get_coupon(code)
                if not cpn:
                    display_error("Invalid coupon code.")
                else:
                    customer = store.get_or_create_customer(phone, customer.name)
                    valid, discount, msg = logic.validate_and_apply_coupon(logic.get_cart_total(cart), cpn, customer)
                    if valid:
                        active_coupon_code = code
                        print(f"Coupon {code} applied. Discount: Rs {discount}")
                    else:
                        display_error(msg)
            elif sub == "2":
                active_coupon_code = None
                print("Coupon removed.")
            else:
                display_error("Invalid choice.")
                
        elif choice == "7":
            customer = store.get_or_create_customer(phone, customer.name)
            print(f"\nYour current Loyalty Points: {customer.loyalty_points}")
            print("You can redeem points during checkout (1 point = Rs 1).")
            print("Note: Coupons and loyalty points cannot be used together.")
            
        elif choice == "8":
            if not cart:
                display_error("Your cart is empty.")
                continue
                
            display_cart(cart)
            customer = store.get_or_create_customer(phone, customer.name)
            print(f"Available Loyalty Points: {customer.loyalty_points}")
            
            if active_coupon_code:
                print(f"Active Coupon applied: {active_coupon_code}")
                
            points_to_redeem = 0
            redeem = input("Do you want to redeem loyalty points? (Y/N): ").strip().upper()
            if redeem == 'Y':
                try:
                    points_to_redeem = int(input(f"Enter points to redeem (max {customer.loyalty_points}): ").strip())
                except ValueError:
                    display_error("Points must be a number.")
                    continue
                    
            try:
                cash_tendered = int(input("Enter cash tendered: Rs ").strip())
            except ValueError:
                display_error("Cash must be a number.")
                continue
                
            # Final pre-check is handled inside calculate_checkout in pure logic, then executed in store.
            res = store.checkout(customer, cart, logic.CheckoutRequest(points_to_redeem, cash_tendered, active_coupon_code), get_current_date())
            
            if res.success:
                print("\nPayment successful! Your order has been placed.")
                print(f"Order ID: {res.order.order_id}")
                cart.clear()
                active_coupon_code = None
                active_selected_product_id = None
            else:
                display_error(res.error_msg)
                
        elif choice == "9":
            oid = input("\nEnter Order ID to view receipt: ").strip().upper()
            orders = store.get_orders_for_customer(phone)
            selected = next((o for o in orders if o.order_id == oid), None)
            if not selected:
                display_error("Order not found or does not belong to you.")
            else:
                print("\n--- Receipt ---")
                print(f"Order ID: {selected.order_id}")
                print(f"Date: {selected.timestamp}")
                print(f"Customer: {customer.name} ({customer.phone})")
                print("-" * 30)
                subtotal = 0
                for item in selected.items:
                    p = store.get_product(item.product_id)
                    p_name = p.name if p else "Unknown"
                    line_sub = logic.get_line_subtotal(item.qty, item.unit_price)
                    subtotal += line_sub
                    print(f"{item.product_id} | {p_name} | {item.qty} x Rs {item.unit_price} = Rs {line_sub}")
                    for alloc in item.allocations:
                        print(f"  -> Supplied from Batch {alloc.batch_id} (Expiry: {alloc.expiry_date}) Qty: {alloc.qty}")
                print("-" * 30)
                print(f"Subtotal: Rs {subtotal}")
                if selected.coupon_discount > 0:
                    print(f"Coupon Discount ({selected.coupon_code}): -Rs {selected.coupon_discount}")
                if selected.loyalty_redeemed > 0:
                    print(f"Loyalty Redeemed: -Rs {selected.loyalty_redeemed}")
                print(f"Final Total: Rs {selected.final_total}")
                print(f"Amount Paid: Rs {selected.amount_paid}")
                print(f"Change: Rs {selected.change}")
                print("-" * 30)
                
        elif choice == "10":
            orders = store.get_orders_for_customer(phone)
            if not orders:
                print("\nYou have no previous orders.")
            else:
                print("\n--- Your Order History ---")
                for o in orders:
                    print(f"{o.timestamp} - {o.order_id} - Rs {o.final_total}")
                    
        elif choice == "11":
            customer = store.get_or_create_customer(phone, customer.name)
            orders = store.get_orders_for_customer(phone)
            returns = store.get_returns_for_customer(phone)
            
            report = logic.calculate_customer_report(customer, orders, returns)
            
            print("\n--- Customer Report ---")
            for k, v in report.items():
                print(f"{k}: {v}")
                
        elif choice == "12":
            break
        else:
            display_error("Invalid choice.")
            
        store.save_data("data.csv")

def owner_flow():
    if not store.is_owner_set():
        print("\n--- First-time Owner Setup ---")
        name = input("Enter Owner Name: ").strip()
        pwd = input("Create Owner Password: ").strip()
        confirm = input("Confirm Owner Password: ").strip()
        
        if not pwd or pwd != confirm:
            display_error("Passwords cannot be empty and must match.")
            return
            
        store.set_owner_password(name, pwd)
        store.save_data("data.csv")
        print("\nOwner setup complete. Please log in.")
        return
        
    print("\n--- Owner Login ---")
    pwd = input("Enter Owner Password: ").strip()
    
    if not store.check_owner_password(pwd):
        display_error("Incorrect password.")
        return
        
    print(f"\nWelcome, {store.get_owner_name()}!")
    
    while True:
        print("\n--- Owner Menu ---")
        print("1. Add Stock")
        print("2. Remove Stock")
        print("3. View Inventory")
        print("4. View Sales")
        print("5. View Reports")
        print("6. Manage Coupons")
        print("7. View Restock Alerts")
        print("8. Logout")
        
        choice = input("Select an option: ").strip()
        
        if choice == "1":
            print("\n1. Restock an Existing Product")
            print("2. Add a New Product")
            print("3. Return to Owner Menu")
            sub = input("Select option: ").strip()
            
            if sub == "1":
                pid = input("\nEnter Product ID to restock: ").strip().upper()
                if not store.product_exists(pid):
                    display_error("Product not found.")
                else:
                    p = store.get_product(pid)
                    print(f"\nSelected: {p.name} ({p.product_id})")
                    try:
                        qty = int(input("Quantity to add: ").strip())
                        cost = int(input("Unit Cost: Rs ").strip())
                    except ValueError:
                        display_error("Quantity and cost must be numbers.")
                        continue
                        
                    exp = input("Expiry Date (YYYY-MM-DD): ").strip()
                    
                    valid, msg = logic.validate_restock_input(qty, cost, exp)
                    if not valid:
                        display_error(msg)
                    else:
                        success, msg = store.add_stock(pid, qty, cost, exp, get_current_date())
                        if success:
                            print(msg)
                            updated_p = store.get_product(pid)
                            print(f"Updated sellable quantity: {updated_p.sellable_qty}")
                        else:
                            display_error(msg)
                            
            elif sub == "2":
                pid = input("\nEnter New Product ID: ").strip().upper()
                if store.product_exists(pid):
                    display_error("Product ID already exists. Please use a different Product ID.")
                else:
                    name = input("Product Name: ").strip()
                    print("Categories:\n1. Cold Beverages\n2. Hot Beverages\n3. Snacks")
                    cat_choice = input("Select Category (1-3): ").strip()
                    cat = "Cold Beverages" if cat_choice == "1" else "Hot Beverages" if cat_choice == "2" else "Snacks" if cat_choice == "3" else None
                    
                    try:
                        price = int(input("Selling Price: Rs ").strip())
                        qty = int(input("Initial Stock Quantity: ").strip())
                        cost = int(input("Unit Cost: Rs ").strip())
                    except ValueError:
                        display_error("Price, quantity, and cost must be numbers.")
                        continue
                        
                    exp = input("Expiry Date (YYYY-MM-DD): ").strip()
                    
                    valid, msg = logic.validate_new_product_input(pid, name, cat, price, qty, cost, exp)
                    if not valid:
                        display_error(msg)
                    else:
                        success, msg = store.add_new_product(pid, name, cat, price, qty, cost, exp, get_current_date())
                        if success:
                            print(f"\nSuccess! Created new product {name} ({pid}).")
                        else:
                            display_error(msg)
                            
        elif choice == "2":
            print("\n--- Remove Stock ---")
            pid = input("Product ID: ").strip().upper()
            if not store.product_exists(pid):
                display_error("Product not found.")
            else:
                try:
                    qty = int(input("Quantity to remove: ").strip())
                except ValueError:
                    display_error("Quantity must be a number.")
                    continue
                    
                print("Reason (1: Damaged, 2: Expired, 3: Package Damage, 4: Other)")
                r = input("Select reason: ").strip()
                reason = "Damaged" if r=="1" else "Expired" if r=="2" else "Package Damage" if r=="3" else "Other"
                
                desc = None
                exp = None
                if reason in ["Damaged", "Package Damage"]:
                    desc = input("Description: ").strip()
                elif reason == "Expired":
                    exp = input("Expiry Date: ").strip()
                    
                valid, msg = logic.validate_removal_input(qty, reason, exp, desc)
                if not valid:
                    display_error(msg)
                else:
                    success, msg = store.remove_stock(pid, qty, reason, exp, desc, get_current_date())
                    if success:
                        print(msg)
                    else:
                        display_error(msg)
                        
        elif choice == "3":
            print("\n--- Inventory ---")
            cats = store.get_categories()
            for cat in cats:
                prods = store.get_all_products(get_current_date(), cat)
                if not prods: continue
                print(f"\n[{cat}]")
                for p in prods:
                    status = "In Stock" if p.sellable_qty > 0 else "Out of Stock"
                    print(f"\n{p.product_id} | {p.name} | Rs {p.price} | Total Sellable: {p.sellable_qty} | {status}")
                    if p.stock_batches:
                        print("  Batches:")
                        for b in sorted(p.stock_batches.values(), key=lambda x: x.added_at):
                            b_status = logic.get_batch_status_label(b, get_current_date())
                            print(f"    - {b.batch_id} | Qty: {b.qty} | Expiry: {b.expiry_date} | [{b_status}]")
                    else:
                        print("  No batches.")
                        
        elif choice == "4":
            print("\n--- Sales ---")
            for o in store.get_all_orders():
                print(f"{o.timestamp} - {o.order_id} - Rs {o.final_total}")
                
        elif choice == "5":
            print("\n--- Financial Reports ---")
            report = store.profit_loss_report()
            for k, v in report.items():
                print(f"{k}: Rs {v}")
                
        elif choice == "6":
            while True:
                print("\n--- Manage Coupons ---")
                print("1. View Coupons")
                print("2. Create Coupon")
                print("3. Update Coupon")
                print("4. Enable/Disable Coupon")
                print("5. Delete Coupon")
                print("6. Return to Owner Menu")
                
                c_choice = input("Select option: ").strip()
                if c_choice == "1":
                    for c in store.get_all_coupons():
                        status = "Enabled" if c.enabled else "Disabled"
                        print(f"{c.code} - {c.percent_off}% off (Min: Rs {c.min_order}) [{status}] (Used: {len(c.used_by)}/{c.usage_limit_per_customer})")
                elif c_choice == "2":
                    code = input("Code: ").strip().upper()
                    try:
                        pct = int(input("Discount Percentage: ").strip())
                        mo = int(input("Min Order Rs: ").strip())
                        ul = int(input("Usage Limit per Customer: ").strip())
                    except ValueError:
                        display_error("Must be numbers.")
                        continue
                    first_time = input("First time customers only? (Y/N): ").strip().upper() == 'Y'
                    valid, msg = logic.validate_coupon_management_input(code, pct, mo, ul)
                    if not valid:
                        display_error(msg)
                    else:
                        success, msg = store.create_coupon(code, pct, mo, first_time, ul)
                        if success: print(msg)
                        else: display_error(msg)
                elif c_choice == "3":
                    code = input("Code to update: ").strip().upper()
                    try:
                        pct = int(input("New Discount Percentage: ").strip())
                        mo = int(input("New Min Order Rs: ").strip())
                        ul = int(input("New Usage Limit per Customer: ").strip())
                    except ValueError:
                        display_error("Must be numbers.")
                        continue
                    first_time = input("First time customers only? (Y/N): ").strip().upper() == 'Y'
                    valid, msg = logic.validate_coupon_management_input(code, pct, mo, ul)
                    if not valid:
                        display_error(msg)
                    else:
                        success, msg = store.update_coupon(code, pct, mo, first_time, ul)
                        if success: print(msg)
                        else: display_error(msg)
                elif c_choice == "4":
                    code = input("Code to toggle: ").strip().upper()
                    success, msg = store.toggle_coupon(code)
                    if success: print(msg)
                    else: display_error(msg)
                elif c_choice == "5":
                    code = input("Code to delete: ").strip().upper()
                    success, msg = store.delete_coupon(code)
                    if success: print(msg)
                    else: display_error(msg)
                elif c_choice == "6":
                    break
                else:
                    display_error("Invalid option.")
                    
        elif choice == "7":
            print("\n--- Restock Alerts ---")
            alerts = store.get_restock_alerts()
            if not alerts:
                print("Inventory is sufficient.")
            else:
                for p in alerts:
                    print(f"{p.product_id} - {p.name} (Only {p.sellable_qty} left)")
                    
        elif choice == "8":
            break
        else:
            display_error("Invalid choice.")
            
        store.save_data("data.csv")

def main():
    store.load_data("data.csv")
    
    while True:
        print("\nSMART VENDING MACHINE")
        print("1. Continue as Customer")
        print("2. Continue as Owner")
        print("3. Exit")
        
        choice = input("Select an option: ").strip()
        
        if choice == "1":
            customer_flow()
        elif choice == "2":
            owner_flow()
        elif choice == "3":
            store.save_data("data.csv")
            print("Goodbye!")
            break
        else:
            display_error("Invalid choice.")
        
        store.save_data("data.csv")

if __name__ == "__main__":
    main()
