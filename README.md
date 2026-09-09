# Kisan2Consumer (hackproject)

**Kisan2Consumer** is a production-ready, full-stack direct-to-consumer agricultural digital marketplace engineered to eliminate intermediaries and brokers. It connects Indian farmers (*Kisans*) directly with consumers (*Grahaks*) with full GPS farm origin traceability, token-based email verification, simulated payments, damage dispute arbitration, and real-time delivery tracking.

- **GitHub Repository**: [shivam-1457/hackproject](https://github.com/shivam-1457/hackproject.git)
- **Render Deployment Blueprint**: [Render Dashboard](https://dashboard.render.com/project/prj-dagp4ep5efls7381303g)
- **Official Helpdesk & Verification Service**: `kisan2consumerhelp@gmail.com`

---

## 🌾 Core Features & Capabilities

1. **Direct Farm-to-Consumer Marketplace**:
   - Consumers purchase harvest directly with 100% transparent pricing and no broker cuts.
   - Proximity search powered by the Haversine formula (km distance from consumer to farm).
   - Category filtering (Vegetables, Fruits, Grains, Pulses, Dairy, Spices) and Organic certification tags.

2. **Farmer Produce Management (Full CRUD + Photo Upload)**:
   - Farmers can **Add**, **Get**, **Update/Edit**, and **Delete** produce listings.
   - **Direct Device Image Upload**: File upload endpoint (`POST /api/products/upload-image`) saves farm photos locally/statically with live thumbnail preview.
   - Farm GPS coordinate recording for map integration.

3. **Interactive Leaflet Delivery & Farm Origin Tracker**:
   - Every order includes a **"🗺️ Track Farm Origin & Route"** button.
   - Visualizes the farmer's **Farm Origin Pin** (🚜) and consumer's **Delivery Address Pin** (🏡).
   - Animated delivery vehicle (🚚) moving along an interactive polyline route according to live dispatch status (`CONFIRMED` -> `SHIPPED` -> `DELIVERED`).
   - Computes highway transit distance in kilometers and ETA.

4. **Simulated Payment Gateway**:
   - Supports Card, UPI (PhonePe / GPay simulation), and NetBanking.
   - Generates unique transaction IDs (`K2C_TXN_...`), deducts stock instantly, and sends email alerts.

5. **Token-Based Email Verification**:
   - Dispatched from `kisan2consumerhelp@gmail.com`.
   - Cryptographically random verification tokens with one-click verification links.

6. **Farmer & Consumer Notifications**:
   - Farmer receives immediate email alerts with customer address and crop quantities upon order placement.
   - Consumer receives order confirmation summaries and digital receipts.

7. **Admin Portal & Dispute Arbitration Desk**:
   - Comprehensive Ombudsman portal at `/site/admin-portal.html` (or `frontend/admin-portal.html`).
   - Platform KPIs (Total Farmers, Total Consumers, Gross Merchandise Value, Open Disputes).
   - Dispute resolution desk: Inspect photo evidence of damaged/spoiled goods, hear consumer statements, and issue legally binding rulings (`RESOLVED_REFUND`, `RESOLVED_REPLACED`, `REJECTED`).
   - Automated verdict notifications emailed to both parties.
   - User Directory tab for managing all platform accounts and verification statuses.

8. **Consumer Rating & Reviews**:
   - 5-star interactive rating widget with written reviews dynamically updating produce ratings.

---

## 🛠️ Technology Stack

- **Backend**:
  - **FastAPI** (Async Python 3 framework)
  - **PostgreSQL** (with automatic SQLite fallback `kisan2consumer.db` for zero-friction local development)
  - **SQLAlchemy 2.0** ORM & **Pydantic v2**
  - **JWT (HS256)** authentication & **Bcrypt** password hashing
  - **Multipart file upload** for produce images (`/uploads`)
  - **Unified static file serving** (`/site`) for single-port Render hosting
- **Frontend**:
  - Semantic **HTML5**, modern **CSS3**, and modular **ES6 JavaScript**
  - **Leaflet.js & OpenStreetMap** for interactive geospatial tracking
  - Fully decoupled architecture in separate `backend/` and `frontend/` folders

---

## 📁 Project Structure

```
kisan2consumer/
├── backend/
│   ├── app/
│   │   ├── config.py              # Configuration with postgresql URL and email settings
│   │   ├── database.py            # PostgreSQL engine with SQLite fallback
│   │   ├── main.py                # FastAPI app with static mounts (/uploads, /site)
│   │   ├── models/                # User, Product, Order, Complaint, Rating
│   │   ├── schemas/               # Pydantic schemas (Product, Order, ComplaintArbitrate)
│   │   ├── routers/               # auth, products, orders, complaints, ratings, admin
│   │   └── utils/                 # security, dependencies, email dispatcher
│   ├── uploads/                   # Uploaded farm crop photos
│   ├── seed_data.py               # Pre-seeded demo accounts and harvest listings
│   ├── test_api.py                # 20-point automated end-to-end test suite
│   ├── requirements.txt           # Python dependencies
│   └── .env.example               # Environment variables template
│
├── frontend/
│   ├── index.html                 # Homepage with hero & featured produce
│   ├── marketplace.html           # Catalog, search, filters & Leaflet farm map
│   ├── product-detail.html        # Produce details & farm mini-map
│   ├── auth.html                  # Sign in / Register with map pin picker & demo accounts
│   ├── verify-email.html          # Email verification portal (kisan2consumerhelp@gmail.com)
│   ├── cart.html                  # Shopping cart
│   ├── checkout.html              # Delivery address & simulated payment gateway
│   ├── farmer-dashboard.html      # Farmer portal (CRUD, image upload, orders)
│   ├── consumer-dashboard.html    # Consumer portal (Leaflet order tracking, damage disputes)
│   ├── admin-portal.html          # Admin arbitration portal (disputes, stats, user oversight)
│   ├── css/
│   │   ├── style.css              # Earth-tone design system
│   │   └── components.css         # Badges, modals, cards, responsive tables
│   └── js/
│       ├── api.js                 # Centralized adaptive API client
│       ├── auth.js                # Authentication & Leaflet pin picker
│       ├── marketplace.js         # India farm map & proximity search
│       ├── product-detail.js      # Mini-map & review submissions
│       ├── farmer.js              # Crop CRUD & photo upload logic
│       ├── consumer.js            # Leaflet live route tracking & complaints
│       └── admin.js               # Dispute arbitration & platform stats
│
├── render.yaml                    # Render Blueprint (Web Service + Managed PostgreSQL)
├── Procfile                       # Process file for cloud hosting
├── start.sh                       # Shell start script
└── .gitignore                     # Git ignore rules
```

---

## 👥 Demo Accounts for Immediate Testing

| Role | Email | Password | Details |
| :--- | :--- | :--- | :--- |
| **Platform Admin** | `admin@kisan2consumer.in` | `Admin@123` | Platform Ombudsman & Dispute Arbitrator |
| **Farmer (Kisan)** | `rameshwar.patil@kisan.in` | `password123` | Patil Organic Agro Farms, Nashik (Maharashtra) |
| **Farmer (Kisan)** | `gurpreet.singh@kisan.in` | `password123` | Golden Harvest Fields, Ludhiana (Punjab) |
| **Consumer (Grahak)** | `priya.sharma@consumer.in` | `password123` | Mumbai, Maharashtra |

*(All demo accounts are pre-verified. You can also register any new account and use the auto-filled verification token!)*

---

## 🚀 Running Locally

### 1. Run the Backend Server
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **API Documentation (Swagger UI)**: `http://127.0.0.1:8000/docs`
- **Database**: Connects to PostgreSQL automatically, or smoothly uses SQLite (`kisan2consumer.db`) if local PostgreSQL credentials are not configured.

### 2. Run the Frontend
Option A (Dedicated server):
```bash
cd frontend
python -m http.server 5500
```
Then visit: `http://127.0.0.1:5500/index.html`

Option B (Unified serving directly from FastAPI):
Visit: `http://127.0.0.1:8000/site/index.html`

---

## 🧪 Running Automated Tests

A comprehensive 20-point automated test suite verifies all system components:

```bash
cd backend
python test_api.py
```

Tests cover:
1. Health check & PostgreSQL / SQLite connection
2. Haversine distance calculation
3. User registration & cryptographic email verification
4. JWT login & role guards
5. Direct image upload (`POST /api/products/upload-image`)
6. Produce listing creation
7. Produce listing update (`PUT /api/products/{id}`)
8. Consumer checkout & order placement
9. Simulated payment gateway & instant stock deduction
10. Transit damage dispute filing
11. Admin login & KPI platform analytics
12. Admin dispute arbitration ruling & email dispatch
13. Product rating & review updates
14. Background email logger (`kisan2consumerhelp@gmail.com`)

---

## ☁️ Deploying on Render

This project is configured with `render.yaml` for 1-click deployment on Render:

1. Push your repository to GitHub:
   ```bash
   git push -u origin main
   ```
2. In your [Render Dashboard](https://dashboard.render.com/project/prj-dagp4ep5efls7381303g):
   - Click **New** -> **Blueprint**.
   - Select your repository `shivam-1457/hackproject`.
   - Render will automatically provision:
     - A **PostgreSQL Database** (`kisan2consumer-postgres`).
     - A **Python Web Service** running Uvicorn.
3. Once deployed, the entire platform (both frontend and backend) is live at your Render URL!
