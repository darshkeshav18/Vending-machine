import os
import csv
from typing import Dict, List, Optional, Tuple
import logic

# --- Global State (Dictionaries) ---

PRODUCTS: Dict[str, logic.Product] = {}
CUSTOMERS: Dict[str, logic.Customer] = {}
COUPONS: Dict[str, logic.Coupon] = {}
ORDERS: Dict[str, logic.Order] = {}
STOCK_REMOVALS: Dict[str, logic.StockRemoval] = {}
RETURNS: Dict[str, logic.Return] = {}
OWNER_AUTH = logic.OwnerAuth()

def _init_defaults():
    global PRODUCTS, COUPONS
    PRODUCTS.clear()
    
    PRODUCTS["P001"] = logic.Product("P001", "Cold Coffee", "Cold Beverages", 60, 30, 2, 2)
    PRODUCTS["P002"] = logic.Product("P002", "Lemon Soda", "Cold Beverages", 40, 20, 3, 2)
    PRODUCTS["P003"] = logic.Product("P003", "Tea", "Hot Beverages", 30, 15, 2, 2)
    PRODUCTS["P004"] = logic.Product("P004", "Coffee", "Hot Beverages", 40, 20, 2, 2)
    PRODUCTS["P005"] = logic.Product("P005", "Chips", "Snacks", 40, 20, 2, 2)
    PRODUCTS["P006"] = logic.Product("P006", "Biscuits", "Snacks", 30, 15, 2, 2)
    PRODUCTS["P007"] = logic.Product("P007", "Lays", "Snacks", 20, 10, 2, 2)
    PRODUCTS["P008"] = logic.Product("P008", "Kurkure", "Snacks", 25, 12, 3, 2)
    
    for pid, p in PRODUCTS.items():
        qty = 6 if pid in ["P001", "P005", "P007"] else 10 if pid in ["P002", "P008"] else 7
        b_id = f"B_{pid}_INIT"
        PRODUCTS[pid].stock_batches[b_id] = logic.StockBatch(b_id, qty, "2099-12-31", "2026-10-09 00:00:00")
        
    COUPONS.clear()
    COUPONS["SAVE20"] = logic.Coupon("SAVE20", 20, 500, False, True, 5, [])
    COUPONS["WELCOME40"] = logic.Coupon("WELCOME40", 40, 100, True, True, 1, [])

