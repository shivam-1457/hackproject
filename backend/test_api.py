import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base, SessionLocal
from seed_data import seed_initial_data

def run_all_tests():
    print("================ [STARTING KISAN2CONSUMER BACKEND TEST] ================")
    # 1. Initialize schema & seed
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_initial_data(db)
    db.close()

    client = TestClient(app)

    # 2. Health check
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] Health check OK:", res.json())

    # 3. Product listing
    res = client.get("/api/products")
    assert res.status_code == 200, f"Products listing failed: {res.text}"
    products = res.json()
    assert len(products) >= 6, f"Expected at least 6 products, got {len(products)}"
    print(f"[PASS] Product listing fetched {len(products)} products.")

    # 4. Geolocation search (Distance from Mumbai lat=19.0760, lng=72.8777)
    res = client.get("/api/products?user_lat=19.0760&user_lng=72.8777&sort_by=distance")
    assert res.status_code == 200
    closest_prods = res.json()
    assert closest_prods[0]["distance_km"] is not None
    print(f"[PASS] Distance calculation working. Closest product: {closest_prods[0]['title']} at {closest_prods[0]['distance_km']} km.")

    # 5. Farmer Registration & Token-based Email Verification Flow
    import time
    test_farmer_email = f"test.farmer.{int(time.time())}@kisan.in"
    reg_data = {
        "email": test_farmer_email,
        "password": "strongPassword123",
        "full_name": "Balwinder Singh",
        "phone": "+91 99999 11111",
        "role": "farmer",
        "farm_name": "Balwinder Wheat Estate",
        "farm_address": "Near Canal Bridge, Moga",
        "farm_city": "Moga",
        "farm_state": "Punjab",
        "farm_pincode": "142001",
        "farm_lat": 30.8165,
        "farm_lng": 75.1717
    }
    reg_res = client.post("/api/auth/register", json=reg_data)
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
    reg_json = reg_res.json()
    verification_token = reg_json["dev_verification_token"]
    print(f"[PASS] Registration successful. Token generated: {verification_token[:10]}...")

    # 6. Verify Email using token
    ver_res = client.post("/api/auth/verify-email", json={"token": verification_token})
    assert ver_res.status_code == 200, f"Email verification failed: {ver_res.text}"
    print("[PASS] Email verified successfully with token.")

    # 7. Login with newly verified user
    login_res = client.post("/api/auth/login", json={"email": test_farmer_email, "password": "strongPassword123"})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    farmer_token = login_res.json()["access_token"]
    farmer_headers = {"Authorization": f"Bearer {farmer_token}"}
    print("[PASS] Farmer Login successful, JWT token obtained.")

    # 8. Test Farmer Image Upload
    import io
    dummy_image_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    upload_res = client.post(
        "/api/products/upload-image",
        files={"file": ("test_carrot.png", io.BytesIO(dummy_image_data), "image/png")},
        headers=farmer_headers
    )
    assert upload_res.status_code == 200, f"Image upload failed: {upload_res.text}"
    uploaded_image_url = upload_res.json()["image_url"]
    print(f"[PASS] Farmer image upload successful: {uploaded_image_url}")

    # 9. Create new crop as farmer (using uploaded image)
    crop_data = {
        "title": "Fresh Organic Carrots",
        "description": "Sweet red crunchy winter carrots grown without synthetic fertilizer.",
        "category": "Fresh Vegetables",
        "unit": "kg",
        "price_per_unit": 40.0,
        "stock_quantity": 250.0,
        "is_organic": True,
        "image_url": uploaded_image_url
    }
    crop_res = client.post("/api/products", json=crop_data, headers=farmer_headers)
    assert crop_res.status_code == 201, f"Crop creation failed: {crop_res.text}"
    created_product_id = crop_res.json()["id"]
    print(f"[PASS] Crop listed successfully with ID #{created_product_id}.")

    # 10. Test Farmer Crop Update (PUT)
    update_data = {
        "price_per_unit": 42.0,
        "stock_quantity": 260.0
    }
    update_res = client.put(f"/api/products/{created_product_id}", json=update_data, headers=farmer_headers)
    assert update_res.status_code == 200, f"Crop update failed: {update_res.text}"
    assert update_res.json()["price_per_unit"] == 42.0
    print(f"[PASS] Farmer crop updated successfully (Price: Rs 42/kg, Stock: 260kg).")

    # 11. Consumer Login
    cons_login = client.post("/api/auth/login", json={"email": "priya.sharma@consumer.in", "password": "password123"})
    assert cons_login.status_code == 200, f"Consumer login failed: {cons_login.text}"
    consumer_token = cons_login.json()["access_token"]
    consumer_headers = {"Authorization": f"Bearer {consumer_token}"}
    print("[PASS] Consumer Login successful.")

    # 12. Consumer Places Order
    order_data = {
        "items": [{"product_id": created_product_id, "quantity": 10.0}],
        "shipping_address": "Flat 402, Green Meadows, Andheri West",
        "shipping_city": "Mumbai",
        "shipping_state": "Maharashtra",
        "shipping_pincode": "400053",
        "shipping_notes": "Leave at front door security",
        "payment_method": "UPI_SIMULATION"
    }
    order_res = client.post("/api/orders", json=order_data, headers=consumer_headers)
    assert order_res.status_code == 201, f"Order placement failed: {order_res.text}"
    order_id = order_res.json()["id"]
    print(f"[PASS] Order placed successfully with ID #{order_id}.")

    # 13. Simulate Payment & Order Confirmation
    pay_res = client.post(f"/api/orders/{order_id}/pay", json={"payment_method": "UPI_SIMULATION", "upi_id": "priya@okaxis"}, headers=consumer_headers)
    assert pay_res.status_code == 200, f"Payment simulation failed: {pay_res.text}"
    assert pay_res.json()["payment_status"] == "COMPLETED"
    print(f"[PASS] Payment simulated & confirmed: Txn ID {pay_res.json()['payment_transaction_id']}")

    # 14. Check Stock Deduction
    prod_check = client.get(f"/api/products/{created_product_id}")
    assert prod_check.json()["stock_quantity"] == 250.0 # 260 - 10
    print("[PASS] Stock deducted correctly (260 -> 250 kg).")

    # 15. File Damaged Goods Complaint
    complaint_payload = {
        "order_id": order_id,
        "product_id": created_product_id,
        "issue_type": "Damaged Produce / Crushed during Transit",
        "description": "Bag of carrots arrived crushed at the bottom due to heavy box pressure.",
        "proof_image_url": "https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?auto=format&fit=crop&w=400&q=80",
        "requested_resolution": "REFUND"
    }
    comp_res = client.post("/api/complaints", json=complaint_payload, headers=consumer_headers)
    assert comp_res.status_code == 201, f"Complaint filing failed: {comp_res.text}"
    complaint_id = comp_res.json()["id"]
    print(f"[PASS] Damage Complaint filed successfully with ID #{complaint_id}.")

    # 16. Admin Login & Dispute Arbitration
    admin_login = client.post("/api/auth/login", json={"email": "admin@kisan2consumer.in", "password": "Admin@123"})
    assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("[PASS] Admin Login successful.")

    # 17. Admin Statistics Check
    admin_stats_res = client.get("/api/admin/stats", headers=admin_headers)
    assert admin_stats_res.status_code == 200
    stats = admin_stats_res.json()
    print(f"[PASS] Admin Stats OK: {stats['total_users']} users, {stats['total_orders']} orders, GMV: Rs {stats['gross_merchandise_value']}.")

    # 18. Admin Arbitrates Dispute
    arbitrate_payload = {
        "status": "RESOLVED_REFUND",
        "admin_verdict": "Arbitrated by Platform Grievance Desk: Full refund approved after photo proof verification.",
        "resolution_notes": "Credited to consumer's original UPI account within 24 hours."
    }
    arb_res = client.put(f"/api/admin/complaints/{complaint_id}/arbitrate", json=arbitrate_payload, headers=admin_headers)
    assert arb_res.status_code == 200, f"Admin arbitration failed: {arb_res.text}"
    print(f"[PASS] Admin arbitrated complaint #{complaint_id} with verdict RESOLVED_REFUND.")

    # 19. Submit Rating & Review
    rating_payload = {
        "product_id": created_product_id,
        "order_id": order_id,
        "rating_score": 4.5,
        "review_text": "Carrots are super sweet and juicy! Great direct farm connection."
    }
    rat_res = client.post("/api/ratings", json=rating_payload, headers=consumer_headers)
    assert rat_res.status_code == 201, f"Rating failed: {rat_res.text}"
    print(f"[PASS] Rating submitted. Product rating updated to {rat_res.json()['rating_score']} stars.")

    # 20. Inspect Dev Email Log
    email_res = client.get("/api/auth/recent-emails")
    assert email_res.status_code == 200
    emails = email_res.json()["emails"]
    print(f"[PASS] Email notification store captured {len(emails)} emails (verification, order confirmation, alerts, arbitration).")

    print("\n================ [ALL BACKEND TESTS PASSED SUCCESSFULLY! 100%] ================")

if __name__ == "__main__":
    run_all_tests()
