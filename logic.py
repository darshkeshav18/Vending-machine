from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Tuple
import copy
import hashlib

# --- Data Structures (Pure schemas) ---

@dataclass
class StockBatch:
    batch_id: str
    qty: int
    expiry_date: str
    added_at: str

@dataclass
class Product:
    product_id: str
    name: str
    category: str
    price: int
    cost: int
    restock_threshold: int
    warning_threshold: int
    stock_batches: Dict[str, StockBatch] = field(default_factory=dict)

    @property
    def sellable_qty(self) -> int:
        return sum(b.qty for b in self.stock_batches.values() if b.qty > 0)

@dataclass
class CartItem:
    product_id: str
    qty: int
    unit_price: int = 0

@dataclass
class Customer:
    phone: str
    name: str
    is_first_time: bool
    loyalty_points: int

@dataclass
class Coupon:
    code: str
    percent_off: int
    min_order: int
    first_time_only: bool
    enabled: bool
    usage_limit_per_customer: int
    used_by: List[str] = field(default_factory=list)

@dataclass
class BatchAllocation:
    batch_id: str
    qty: int
    expiry_date: str

@dataclass
class OrderItem:
    product_id: str
    qty: int
    unit_price: int
    allocations: List[BatchAllocation] = field(default_factory=list)

@dataclass
class Order:
    order_id: str
    customer_phone: str
    timestamp: str
    items: List[OrderItem]
    coupon_code: str
    coupon_discount: int
    loyalty_redeemed: int
    amount_paid: int
    change: int
    final_total: int

@dataclass
class StockRemoval:
    removal_id: str
    product_id: str
    qty: int
    reason: str
    expiry_date: Optional[str]
    description: Optional[str]
    timestamp: str

@dataclass
class Return:
    return_id: str
    order_id: str
    product_id: str
    qty: int
    reason: str
    expiry_date: Optional[str]
    description: Optional[str]
    refund_amount: int
    timestamp: str

class OwnerAuth:
    name: str = ""
    password_hash: str = ""
    is_set: bool = False

@dataclass
class CheckoutRequest:
    loyalty_points_to_redeem: int
    cash_tendered: int
    coupon_code: Optional[str] = None

@dataclass
class ReturnRequest:
    order_id: str
    product_id: str
    qty: int
    reason: str
    expiry_date: Optional[str] = None
    description: Optional[str] = None

@dataclass
class CheckoutCalculation:
    success: bool
    error_msg: str
    order: Optional[Order]
    points_earned: int
    allocations_plan: Dict[str, List[BatchAllocation]] # product_id -> allocations

@dataclass
class ReturnCalculation:
    success: bool
    error_msg: str
    refund_amount: int
    points_awarded: int


# --- Pure Functions ---

def get_available_quantity_after_cart(product: Product, cart: Dict[str, CartItem]) -> int:
    cart_qty = cart[product.product_id].qty if product.product_id in cart else 0
    return max(0, product.sellable_qty - cart_qty)

def get_line_subtotal(item_qty: int, unit_price: int) -> int:
    return item_qty * unit_price

def get_returnable_quantity(order_item: OrderItem, existing_returns_for_item: int) -> int:
    return max(0, order_item.qty - existing_returns_for_item)

def get_batch_status_label(batch: StockBatch, current_date: str) -> str:
    if batch.expiry_date < current_date:
        return "EXPIRED"
    elif batch.qty > 0:
        return "SELLABLE"
    return "DEPLETED"

def validate_new_product_input(pid: str, name: str, cat: Optional[str], price: int, qty: int, cost: int, expiry: str) -> Tuple[bool, str]:
    if not pid or not name or not cat or not expiry:
        return False, "All string fields must be non-empty."
    if price < 0 or qty < 0 or cost < 0:
        return False, "Price, quantity, and cost must be zero or positive."
    if len(expiry) != 10 or expiry.count('-') != 2:
        return False, "Expiry date must be in YYYY-MM-DD format."
    return True, "Valid input."

def validate_restock_input(qty: int, cost: int, expiry: str) -> Tuple[bool, str]:
    if qty <= 0:
        return False, "Quantity must be greater than zero."
    if cost < 0:
        return False, "Cost cannot be negative."
    if len(expiry) != 10 or expiry.count('-') != 2:
        return False, "Expiry date must be in YYYY-MM-DD format."
    return True, "Valid input."

def validate_removal_input(qty: int, reason: str, expiry: Optional[str], desc: Optional[str]) -> Tuple[bool, str]:
    if qty <= 0:
        return False, "Quantity must be greater than zero."
    if reason not in ["Damaged", "Expired", "Package Damage", "Other"]:
        return False, "Invalid reason."
    if reason in ["Damaged", "Package Damage"] and not desc:
        return False, "Description is required for damaged stock."
    if reason == "Expired" and not expiry:
        return False, "Expiry date is required for expired stock."
    return True, "Valid input."

