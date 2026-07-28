from flask import Blueprint, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import uuid
from models import Product, ProductSize, Transaction, TransactionItem, Settings, ProductSizeChart
from database import db
from helpers import get_dashboard_stats, get_sales_report, process_sale
from datetime import datetime, timedelta
import os
import json

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
PRODUCT_IMG_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'images', 'products')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_product_image(file):
    """Save uploaded image, return filename or None."""
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        return None
    os.makedirs(PRODUCT_IMG_FOLDER, exist_ok=True)
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(PRODUCT_IMG_FOLDER, filename))
    return filename

def delete_product_image(filename):
    """Delete a product image file from disk."""
    if filename:
        path = os.path.join(PRODUCT_IMG_FOLDER, filename)
        if os.path.exists(path):
            os.remove(path)

def parse_sizes_from_request(data):
    """
    Parse sizes from form or JSON data.
    Expects sizes as JSON string: '[{"size":"S","stock":10},{"size":"M","stock":5}]'
    or as individual form fields: sizes_data=<json>
    Returns list of dicts: [{"size": "S", "stock": 10}, ...]
    """
    raw = data.get('sizes_data', '')
    if not raw:
        return []
    try:
        sizes = json.loads(raw)
        result = []
        for s in sizes:
            size_name = str(s.get('size', '')).strip()
            stock = int(s.get('stock', 0))
            if size_name and stock >= 0:
                result.append({'size': size_name, 'stock': stock})
        return result
    except (json.JSONDecodeError, ValueError, TypeError):
        return []

main = Blueprint('main', __name__)


# ─── PAGE ROUTES ────────────────────────────────────────────────────────────────

@main.route('/')
def dashboard():
    stats = get_dashboard_stats()
    settings = Settings.query.first()
    return render_template('dashboard.html', stats=stats, settings=settings)


@main.route('/billing')
def billing():
    settings = Settings.query.first()
    categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in categories]
    return render_template('billing.html', settings=settings, categories=categories)


@main.route('/products')
def products():
    settings = Settings.query.first()
    categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in categories]
    return render_template('products.html', settings=settings, categories=categories)


@main.route('/inventory')
def inventory():
    settings = Settings.query.first()
    threshold = settings.low_stock_threshold if settings else 5
    products = Product.query.order_by(Product.name.asc()).all()
    return render_template('inventory.html', products=products, settings=settings, threshold=threshold)


@main.route('/sales_report')
def sales_report():
    settings = Settings.query.first()
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    return render_template('sales_report.html', settings=settings,
                           default_start=start_date, default_end=end_date)


@main.route('/settings')
def settings():
    store_settings = Settings.query.first()
    return render_template('settings.html', settings=store_settings)


# ─── API: PRODUCTS ───────────────────────────────────────────────────────────────

@main.route('/api/products', methods=['GET'])
def api_get_products():
    try:
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        query = Product.query
        if category:
            query = query.filter(Product.category == category)
        if search:
            query = query.filter(Product.name.ilike(f'%{search}%'))
        products = query.order_by(Product.name.asc()).all()
        if not products:
            return jsonify([])
        return jsonify([p.to_dict() for p in products])
    except Exception as e:
        print(f"Error fetching products: {e}")
        return jsonify({'error': str(e)}), 500


@main.route('/api/products/<int:product_id>', methods=['GET'])
def api_get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())


@main.route('/api/products', methods=['POST'])
def api_add_product():
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form
        image_file = request.files.get('image')
    else:
        data = request.get_json() or {}
        image_file = None

    if not data.get('name') or not data.get('price'):
        return jsonify({'error': 'Name and price are required'}), 400

    # Handle image upload
    image_filename = ''
    if image_file:
        saved = save_product_image(image_file)
        if saved:
            image_filename = saved
        elif image_file.filename:
            return jsonify({'error': 'Invalid image format. Use jpg, jpeg, png or webp.'}), 400

    product = Product(
        name=data['name'].strip(),
        category=data.get('category', 'General').strip(),
        price=float(data['price']),
        image_filename=image_filename,
        applicable_measurements=data.get('applicable_measurements', '').strip()
    )
    db.session.add(product)
    db.session.flush()  # get product.id

    # Save per-size stock
    sizes = parse_sizes_from_request(data)
    for s in sizes:
        ps = ProductSize(product_id=product.id, size=s['size'], stock=s['stock'])
        db.session.add(ps)

    # Save per-product size chart if provided
    sc_raw = data.get('size_chart_data', '')
    if sc_raw:
        try:
            sc_rows = json.loads(sc_raw) if isinstance(sc_raw, str) else sc_raw
            unit = data.get('unit', 'in')
            save_product_size_charts(product.id, product.applicable_measurements, unit, sc_rows)
        except Exception as e:
            print(f"Error parsing size chart data: {e}")

    db.session.commit()
    return jsonify(product.to_dict()), 201



