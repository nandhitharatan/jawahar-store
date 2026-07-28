from database import db
from datetime import datetime
import json


VALID_SIZES = ['S', 'M', 'L', 'XL', 'XXL', 'Free Size']


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(300), default='')
    applicable_measurements = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product_sizes = db.relationship('ProductSize', backref='product', lazy=True,
                                    cascade='all, delete-orphan')
    size_charts = db.relationship('ProductSizeChart', backref='product', lazy=True,
                                  cascade='all, delete-orphan')
    transaction_items = db.relationship('TransactionItem', backref='product', lazy=True)

    @property
    def image_url(self):
        if self.image_filename:
            return f'/static/images/products/{self.image_filename}'
        return ''

    @property
    def total_stock(self):
        return sum(ps.stock for ps in self.product_sizes)

    def to_dict(self):
        sizes_data = [ps.to_dict() for ps in self.product_sizes]
        charts_data = [sc.to_dict() for sc in self.size_charts]
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'price': self.price,
            'sizes': sizes_data,
            'total_stock': self.total_stock,
            'image_filename': self.image_filename,
            'image_url': self.image_url,
            'applicable_measurements': self.applicable_measurements or '',
            'size_charts': charts_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Product {self.name}>'


class ProductSize(db.Model):
    __tablename__ = 'product_sizes'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size = db.Column(db.String(30), nullable=False)
    stock = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'size': self.size,
            'stock': self.stock
        }

    def __repr__(self):
        return f'<ProductSize {self.size}: {self.stock}>'


class ProductSizeChart(db.Model):
    __tablename__ = 'product_size_charts'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    size = db.Column(db.String(30), nullable=False)

    # Upper Body
    bust = db.Column(db.Float, nullable=True)
    across_shoulder = db.Column(db.Float, nullable=True)
    sleeve_length = db.Column(db.Float, nullable=True)
    armhole = db.Column(db.Float, nullable=True)
    neck_width = db.Column(db.Float, nullable=True)

    # Lower Body
    waist = db.Column(db.Float, nullable=True)
    hips = db.Column(db.Float, nullable=True)
    inseam_length = db.Column(db.Float, nullable=True)
    outseam_length = db.Column(db.Float, nullable=True)
    thigh_width = db.Column(db.Float, nullable=True)
    knee_width = db.Column(db.Float, nullable=True)
    bottom_width = db.Column(db.Float, nullable=True)

    # Length
    front_length = db.Column(db.Float, nullable=True)
    back_length = db.Column(db.Float, nullable=True)
    dress_length = db.Column(db.Float, nullable=True)
    kurta_length = db.Column(db.Float, nullable=True)
    dupatta_length = db.Column(db.Float, nullable=True)
    dupatta_width = db.Column(db.Float, nullable=True)

    # Other
    rise = db.Column(db.Float, nullable=True)
    ankle_width = db.Column(db.Float, nullable=True)

    unit = db.Column(db.String(10), default='in')

    def to_dict(self):
        fields = [
            'bust', 'across_shoulder', 'sleeve_length', 'armhole', 'neck_width',
            'waist', 'hips', 'inseam_length', 'outseam_length', 'thigh_width',
            'knee_width', 'bottom_width', 'front_length', 'back_length',
            'dress_length', 'kurta_length', 'dupatta_length', 'dupatta_width',
            'rise', 'ankle_width'
        ]
        res = {
            'id': self.id,
            'product_id': self.product_id,
            'size': self.size,
            'unit': self.unit or 'in'
        }
        for f in fields:
            val = getattr(self, f)
            res[f] = val
        return res

    def __repr__(self):
        return f'<ProductSizeChart {self.size} for Product {self.product_id}>'



class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    customer_name = db.Column(db.String(200), default='Walk-in Customer')
    customer_phone = db.Column(db.String(20), default='')
    payment_method = db.Column(db.String(20), nullable=False)
    subtotal = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    gst_amount = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, default='')

    items = db.relationship('TransactionItem', backref='transaction', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'date': self.date.isoformat() if self.date else None,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'payment_method': self.payment_method,
            'subtotal': self.subtotal,
            'discount_amount': self.discount_amount,
            'gst_amount': self.gst_amount,
            'total': self.total,
            'notes': self.notes,
            'items': [item.to_dict() for item in self.items]
        }

    def __repr__(self):
        return f'<Transaction {self.invoice_number}>'


class TransactionItem(db.Model):
    __tablename__ = 'transaction_items'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    product_size = db.Column(db.String(20), default='')
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_size': self.product_size,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price
        }

    def __repr__(self):
        return f'<TransactionItem {self.product_name} x{self.quantity}>'


class Settings(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(200), default='Jawahar Enterprises')
    email = db.Column(db.String(200), default='')
    phone = db.Column(db.String(20), default='')
    gst_number = db.Column(db.String(50), default='')
    address = db.Column(db.Text, default='')
    currency_symbol = db.Column(db.String(5), default='₹')
    gst_rate = db.Column(db.Float, default=18.0)
    low_stock_threshold = db.Column(db.Integer, default=5)

    def to_dict(self):
        return {
            'id': self.id,
            'store_name': self.store_name,
            'email': self.email,
            'phone': self.phone,
            'gst_number': self.gst_number,
            'address': self.address,
            'currency_symbol': self.currency_symbol,
            'gst_rate': self.gst_rate,
            'low_stock_threshold': self.low_stock_threshold
        }

    def __repr__(self):
        return f'<Settings {self.store_name}>'
