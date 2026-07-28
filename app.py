import os
from flask import Flask


def create_app():
    app = Flask(__name__)

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SECRET_KEY'] = 'jawahar-enterprises-secret-2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "store.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    upload_folder = os.path.join(basedir, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)

    # Run DB migration BEFORE creating tables (handles old schema → new schema)
    db_path = os.path.join(basedir, 'store.db')
    if os.path.exists(db_path):
        try:
            from migrate import migrate
            migrate()
        except Exception as e:
            print(f"Migration warning: {e}")

    from database import db
    db.init_app(app)

    import models  # noqa: F401

    with app.app_context():
        db.create_all()
        _seed_defaults(db)

    from routes import main
    app.register_blueprint(main)

    return app


def _seed_defaults(db):
    from models import Settings, Product, ProductSize

    if not Settings.query.first():
        db.session.add(Settings(
            store_name='Jawahar Enterprises',
            email='jawaharnterprises@gmail.com',
            phone='+91 98765 43210',
            gst_number='36AABCU9603R1ZX',
            address='Shop No. 12, Begum Bazaar\nHyderabad, Telangana - 500012',
            currency_symbol='₹',
            gst_rate=18.0,
            low_stock_threshold=5
        ))

    if not Product.query.first():
        def add_product(name, category, price, sizes_stocks):
            p = Product(name=name, category=category, price=price)
            db.session.add(p)
            db.session.flush()
            for size, stock in sizes_stocks:
                db.session.add(ProductSize(product_id=p.id, size=size, stock=stock))

        add_product('Banarasi Silk Saree', 'Sarees', 4500.0, [('Free Size', 12)])
        add_product('Cotton Churidar Set', 'Churidar', 1200.0, [('S',2),('M',0),('L',1),('XL',0),('XXL',0)])
        add_product('Designer Lehenga', 'Lehenga', 8500.0, [('S',2),('M',3),('L',1),('XL',1)])
        add_product('Printed Kurti', 'Kurtis', 650.0, [('S',5),('M',8),('L',6),('XL',4),('XXL',2)])
        add_product('Embroidered Dupatta', 'Dupattas', 850.0, [('Free Size', 4)])
        add_product('Chanderi Suit Set', 'Suit Sets', 3200.0, [('S',1),('M',1),('L',0),('XL',0)])
        add_product('Palazzo Pants', 'Bottoms', 550.0, [('S',4),('M',6),('L',5),('XL',2),('XXL',1)])
        add_product('Anarkali Suit', 'Suit Sets', 2800.0, [('S',2),('M',2),('L',1),('XL',1)])
        add_product('Cotton Saree', 'Sarees', 1800.0, [('Free Size', 1)])
        add_product('Party Wear Gown', 'Gowns', 5500.0, [('S',2),('M',2),('L',1)])

    db.session.commit()



if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
