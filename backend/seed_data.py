import datetime
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models.user import User, UserRole
from app.models.product import Product, ProductCategory
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.complaint import Complaint, ComplaintIssueType, ComplaintStatus
from app.models.rating import Rating
from app.utils.security import hash_password

def seed_initial_data(db: Session = None):
    should_close = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        should_close = True

    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("Database already contains records. Skipping seed.")
            return

        print("Seeding demo users...")
        default_pwd = hash_password("password123")

        # 1. Farmers
        farmer1 = User(
            email="rameshwar.patil@kisan.in",
            hashed_password=default_pwd,
            full_name="Rameshwar Patil",
            phone="+91 98220 12345",
            role=UserRole.FARMER,
            farm_name="Patil Organic Agro Farms",
            farm_address="Gat No. 44, Dindori Road, Nashik",
            farm_city="Nashik",
            farm_state="Maharashtra",
            farm_pincode="422003",
            farm_lat=19.9975,
            farm_lng=73.7898,
            is_verified=True
        )

        farmer2 = User(
            email="gurpreet.singh@kisan.in",
            hashed_password=default_pwd,
            full_name="Sardar Gurpreet Singh",
            phone="+91 98140 56789",
            role=UserRole.FARMER,
            farm_name="Golden Harvest Fields",
            farm_address="Village Khanna, GT Road, Ludhiana",
            farm_city="Ludhiana",
            farm_state="Punjab",
            farm_pincode="141401",
            farm_lat=30.9010,
            farm_lng=75.8573,
            is_verified=True
        )

        farmer3 = User(
            email="ananya.reddy@kisan.in",
            hashed_password=default_pwd,
            full_name="Ananya Reddy",
            phone="+91 98480 11223",
            role=UserRole.FARMER,
            farm_name="Reddy Spices & Horticulture",
            farm_address="Etukur Road, Guntur",
            farm_city="Guntur",
            farm_state="Andhra Pradesh",
            farm_pincode="522017",
            farm_lat=16.3067,
            farm_lng=80.4365,
            is_verified=True
        )

        # 2. Consumers
        consumer1 = User(
            email="priya.sharma@consumer.in",
            hashed_password=default_pwd,
            full_name="Priya Sharma",
            phone="+91 98200 44556",
            role=UserRole.CONSUMER,
            delivery_address="Flat 402, Green Meadows, Andheri West",
            delivery_city="Mumbai",
            delivery_state="Maharashtra",
            delivery_pincode="400053",
            is_verified=True
        )

        consumer2 = User(
            email="rajesh.verma@consumer.in",
            hashed_password=default_pwd,
            full_name="Rajesh Verma",
            phone="+91 98110 77889",
            role=UserRole.CONSUMER,
            delivery_address="B-12, Sector 62, Noida",
            delivery_city="Noida",
            delivery_state="Uttar Pradesh",
            delivery_pincode="201301",
            is_verified=True
        )

        # 3. Admin Account
        admin1 = User(
            email="admin@kisan2consumer.in",
            hashed_password=hash_password("Admin@123"),
            full_name="Chief Ombudsman & Platform Admin",
            phone="+91 99000 11222",
            role=UserRole.ADMIN,
            is_verified=True
        )

        db.add_all([farmer1, farmer2, farmer3, consumer1, consumer2, admin1])
        db.commit()

        # Refresh to get IDs
        db.refresh(farmer1)
        db.refresh(farmer2)
        db.refresh(farmer3)
        db.refresh(consumer1)
        db.refresh(consumer2)

        print("Seeding crops and agricultural products...")
        products = [
            Product(
                farmer_id=farmer1.id,
                title="Nashik Farm-Fresh Red Onions",
                description="Naturally harvested pungent Nashik onions. Dried and sorted for supreme shelf life. Direct from Dindori belt.",
                category=ProductCategory.VEGETABLES,
                unit="kg",
                price_per_unit=28.0,
                stock_quantity=500.0,
                harvest_date="2026-08-25",
                image_url="https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=600&q=80",
                is_organic=True,
                farm_location_name="Patil Organic Agro, Nashik",
                farm_lat=19.9975,
                farm_lng=73.7898,
                average_rating=4.8,
                total_reviews=12
            ),
            Product(
                farmer_id=farmer1.id,
                title="Vine-Ripened Organic Tomatoes",
                description="Juicy, pesticide-free red salad tomatoes handpicked at optimal ripeness.",
                category=ProductCategory.VEGETABLES,
                unit="kg",
                price_per_unit=32.0,
                stock_quantity=300.0,
                harvest_date="2026-08-28",
                image_url="https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=600&q=80",
                is_organic=True,
                farm_location_name="Patil Organic Agro, Nashik",
                farm_lat=19.9975,
                farm_lng=73.7898,
                average_rating=4.6,
                total_reviews=8
            ),
            Product(
                farmer_id=farmer2.id,
                title="Punjab Sharbati Gold Wheat (Whole Grain)",
                description="Authentic heavy Sharbati wheat grains from fertile Ludhiana plains. Perfect for soft rotis and traditional breads.",
                category=ProductCategory.GRAINS,
                unit="kg",
                price_per_unit=42.0,
                stock_quantity=1200.0,
                harvest_date="2026-08-15",
                image_url="https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=600&q=80",
                is_organic=True,
                farm_location_name="Golden Harvest Fields, Ludhiana",
                farm_lat=30.9010,
                farm_lng=75.8573,
                average_rating=4.9,
                total_reviews=25
            ),
            Product(
                farmer_id=farmer2.id,
                title="Aromatic Long Grain Basmati Rice",
                description="Traditional 1121 steam Basmati rice with exquisite aroma and double-length elongation upon cooking.",
                category=ProductCategory.GRAINS,
                unit="kg",
                price_per_unit=85.0,
                stock_quantity=800.0,
                harvest_date="2026-08-10",
                image_url="https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=600&q=80",
                is_organic=False,
                farm_location_name="Golden Harvest Fields, Ludhiana",
                farm_lat=30.9010,
                farm_lng=75.8573,
                average_rating=4.7,
                total_reviews=19
            ),
            Product(
                farmer_id=farmer3.id,
                title="Guntur Sun-Dried Red Stemless Chillies",
                description="World-renowned pungent Guntur Sannam chillies. Naturally sun-dried on clean tarpaulins without artificial coloring.",
                category=ProductCategory.SPICES,
                unit="kg",
                price_per_unit=240.0,
                stock_quantity=150.0,
                harvest_date="2026-08-20",
                image_url="https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=600&q=80",
                is_organic=True,
                farm_location_name="Reddy Spices, Guntur",
                farm_lat=16.3067,
                farm_lng=80.4365,
                average_rating=5.0,
                total_reviews=14
            ),
            Product(
                farmer_id=farmer3.id,
                title="High-Curcumin Lakadong Turmeric Powder",
                description="7%+ active curcumin organic turmeric ground from whole fingers. Lab-tested pure immunity booster.",
                category=ProductCategory.SPICES,
                unit="kg",
                price_per_unit=310.0,
                stock_quantity=100.0,
                harvest_date="2026-08-12",
                image_url="https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=600&q=80",
                is_organic=True,
                farm_location_name="Reddy Spices, Guntur",
                farm_lat=16.3067,
                farm_lng=80.4365,
                average_rating=4.9,
                total_reviews=17
            )
        ]

        db.add_all(products)
        db.commit()
        for p in products:
            db.refresh(p)

        print("Seeding initial order and ratings...")
        # Sample order from Priya Sharma to Rameshwar Patil
        sample_order = Order(
            consumer_id=consumer1.id,
            total_amount=200.0,
            delivery_fee=0.0,
            grand_total=200.0,
            status=OrderStatus.DELIVERED,
            payment_status=PaymentStatus.COMPLETED,
            payment_method="UPI_SIMULATION",
            payment_transaction_id="K2C_TXN_DEMO987654",
            payment_timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=2),
            shipping_address=consumer1.delivery_address,
            shipping_city=consumer1.delivery_city,
            shipping_state=consumer1.delivery_state,
            shipping_pincode=consumer1.delivery_pincode,
            shipping_notes="Please leave with society guard if unavailable"
        )
        db.add(sample_order)
        db.commit()
        db.refresh(sample_order)

        order_item1 = OrderItem(
            order_id=sample_order.id,
            product_id=products[0].id,
            farmer_id=farmer1.id,
            product_title=products[0].title,
            quantity=5.0,
            unit="kg",
            unit_price=28.0,
            subtotal=140.0
        )
        order_item2 = OrderItem(
            order_id=sample_order.id,
            product_id=products[1].id,
            farmer_id=farmer1.id,
            product_title=products[1].title,
            quantity=2.0,
            unit="kg",
            unit_price=30.0,
            subtotal=60.0
        )
        db.add_all([order_item1, order_item2])
        db.commit()

        # Sample rating from Priya
        sample_rating = Rating(
            product_id=products[0].id,
            consumer_id=consumer1.id,
            order_id=sample_order.id,
            rating_score=5.0,
            review_text="Extremely fresh Nashik onions! No middleman markups and received crisp farm produce in just 2 days."
        )
        db.add(sample_rating)

        # Sample complaint to demonstrate dispute resolution
        sample_complaint = Complaint(
            order_id=sample_order.id,
            order_item_id=order_item2.id,
            product_id=products[1].id,
            consumer_id=consumer1.id,
            farmer_id=farmer1.id,
            issue_type=ComplaintIssueType.DAMAGED_PRODUCE,
            description="Two tomatoes in the box were crushed during transit box handling.",
            proof_image_url="https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=400&q=80",
            requested_resolution="REFUND",
            status=ComplaintStatus.RESOLVED_REFUND,
            resolution_notes="Farmer approved instant partial refund of Rs 30 for the damaged produce."
        )
        db.add(sample_complaint)

        # Open complaint awaiting Admin Arbitration
        open_dispute = Complaint(
            order_id=sample_order.id,
            order_item_id=order_item1.id,
            product_id=products[0].id,
            consumer_id=consumer2.id,
            farmer_id=farmer1.id,
            issue_type=ComplaintIssueType.DELAYED_DELIVERY,
            description="Delivery was delayed by 3 days due to courier route re-allocation. Seeking compensation or verification of produce freshness.",
            proof_image_url="https://images.unsplash.com/photo-1582284540020-8acbe03f4924?auto=format&fit=crop&w=400&q=80",
            requested_resolution="REFUND",
            status=ComplaintStatus.OPEN
        )
        db.add(open_dispute)
        db.commit()

        print("Database seeded successfully with demo farmers, consumers, crops, and disputes!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        if should_close:
            db.close()

if __name__ == "__main__":
    seed_initial_data()
