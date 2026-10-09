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

def display_catalog(cart: Optional[Dict[str, logic.CartItem]] = None):
    cart = cart or {}
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
    print(f"Loyalty Points: {customer.loyalty_points}")
    
    cart: Dict[str, logic.CartItem] = {}
    
    while True:
        print("\n--- Customer Menu ---")
        print("1. View Products & Add to Cart")
        print("2. View/Edit Cart")
        print("3. Checkout")
        print("4. Return Purchased Item")
        print("5. Back to Main Menu")
        
        choice = input("Select an option: ").strip()
        
        if choice == "1":
            while True:
                display_catalog(cart)
                pid = input("\nEnter Product ID to add (or press Enter to go back): ").strip().upper()
                if not pid:
                    break
                    
                p = store.get_product(pid)
                if not p:
                    display_error("Product not found.")
                else:
                    print(f"\nSelected: {p.name} ({p.product_id}) - Rs {p.price}")
                    effective_qty = logic.get_available_quantity_after_cart(p, cart)
                    print(f"Available Quantity: {effective_qty}")
                    if effective_qty <= p.warning_threshold and effective_qty > 0:
                        print(f"Only {effective_qty} left!")
                        
                    try:
                        qty = int(input("Enter desired quantity: ").strip())
                    except ValueError:
                        display_error("Quantity must be a number.")
                        if not ask_continue("Do you want to add another product?"): break
                        continue
                        
                    success, msg, cart = logic.add_to_cart(cart, p, qty)
                    if success:
                        print(msg)
                    else:
                        display_error(msg)
                        
                if not ask_continue("\nDo you want to view products again?"):
                    break
                    
        elif choice == "2":
            while True:
                if not cart:
                    print("\nYour cart is empty.")
                    break
                display_cart(cart)
                pid = input("\nEnter Product ID to edit (or press Enter to go back): ").strip().upper()
                if not pid:
                    break
                    
                if pid not in cart:
                    display_error("Product not in cart.")
                else:
                    p = store.get_product(pid)
                    if p:
                        try:
                            qty = int(input("Enter new quantity (0 to remove): ").strip())
                        except ValueError:
                            display_error("Quantity must be a number.")
                            if not ask_continue("Do you want to edit another item?"): break
                            continue
                            
                        success, msg, cart = logic.edit_cart_item(cart, p, qty)
                        if success:
                            print(msg)
                        else:
                            display_error(msg)
                
                if not cart: break
                if not ask_continue("\nDo you want to edit another item?"):
                    break
                    
        elif choice == "3":
            if not cart:
                display_error("Your cart is empty.")
                continue
                
            while True:
                display_cart(cart)
                print(f"Available Loyalty Points: {customer.loyalty_points}")
                
                coupon_code = None
                points_to_redeem = 0
                
                has_coupon = input("\nDo you have a coupon code? (Y/N): ").strip().upper()
                if has_coupon == 'Y':
                    coupon_code = input("Enter coupon code: ").strip().upper()
                    
                redeem = input("Do you want to redeem loyalty points? (Y/N): ").strip().upper()
                if redeem == 'Y':
                    try:
                        points_to_redeem = int(input(f"Enter points to redeem (max {customer.loyalty_points}): ").strip())
                    except ValueError:
                        display_error("Points must be a number.")
                        if not ask_continue("Do you want to restart checkout?"): break
                        continue
                        
                # Re-fetch customer to get latest state before checkout calculation
                customer = store.get_or_create_customer(phone, customer.name)
                
                try:
                    cash_tendered = int(input("Enter cash tendered: Rs ").strip())
                except ValueError:
                    display_error("Cash must be a number.")
                    if not ask_continue("Do you want to restart checkout?"): break
                    continue
                    
                req = logic.CheckoutRequest(points_to_redeem, cash_tendered, coupon_code)
                res = store.checkout(customer, cart, req, get_current_date())
                
                if res.success:
                    print("\n--- Receipt ---")
                    print(f"Order ID: {res.order.order_id}")
                    print(f"Date: {res.order.timestamp}")
                    print(f"Customer: {customer.name} ({customer.phone})")
                    print("-" * 30)
                    for item in res.order.items:
                        p_name = store.get_product(item.product_id).name
                        sub = logic.get_line_subtotal(item.qty, item.unit_price)
                        print(f"{item.product_id} | {p_name} | {item.qty} x Rs {item.unit_price} = Rs {sub}")
                        for alloc in item.allocations:
                            print(f"  -> Supplied from Batch {alloc.batch_id} (Expiry: {alloc.expiry_date}) Qty: {alloc.qty}")
                    print("-" * 30)
                    print(f"Subtotal: Rs {logic.get_cart_total(cart)}")
                    if res.order.coupon_discount > 0:
                        print(f"Coupon Discount ({res.order.coupon_code}): -Rs {res.order.coupon_discount}")
                    if res.order.loyalty_redeemed > 0:
                        print(f"Loyalty Redeemed: -Rs {res.order.loyalty_redeemed}")
                    print(f"Final Total: Rs {res.order.final_total}")
                    print(f"Amount Paid: Rs {res.order.amount_paid}")
                    print(f"Change: Rs {res.order.change}")
                    print(f"Loyalty Points Earned: {res.points_earned}")
                    print("-" * 30)
                    print("Thank you for your purchase!")
                    
                    cart.clear()
                    break
                else:
                    display_error(res.error_msg)
                    if not ask_continue("Do you want to try checking out again?"):
                        break
                        
        elif choice == "4":
            while True:
                orders = store.get_orders_for_customer(phone)
                if not orders:
                    print("\nYou have no previous orders.")
                    break
                    
                print("\n--- Your Orders ---")
                for o in orders:
                    print(f"{o.timestamp} - {o.order_id} - Rs {o.final_total}")
                    
                oid = input("\nEnter Order ID to return an item: ").strip().upper()
                selected = next((o for o in orders if o.order_id == oid), None)
                if not selected:
                    display_error("Order not found or does not belong to you.")
                else:
                    print("\nItems in this order:")
                    for item in selected.items:
                        p_name = store.get_product(item.product_id).name
                        print(f"{item.product_id} - {p_name} - Qty: {item.qty}")
                        
                    pid = input("Enter Product ID to return: ").strip().upper()
                    try:
                        qty = int(input("Enter quantity to return: ").strip())
                    except ValueError:
                        display_error("Invalid quantity.")
                        if not ask_continue("Do you want to process another return?"): break
                        continue
                        
                    print("Return Reason (1: Damaged, 2: Expired)")
                    reason_choice = input("Select reason: ").strip()
                    reason = "Damaged" if reason_choice == "1" else "Expired" if reason_choice == "2" else "Other"
                    
                    desc = None
                    exp = None
                    if reason == "Damaged":
                        desc = input("Enter damage description: ").strip()
                    elif reason == "Expired":
                        exp = input("Enter expiry date (YYYY-MM-DD): ").strip()
                        
                    req = logic.ReturnRequest(oid, pid, qty, reason, exp, desc)
                    res = store.process_return(req, get_current_date())
                    
                    if res.success:
                        print(f"\nReturn processed successfully.")
                        print(f"Refund amount: Rs {res.refund_amount}")
                        print(f"Loyalty points awarded for refund: {res.points_awarded}")
                        cust_after = store.get_customer(phone)
                        if cust_after:
                            print(f"Updated loyalty balance: {cust_after.loyalty_points} points")
                    else:
                        display_error(res.error_msg)
                        
                if not ask_continue("\nDo you want to process another return?"):
                    break
                    
        elif choice == "5":
            break
        else:
            display_error("Invalid choice.")
            
        store.save_data("data.csv")