def hash_password(password: str, salt: bytes) -> str:
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + pwd_hash.hex()

def verify_password(password: str, hashed_str: str) -> bool:
    try:
        salt_hex, hash_hex = hashed_str.split(':')
        salt = bytes.fromhex(salt_hex)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return pwd_hash.hex() == hash_hex
    except ValueError:
        return password == hashed_str

def check_stock_available(product: Product, requested_qty: int) -> Tuple[bool, int]:
    return requested_qty <= product.sellable_qty, product.sellable_qty

def get_cart_total(cart: Dict[str, CartItem]) -> int:
    return sum(item.qty * item.unit_price for item in cart.values())

def add_to_cart(cart: Dict[str, CartItem], product: Product, qty: int) -> Tuple[bool, str, Dict[str, CartItem]]:
    new_cart = copy.deepcopy(cart)
    if qty <= 0:
        return False, "Quantity must be a positive whole number.", new_cart
    
    current_qty = new_cart[product.product_id].qty if product.product_id in new_cart else 0
    new_qty = current_qty + qty
    
    available, max_qty = check_stock_available(product, new_qty)
    if not available:
        return False, f"Cannot add. Only {max_qty} available.", new_cart
    
    if product.product_id in new_cart:
        new_cart[product.product_id].qty = new_qty
    else:
        new_cart[product.product_id] = CartItem(product_id=product.product_id, qty=qty, unit_price=product.price)
    
    return True, "Added to cart.", new_cart

def edit_cart_item(cart: Dict[str, CartItem], product: Product, new_qty: int) -> Tuple[bool, str, Dict[str, CartItem]]:
    new_cart = copy.deepcopy(cart)
    if new_qty < 0:
        return False, "Quantity cannot be negative.", new_cart
    
    if new_qty == 0:
        if product.product_id in new_cart:
            del new_cart[product.product_id]
        return True, "Item removed from cart.", new_cart
        
    available, max_qty = check_stock_available(product, new_qty)
    if not available:
        return False, f"Cannot edit. Only {max_qty} available.", new_cart
        
    if product.product_id in new_cart:
        new_cart[product.product_id].qty = new_qty
        return True, "Cart updated.", new_cart
    else:
        return False, "Product not in cart.", new_cart

def calculate_coupon_discount(cart_total: int, coupon: Coupon) -> int:
    return int(cart_total * (coupon.percent_off / 100.0))

def validate_and_apply_coupon(cart_total: int, coupon: Coupon, customer: Customer) -> Tuple[bool, int, str]:
    if not coupon.enabled:
        return False, 0, "Coupon is disabled."
    if cart_total < coupon.min_order:
        return False, 0, f"Minimum order amount of Rs {coupon.min_order} required."
    if coupon.first_time_only and not customer.is_first_time:
        return False, 0, "Coupon valid for first-time customers only."
    usage_count = coupon.used_by.count(customer.phone)
    if usage_count >= coupon.usage_limit_per_customer:
        return False, 0, f"Coupon usage limit ({coupon.usage_limit_per_customer}) reached."
        
    discount = calculate_coupon_discount(cart_total, coupon)
    return True, discount, "Coupon applied successfully."

def calculate_loyalty_earned(final_total: int) -> int:
    return final_total // 10

def calculate_loyalty_redemption(points: int) -> int:
    return points * 1

def resolve_loyalty_coupon_combination(coupon_applied: bool, points_requested: int) -> int:
    if coupon_applied and points_requested > 0:
        return 0 # Disallowed
    return points_requested

def allocate_fifo_batches(product: Product, qty_needed: int, current_date: str) -> Tuple[bool, str, List[BatchAllocation]]:
    allocations = []
    # Work on a copy of batches or just read
    remaining = qty_needed
    sorted_batches = sorted(product.stock_batches.values(), key=lambda b: b.added_at)
    
    for batch in sorted_batches:
        if remaining == 0:
            break
        if batch.qty > 0 and batch.expiry_date >= current_date:
            deduct = min(batch.qty, remaining)
            allocations.append(BatchAllocation(batch.batch_id, deduct, batch.expiry_date))
            remaining -= deduct
            
    if remaining > 0:
        return False, f"Insufficient non-expired stock for {product.name}.", []
        
    return True, "Allocated.", allocations