@main.route('/api/products/<int:product_id>', methods=['PUT'])
def api_update_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form
        image_file = request.files.get('image')
    else:
        data = request.get_json() or {}
        image_file = None

    if 'name' in data:
        product.name = data['name'].strip()
    if 'category' in data:
        product.category = data['category'].strip()
    if 'price' in data:
        product.price = float(data['price'])
    if 'applicable_measurements' in data:
        product.applicable_measurements = data['applicable_measurements'].strip()

    # Replace all sizes if sizes_data is provided
    if 'sizes_data' in data:
        # Delete old sizes
        ProductSize.query.filter_by(product_id=product.id).delete()
        sizes = parse_sizes_from_request(data)
        for s in sizes:
            ps = ProductSize(product_id=product.id, size=s['size'], stock=s['stock'])
            db.session.add(ps)

    # Save size chart data if provided
    if 'size_chart_data' in data:
        sc_raw = data.get('size_chart_data', '')
        try:
            sc_rows = json.loads(sc_raw) if isinstance(sc_raw, str) else sc_raw
            unit = data.get('unit', 'in')
            save_product_size_charts(product.id, product.applicable_measurements, unit, sc_rows)
        except Exception as e:
            print(f"Error parsing size chart data on update: {e}")

    # Handle image replacement
    if image_file and image_file.filename:
        saved = save_product_image(image_file)
        if saved:
            delete_product_image(product.image_filename)
            product.image_filename = saved
        else:
            return jsonify({'error': 'Invalid image format. Use jpg, jpeg, png or webp.'}), 400

    product.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(product.to_dict())



@main.route('/api/products/<int:product_id>', methods=['DELETE'])
def api_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    delete_product_image(product.image_filename)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'})


@main.route('/api/categories', methods=['GET'])
def api_get_categories():
    categories = db.session.query(Product.category).distinct().order_by(Product.category).all()
    return jsonify([c[0] for c in categories])


# ─── API: INVENTORY ───────────────────────────────────────────────────────────────

@main.route('/api/inventory/update', methods=['POST'])
def api_update_stock():
    """Update stock for a specific product size."""
    data = request.get_json()
    product_id = data.get('product_id')
    size_name = data.get('size')
    new_stock = data.get('stock')

    if product_id is None or new_stock is None or not size_name:
        return jsonify({'error': 'product_id, size, and stock are required'}), 400

    ps = ProductSize.query.filter_by(product_id=product_id, size=size_name).first()
    if not ps:
        return jsonify({'error': f'Size "{size_name}" not found for this product'}), 404

    ps.stock = int(new_stock)
    product = Product.query.get(product_id)
    if product:
        product.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Stock updated', 'product': product.to_dict() if product else {}})


# ─── API: BILLING / TRANSACTIONS ─────────────────────────────────────────────────

@main.route('/api/transactions', methods=['POST'])
def api_create_transaction():
    data = request.get_json()
    transaction, error = process_sale(data)
    if error:
        return jsonify({'error': error}), 400
    return jsonify(transaction.to_dict()), 201


@main.route('/api/transactions/<int:transaction_id>', methods=['GET'])
def api_get_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    return jsonify(transaction.to_dict())


@main.route('/api/transactions', methods=['GET'])
def api_get_transactions():
    limit = int(request.args.get('limit', 50))
    transactions = Transaction.query.order_by(Transaction.date.desc()).limit(limit).all()
    return jsonify([t.to_dict() for t in transactions])


# ─── API: REPORTS ─────────────────────────────────────────────────────────────────

@main.route('/api/reports/sales', methods=['GET'])
def api_sales_report():
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    report = get_sales_report(start_date, end_date)
    return jsonify(report)


@main.route('/api/dashboard/stats', methods=['GET'])
def api_dashboard_stats():
    stats = get_dashboard_stats()
    return jsonify(stats)


# ─── API: SETTINGS ───────────────────────────────────────────────────────────────

@main.route('/api/settings', methods=['GET'])
def api_get_settings():
    settings = Settings.query.first()
    if not settings:
        return jsonify({'error': 'Settings not found'}), 404
    return jsonify(settings.to_dict())