def load_data(filepath: str = "data.csv") -> None:
    global PRODUCTS, CUSTOMERS, COUPONS, ORDERS, STOCK_REMOVALS, RETURNS, OWNER_AUTH
    PRODUCTS.clear()
    CUSTOMERS.clear()
    COUPONS.clear()
    ORDERS.clear()
    STOCK_REMOVALS.clear()
    RETURNS.clear()
    OWNER_AUTH.name = ""
    OWNER_AUTH.is_set = False
    OWNER_AUTH.password_hash = ""
    
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        _init_defaults()
        return

    try:
        with open(filepath, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row: continue
                rtype = row[0]
                if rtype == "RecordType":
                    continue
                try:
                    if rtype == "PRODUCT":
                        if row[1] not in PRODUCTS:
                            PRODUCTS[row[1]] = logic.Product(row[1], row[2], row[3], int(row[4]), int(row[5]), int(row[6]), int(row[7]))
                    elif rtype == "BATCH":
                        pid = row[2]
                        if pid in PRODUCTS:
                            PRODUCTS[pid].stock_batches[row[1]] = logic.StockBatch(row[1], int(row[3]), row[4], row[5])
                    elif rtype == "CUSTOMER":
                        if row[1] not in CUSTOMERS:
                            CUSTOMERS[row[1]] = logic.Customer(row[1], row[2], row[3] == 'True', int(row[4]))
                    elif rtype == "COUPON":
                        if row[1] not in COUPONS:
                            used_by = row[7].split('|') if row[7] else []
                            COUPONS[row[1]] = logic.Coupon(row[1], int(row[2]), int(row[3]), row[4] == 'True', row[5] == 'True', int(row[6]), used_by)
                    elif rtype == "ORDER":
                        if row[1] not in ORDERS:
                            ORDERS[row[1]] = logic.Order(row[1], row[2], row[3], [], row[4], int(row[5]), int(row[6]), int(row[7]), int(row[8]), int(row[9]))
                    elif rtype == "ORDER_ITEM":
                        oid = row[1]
                        if oid in ORDERS:
                            allocations = []
                            if len(row) > 5 and row[5]:
                                for part in row[5].split('|'):
                                    parts = part.split(':')
                                    if len(parts) == 3:
                                        allocations.append(logic.BatchAllocation(parts[0], int(parts[1]), parts[2]))
                            ORDERS[oid].items.append(logic.OrderItem(row[2], int(row[3]), int(row[4]), allocations))
                    elif rtype == "REMOVAL":
                        if row[1] not in STOCK_REMOVALS:
                            STOCK_REMOVALS[row[1]] = logic.StockRemoval(row[1], row[2], int(row[3]), row[4], row[5] if row[5] else None, row[6] if row[6] else None, row[7])
                    elif rtype == "RETURN":
                        if row[1] not in RETURNS:
                            RETURNS[row[1]] = logic.Return(row[1], row[2], row[3], int(row[4]), row[5], row[6] if row[6] else None, row[7] if row[7] else None, int(row[8]), row[9])
                    elif rtype == "OWNER_AUTH":
                        if len(row) > 3:
                            OWNER_AUTH.name = row[1]
                            OWNER_AUTH.password_hash = row[2]
                            OWNER_AUTH.is_set = row[3] == 'True'
                        else:
                            OWNER_AUTH.name = "Owner"
                            OWNER_AUTH.password_hash = row[1]
                            OWNER_AUTH.is_set = row[2] == 'True'
                except (IndexError, ValueError):
                    continue
        if not PRODUCTS:
            _init_defaults()
    except Exception:
        if not PRODUCTS:
            _init_defaults()

def save_data(filepath: str = "data.csv") -> None:
    temp_filepath = filepath + ".tmp"
    with open(temp_filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["RecordType", "Col1", "Col2", "Col3", "Col4", "Col5", "Col6", "Col7", "Col8", "Col9"])
        for p in PRODUCTS.values():
            writer.writerow(["PRODUCT", p.product_id, p.name, p.category, p.price, p.cost, p.restock_threshold, p.warning_threshold])
            for b in p.stock_batches.values():
                writer.writerow(["BATCH", b.batch_id, p.product_id, b.qty, b.expiry_date, b.added_at])
        for c in CUSTOMERS.values():
            writer.writerow(["CUSTOMER", c.phone, c.name, str(c.is_first_time), c.loyalty_points])
        for c in COUPONS.values():
            writer.writerow(["COUPON", c.code, c.percent_off, c.min_order, str(c.first_time_only), str(c.enabled), c.usage_limit_per_customer, "|".join(c.used_by)])
        for o in ORDERS.values():
            writer.writerow(["ORDER", o.order_id, o.customer_phone, o.timestamp, o.coupon_code, o.coupon_discount, o.loyalty_redeemed, o.amount_paid, o.change, o.final_total])
            for i in o.items:
                alloc_str = "|".join([f"{a.batch_id}:{a.qty}:{a.expiry_date}" for a in i.allocations])
                writer.writerow(["ORDER_ITEM", o.order_id, i.product_id, i.qty, i.unit_price, alloc_str])
        for r in STOCK_REMOVALS.values():
            writer.writerow(["REMOVAL", r.removal_id, r.product_id, r.qty, r.reason, r.expiry_date or "", r.description or "", r.timestamp])
        for r in RETURNS.values():
            writer.writerow(["RETURN", r.return_id, r.order_id, r.product_id, r.qty, r.reason, r.expiry_date or "", r.description or "", r.refund_amount, r.timestamp])
        writer.writerow(["OWNER_AUTH", OWNER_AUTH.name, OWNER_AUTH.password_hash, str(OWNER_AUTH.is_set)])
    os.replace(temp_filepath, filepath)

def get_or_create_customer(phone: str, name: str) -> logic.Customer:
    if phone in CUSTOMERS:
        return CUSTOMERS[phone]
    customer = logic.Customer(phone=phone, name=name, is_first_time=True, loyalty_points=0)
    CUSTOMERS[phone] = customer
    return customer

def expire_batches(current_date: str) -> None:
    for p in PRODUCTS.values():
        for b in list(p.stock_batches.values()):
            if b.qty > 0 and b.expiry_date < current_date:
                rem_id = f"REM{len(STOCK_REMOVALS) + 1000}"
                rem = logic.StockRemoval(
                    removal_id=rem_id,
                    product_id=p.product_id,
                    qty=b.qty,
                    reason="Expired",
                    expiry_date=b.expiry_date,
                    description=None,
                    timestamp=current_date
                )
                STOCK_REMOVALS[rem_id] = rem
                b.qty = 0

def get_all_products(current_date: str, category: Optional[str] = None) -> List[logic.Product]:
    expire_batches(current_date)
    if category:
        return [p for p in PRODUCTS.values() if p.category.lower() == category.lower()]
    return list(PRODUCTS.values())

def get_categories() -> List[str]:
    cats = ["Cold Beverages", "Hot Beverages", "Snacks"]
    existing_cats = set(p.category for p in PRODUCTS.values())
    for c in existing_cats:
        if c not in cats:
            cats.append(c)
    return cats

def add_stock(product_id: str, qty: int, cost: int, expiry_date: str, added_at: str) -> Tuple[bool, str]:
    if product_id not in PRODUCTS:
        return False, "Product not found."
        
    p = PRODUCTS[product_id]
    b_id = f"B_{product_id}_{len(p.stock_batches)+1}"
    batch = logic.StockBatch(
        batch_id=b_id,
        qty=qty,
        expiry_date=expiry_date,
        added_at=added_at
    )
    p.stock_batches[b_id] = batch
    return True, "Stock added successfully."

def remove_stock(product_id: str, qty: int, reason: str, expiry_date: Optional[str], description: Optional[str], timestamp: str) -> Tuple[bool, str]:
    if product_id not in PRODUCTS:
        return False, "Product not found."
        
    prod = PRODUCTS[product_id]
    if prod.sellable_qty < qty:
        return False, f"Cannot remove {qty}; only {prod.sellable_qty} in stock."
        
    qty_needed = qty
    sorted_batches = sorted(prod.stock_batches.values(), key=lambda b: b.added_at)
    for batch in sorted_batches:
        if qty_needed == 0:
            break
        if batch.qty > 0:
            deduct = min(batch.qty, qty_needed)
            batch.qty -= deduct
            qty_needed -= deduct
            
    rem_id = f"REM{len(STOCK_REMOVALS) + 1000}"
    rem = logic.StockRemoval(
        removal_id=rem_id,
        product_id=product_id,
        qty=qty,
        reason=reason,
        expiry_date=expiry_date,
        description=description,
        timestamp=timestamp
    )
    STOCK_REMOVALS[rem_id] = rem
    return True, "Stock removed successfully."

def checkout(customer: logic.Customer, cart: Dict[str, logic.CartItem], request: logic.CheckoutRequest, current_date: str) -> logic.CheckoutCalculation:
    expire_batches(current_date)
    
    coupon = COUPONS.get(request.coupon_code) if request.coupon_code else None
    next_order_id = f"ORD{len(ORDERS) + 1000}"
    
    calc = logic.calculate_checkout(cart, PRODUCTS, coupon, customer, 
                                    request.loyalty_points_to_redeem, request.cash_tendered, 
                                    current_date, next_order_id)
                                    
    if calc.success and calc.order:
        for item_pid, allocations in calc.allocations_plan.items():
            prod = PRODUCTS[item_pid]
            for alloc in allocations:
                prod.stock_batches[alloc.batch_id].qty -= alloc.qty
                
        customer.loyalty_points -= request.loyalty_points_to_redeem
        customer.loyalty_points += calc.points_earned
        if customer.is_first_time:
            customer.is_first_time = False
            
        if calc.order.coupon_code and calc.order.coupon_code in COUPONS:
            COUPONS[calc.order.coupon_code].used_by.append(customer.phone)
            
        ORDERS[calc.order.order_id] = calc.order
        
    return calc

def process_return(request: logic.ReturnRequest, timestamp: str) -> logic.ReturnCalculation:
    order = ORDERS.get(request.order_id)
    existing_returns_qty = sum(r.qty for r in RETURNS.values() if r.order_id == request.order_id and r.product_id == request.product_id)
    
    calc = logic.calculate_process_return(request, order, existing_returns_qty)
    
    if calc.success:
        ret_id = f"RET{len(RETURNS) + 1000}"
        ret = logic.Return(
            return_id=ret_id,
            order_id=request.order_id,
            product_id=request.product_id,
            qty=request.qty,
            reason=request.reason,
            expiry_date=request.expiry_date,
            description=request.description,
            refund_amount=calc.refund_amount,
            timestamp=timestamp
        )
        RETURNS[ret_id] = ret
        
        rem_id = f"REM_RET_{ret_id}"
        rem = logic.StockRemoval(
            removal_id=rem_id,
            product_id=request.product_id,
            qty=request.qty,
            reason=f"Return - {request.reason}",
            expiry_date=request.expiry_date,
            description=request.description,
            timestamp=timestamp
        )
        STOCK_REMOVALS[rem_id] = rem
        
        if order.customer_phone in CUSTOMERS:
            CUSTOMERS[order.customer_phone].loyalty_points += calc.points_awarded
            
    return calc

def get_orders_for_customer(phone: str) -> List[logic.Order]:
    return [o for o in ORDERS.values() if o.customer_phone == phone]

def get_restock_alerts() -> List[logic.Product]:
    return [p for p in PRODUCTS.values() if p.sellable_qty <= p.restock_threshold]

def profit_loss_report() -> Dict[str, int]:
    return logic.calculate_profit_loss(list(ORDERS.values()), PRODUCTS, list(RETURNS.values()), list(STOCK_REMOVALS.values()))

def get_product(pid: str) -> Optional[logic.Product]:
    return PRODUCTS.get(pid)

def product_exists(pid: str) -> bool:
    return pid in PRODUCTS

def get_coupon(code: str) -> Optional[logic.Coupon]:
    return COUPONS.get(code)

def get_customer(phone: str) -> Optional[logic.Customer]:
    return CUSTOMERS.get(phone)

def get_all_orders() -> List[logic.Order]:
    return list(ORDERS.values())

def get_all_coupons() -> List[logic.Coupon]:
    return list(COUPONS.values())

def is_owner_set() -> bool:
    return OWNER_AUTH.is_set

def get_owner_name() -> str:
    return OWNER_AUTH.name

def set_owner_password(name: str, password: str) -> None:
    salt = os.urandom(16)
    hashed = logic.hash_password(password, salt)
    OWNER_AUTH.name = name
    OWNER_AUTH.password_hash = hashed
    OWNER_AUTH.is_set = True

def check_owner_password(password: str) -> bool:
    if not OWNER_AUTH.is_set:
        return False
    return logic.verify_password(password, OWNER_AUTH.password_hash)

def add_new_product(pid: str, name: str, cat: str, price: int, qty: int, cost: int, expiry: str, added_at: str) -> Tuple[bool, str]:
    if pid in PRODUCTS:
        return False, "Product ID already exists."
    PRODUCTS[pid] = logic.Product(pid, name, cat, price, cost, 2, 2)
    return add_stock(pid, qty, cost, expiry, added_at)