def calculate_checkout(cart: Dict[str, CartItem], products: Dict[str, Product], 
                       coupon: Optional[Coupon], customer: Customer, 
                       points_to_redeem: int, cash_tendered: int, 
                       current_date: str, next_order_id: str) -> CheckoutCalculation:
    if not cart:
        return CheckoutCalculation(False, "Your cart is empty.", None, 0, {})
        
    cart_total = get_cart_total(cart)
    
    coupon_discount = 0
    coupon_code_str = ""
    if coupon:
        valid, discount, msg = validate_and_apply_coupon(cart_total, coupon, customer)
        if valid:
            coupon_discount = discount
            coupon_code_str = coupon.code
        else:
            return CheckoutCalculation(False, msg, None, 0, {})
            
    if coupon_discount > 0 and points_to_redeem > 0:
        return CheckoutCalculation(False, "Cannot combine coupon and loyalty points.", None, 0, {})
        
    if points_to_redeem > customer.loyalty_points:
        return CheckoutCalculation(False, "Insufficient loyalty points.", None, 0, {})
        
    loyalty_value = calculate_loyalty_redemption(points_to_redeem)
    
    final_total = max(0, cart_total - coupon_discount - loyalty_value)
    
    if cash_tendered < final_total:
        return CheckoutCalculation(False, f"Payment is short by Rs {final_total - cash_tendered}.", None, 0, {})
        
    change = cash_tendered - final_total
    
    # Calculate allocations purely
    allocations_plan = {}
    order_items = []
    
    for item in cart.values():
        prod = products.get(item.product_id)
        if not prod:
            return CheckoutCalculation(False, f"Product {item.product_id} not found.", None, 0, {})
            
        success, msg, item_allocations = allocate_fifo_batches(prod, item.qty, current_date)
        if not success:
            return CheckoutCalculation(False, msg, None, 0, {})
            
        allocations_plan[item.product_id] = item_allocations
        order_items.append(OrderItem(product_id=item.product_id, qty=item.qty, unit_price=item.unit_price, allocations=item_allocations))
        
    order = Order(
        order_id=next_order_id,
        customer_phone=customer.phone,
        timestamp=current_date,
        items=order_items,
        coupon_code=coupon_code_str,
        coupon_discount=coupon_discount,
        loyalty_redeemed=points_to_redeem,
        amount_paid=cash_tendered,
        change=change,
        final_total=final_total
    )
    
    points_earned = calculate_loyalty_earned(final_total)
    
    return CheckoutCalculation(True, "Checkout successful.", order, points_earned, allocations_plan)

def calculate_process_return(request: ReturnRequest, order: Optional[Order], 
                             existing_returns_qty: int) -> ReturnCalculation:
    if not order:
        return ReturnCalculation(False, "Order not found.", 0, 0)
        
    order_item = next((item for item in order.items if item.product_id == request.product_id), None)
    if not order_item:
        return ReturnCalculation(False, "Product not in order.", 0, 0)
        
    eligible_qty = get_returnable_quantity(order_item, existing_returns_qty)
    if request.qty > eligible_qty:
        return ReturnCalculation(False, f"Return quantity exceeds eligible quantity ({eligible_qty} remains).", 0, 0)
        
    if request.reason not in ["Damaged", "Expired"]:
        return ReturnCalculation(False, "Invalid return reason.", 0, 0)
        
    if request.reason == "Expired" and not request.expiry_date:
        return ReturnCalculation(False, "Expiry date required for expired return.", 0, 0)
        
    if request.reason == "Damaged" and not request.description:
        return ReturnCalculation(False, "Description required for damaged return.", 0, 0)
        
    refund = get_line_subtotal(request.qty, order_item.unit_price)
    
    # Calculate refund points
    refund_points = refund // 10
    
    return ReturnCalculation(True, "Valid return calculation.", refund, refund_points)

def calculate_profit_loss(orders: List[Order], products: Dict[str, Product], returns: List[Return], removals: List[StockRemoval]) -> Dict[str, int]:
    sales_revenue = sum(o.final_total for o in orders)
    
    product_costs = 0
    for o in orders:
        for item in o.items:
            prod = products.get(item.product_id)
            if prod:
                product_costs += item.qty * prod.cost
                
    refunds = sum(r.refund_amount for r in returns)
    
    stock_losses = 0
    for rem in removals:
        if not rem.reason.startswith("Return"):
            prod = products.get(rem.product_id)
            if prod:
                stock_losses += rem.qty * prod.cost
                
    net_profit = sales_revenue - product_costs - refunds - stock_losses
    
    return {
        "Sales Revenue": sales_revenue,
        "Product Costs": product_costs,
        "Refunds": refunds,
        "Stock Losses": stock_losses,
        "Net Result": net_profit
    }