@main.route('/api/settings', methods=['PUT'])
def api_update_settings():
    data = request.get_json()
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)

    fields = ['store_name', 'email', 'phone', 'gst_number', 'address',
              'currency_symbol', 'gst_rate', 'low_stock_threshold']
    for field in fields:
        if field in data:
            val = data[field]
            if field in ['gst_rate']:
                val = float(val)
            elif field in ['low_stock_threshold']:
                val = int(val)
            setattr(settings, field, val)

    db.session.commit()
    return jsonify(settings.to_dict())


# ─── API & PAGES: PER-PRODUCT SIZE CHART ───────────────────────────────────────

MEASUREMENT_FIELDS = [
    'bust', 'across_shoulder', 'sleeve_length', 'armhole', 'neck_width',
    'waist', 'hips', 'inseam_length', 'outseam_length', 'thigh_width',
    'knee_width', 'bottom_width', 'front_length', 'back_length',
    'dress_length', 'kurta_length', 'dupatta_length', 'dupatta_width',
    'rise', 'ankle_width'
]

def save_product_size_charts(product_id, applicable_measurements_str, unit, rows_data):
    """Save or update ProductSizeChart rows for a given product."""
    product = Product.query.get(product_id)
    if not product:
        return
    product.applicable_measurements = applicable_measurements_str or ''
    
    # Delete old size charts for this product
    ProductSizeChart.query.filter_by(product_id=product_id).delete()
    
    unit = unit or 'in'

    for row in rows_data:
        size_name = str(row.get('size', '')).strip()
        if not size_name:
            continue
        sc = ProductSizeChart(product_id=product_id, size=size_name, unit='in')
        for f in MEASUREMENT_FIELDS:
            if f in row and row[f] is not None and str(row[f]).strip() != '':
                try:
                    val = float(row[f])
                    # If payload sent in cm, convert to inches for standard DB storage
                    if unit == 'cm':
                        val = round(val / 2.54, 2)
                    else:
                        val = round(val, 2)
                    setattr(sc, f, val)
                except (ValueError, TypeError):
                    setattr(sc, f, None)
        db.session.add(sc)


@main.route('/product/<int:product_id>/size-chart')
def product_size_chart_page(product_id):
    product = Product.query.get_or_404(product_id)
    settings = Settings.query.first()
    return render_template('product_size_chart.html', product=product, settings=settings)


@main.route('/api/product/<int:product_id>/size-chart', methods=['GET'])
def api_get_product_size_chart(product_id):
    product = Product.query.get_or_404(product_id)
    charts = ProductSizeChart.query.filter_by(product_id=product_id).order_by(ProductSizeChart.id.asc()).all()
    return jsonify({
        'product': product.to_dict(),
        'applicable_measurements': product.applicable_measurements or '',
        'size_charts': [c.to_dict() for c in charts]
    })


@main.route('/api/product/<int:product_id>/size-chart/modal', methods=['GET'])
@main.route('/product/<int:product_id>/size-chart/modal', methods=['GET'])
def api_get_product_size_chart_modal(product_id):
    product = Product.query.get_or_404(product_id)
    charts = ProductSizeChart.query.filter_by(product_id=product_id).order_by(ProductSizeChart.id.asc()).all()
    return jsonify({
        'product_id': product.id,
        'product_name': product.name,
        'category': product.category,
        'applicable_measurements': product.applicable_measurements or '',
        'size_charts': [c.to_dict() for c in charts]
    })


@main.route('/api/product/<int:product_id>/size-chart/update', methods=['POST'])
@main.route('/product/<int:product_id>/size-chart/update', methods=['POST'])
def api_update_product_size_chart(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json() or {}
    applicable_measurements = data.get('applicable_measurements', '').strip()
    unit = data.get('unit', 'in')
    rows = data.get('rows', [])

    save_product_size_charts(product.id, applicable_measurements, unit, rows)
    db.session.commit()

    charts = ProductSizeChart.query.filter_by(product_id=product.id).order_by(ProductSizeChart.id.asc()).all()
    return jsonify({
        'message': 'Product size chart updated successfully',
        'product': product.to_dict(),
        'applicable_measurements': product.applicable_measurements,
        'size_charts': [c.to_dict() for c in charts]
    })



# ─── STATIC FILES ─────────────────────────────────────────────────────────────────

@main.route('/static/images/products/<filename>')
def product_image(filename):
    return send_from_directory(PRODUCT_IMG_FOLDER, filename)