def owner_flow():
    if not store.is_owner_set():
        print("\n--- First-time Owner Setup ---")
        name = input("Enter Owner Name: ").strip()
        print("WARNING: Password will be visible as you type.")
        pwd = input("Create Owner Password: ").strip()
        confirm = input("Confirm Owner Password: ").strip()
        
        if pwd != confirm:
            display_error("Passwords do not match.")
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
        print("1. Add Stock / Add Product")
        print("2. Remove Stock")
        print("3. View Inventory")
        print("4. View Sales")
        print("5. View Profit/Loss Report")
        print("6. Manage Coupons")
        print("7. Restock Alerts")
        print("8. Logout")
        
        choice = input("Select an option: ").strip()
        
        if choice == "1":
            while True:
                print("\n1. Restock an Existing Product")
                print("2. Add a New Product")
                print("3. Return to Owner Menu")
                sub = input("Select option: ").strip()
                
                if sub == "1":
                    display_catalog()
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
                            if not ask_continue("Do you want to add more stock or products?"): break
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
                            if not ask_continue("Do you want to add more stock or products?"): break
                            continue
                            
                        exp = input("Expiry Date (YYYY-MM-DD): ").strip()
                        
                        valid, msg = logic.validate_new_product_input(pid, name, cat, price, qty, cost, exp)
                        if not valid:
                            display_error(msg)
                        else:
                            success, msg = store.add_new_product(pid, name, cat, price, qty, cost, exp, get_current_date())
                            if success:
                                print(f"\nSuccess! Created new product {name} ({pid}) in {cat}.")
                                print(f"Price: Rs {price} | Initial Qty: {qty} | Unit Cost: Rs {cost} | Expiry: {exp}")
                            else:
                                display_error(msg)
                                
                elif sub == "3":
                    break
                else:
                    display_error("Invalid option.")
                    
                if not ask_continue("\nDo you want to add more stock or products?"):
                    break
                    
        elif choice == "2":
            while True:
                print("\n--- Remove Stock ---")
                pid = input("Product ID: ").strip().upper()
                if not store.product_exists(pid):
                    display_error("Product not found.")
                else:
                    try:
                        qty = int(input("Quantity to remove: ").strip())
                    except ValueError:
                        display_error("Quantity must be a number.")
                        if not ask_continue("Do you want to remove more stock?"): break
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
                        
                if not ask_continue("\nDo you want to remove more stock?"):
                    break
                    
        elif choice == "3":
            while True:
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
                            
                if not ask_continue("\nDo you want to view inventory again?"):
                    break
                    
        elif choice == "4":
            print("\n--- Sales ---")
            for o in store.get_all_orders():
                print(f"{o.timestamp} - {o.order_id} - Rs {o.final_total}")
                
        elif choice == "5":
            print("\n--- Reports ---")
            report = store.profit_loss_report()
            for k, v in report.items():
                print(f"{k}: Rs {v}")
                
        elif choice == "6":
            print("\n--- Manage Coupons ---")
            for c in store.get_all_coupons():
                status = "Enabled" if c.enabled else "Disabled"
                print(f"{c.code} - {c.percent_off}% off (Min: Rs {c.min_order}) [{status}]")
                
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
        print("\n--- Smart Vending Machine V2 ---")
        print("1. Customer")
        print("2. Owner")
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
