from datetime import datetime, date, timedelta
from models import Transaction, TransactionItem, Product, ProductSize, Settings
from database import db
import random
import string


def generate_invoice_number():
    """Generate a unique invoice number: JE-YYYYMMDD-XXXX"""
    today = datetime.now().strftime('%Y%m%d')
    suffix = ''.join(random.choices(string.digits, k=4))
    invoice_number = f'JE-{today}-{suffix}'
    while Transaction.query.filter_by(invoice_number=invoice_number).first():
        suffix = ''.join(random.choices(string.digits, k=4))
        invoice_number = f'JE-{today}-{suffix}'
    return invoice_number


def get_dashboard_stats():
    """Return aggregated stats for the dashboard."""
    settings = Settings.query.first()
    threshold = settings.low_stock_threshold if settings else 5

    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())

    today_transactions = Transaction.query.filter(
        Transaction.date >= today_start,
        Transaction.date <= today_end
    ).all()

    today_sales = sum(t.total for t in today_transactions)
    today_orders = len(today_transactions)
    total_products = Product.query.count()

    # Low stock: any product that has at least one size with stock <= threshold
    low_stock_count = (
        db.session.query(Product.id)
        .join(ProductSize)
        .filter(ProductSize.stock <= threshold)
        .distinct()
        .count()
    )

    recent_transactions = Transaction.query.order_by(
        Transaction.date.desc()
    ).limit(10).all()

    return {
        'today_sales': today_sales,
        'today_orders': today_orders,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'recent_transactions': [t.to_dict() for t in recent_transactions]
    }


def get_sales_report(start_date_str, end_date_str):
    """Return sales data for a date range."""
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
    except (ValueError, TypeError):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

    transactions = Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).order_by(Transaction.date.asc()).all()

    # Daily breakdown
    daily_map = {}
    current = start_date.date()
    while current <= end_date.date():
        daily_map[current.isoformat()] = {'date': current.isoformat(), 'sales': 0, 'orders': 0}
        current += timedelta(days=1)

    for t in transactions:
        key = t.date.date().isoformat()
        if key in daily_map:
            daily_map[key]['sales'] += t.total
            daily_map[key]['orders'] += 1

    daily_data = list(daily_map.values())

    total_revenue = sum(t.total for t in transactions)
    total_orders = len(transactions)
    avg_daily = total_revenue / max(len(daily_data), 1)

    payment_breakdown = {}
    for t in transactions:
        pm = t.payment_method
        payment_breakdown[pm] = payment_breakdown.get(pm, 0) + t.total

    from sqlalchemy import func
    top_products = (
        db.session.query(
            TransactionItem.product_name,
            func.sum(TransactionItem.quantity).label('total_qty'),
            func.sum(TransactionItem.total_price).label('total_revenue')
        )
        .join(Transaction, TransactionItem.transaction_id == Transaction.id)
        .filter(Transaction.date >= start_date, Transaction.date <= end_date)
        .group_by(TransactionItem.product_name)
        .order_by(func.sum(TransactionItem.total_price).desc())
        .limit(5)
        .all()
    )

    return {
        'daily_data': daily_data,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_daily_sales': avg_daily,
        'payment_breakdown': payment_breakdown,
        'top_products': [
            {'name': p.product_name, 'quantity': int(p.total_qty), 'revenue': float(p.total_revenue)}
            for p in top_products
        ],
        'transactions': [t.to_dict() for t in transactions]
    }


def format_currency(amount, symbol='₹'):
    """Format amount as currency string."""
    return f'{symbol}{amount:,.2f}'


def process_sale(data):
    """Process a complete sale transaction."""
    settings = Settings.query.first()
    gst_rate = settings.gst_rate if settings else 18.0

    invoice_number = generate_invoice_number()
    items_data = data.get('items', [])
    discount_percent = float(data.get('discount_percent', 0))
    payment_method = data.get('payment_method', 'Cash')
    customer_name = data.get('customer_name', 'Walk-in Customer')
    customer_phone = data.get('customer_phone', '')

    if not items_data:
        return None, 'No items in transaction'

    subtotal = 0
    transaction_items = []

    for item in items_data:
        product = Product.query.get(item['product_id'])
        if not product:
            return None, f'Product {item["product_id"]} not found'

        size_name = item.get('size', '')
        qty = int(item['quantity'])

        # Find the matching ProductSize record
        product_size_rec = None
        if size_name:
            product_size_rec = ProductSize.query.filter_by(
                product_id=product.id, size=size_name
            ).first()
            if not product_size_rec:
                return None, f'Size "{size_name}" not found for {product.name}'
            if product_size_rec.stock < qty:
                return None, f'Insufficient stock for {product.name} (size {size_name}). Available: {product_size_rec.stock}'
        else:
            # No size — check total stock (e.g. Free Size only product)
            if product.total_stock < qty:
                return None, f'Insufficient stock for {product.name}'

        unit_price = float(item.get('price', product.price))
        total_price = unit_price * qty
        subtotal += total_price

        transaction_items.append({
            'product': product,
            'product_size_rec': product_size_rec,
            'product_name': product.name,
            'product_size': size_name,
            'quantity': qty,
            'unit_price': unit_price,
            'total_price': total_price
        })

    discount_amount = subtotal * (discount_percent / 100)
    after_discount = subtotal - discount_amount
    gst_amount = after_discount * (gst_rate / 100)
    total = after_discount + gst_amount

    transaction = Transaction(
        invoice_number=invoice_number,
        customer_name=customer_name,
        customer_phone=customer_phone,
        payment_method=payment_method,
        subtotal=round(subtotal, 2),
        discount_amount=round(discount_amount, 2),
        gst_amount=round(gst_amount, 2),
        total=round(total, 2)
    )
    db.session.add(transaction)
    db.session.flush()

    for item_data in transaction_items:
        ti = TransactionItem(
            transaction_id=transaction.id,
            product_id=item_data['product'].id,
            product_name=item_data['product_name'],
            product_size=item_data['product_size'],
            quantity=item_data['quantity'],
            unit_price=item_data['unit_price'],
            total_price=item_data['total_price']
        )
        db.session.add(ti)
        # Deduct from the correct size's stock
        if item_data['product_size_rec']:
            item_data['product_size_rec'].stock -= item_data['quantity']

    db.session.commit()
    return transaction, None
