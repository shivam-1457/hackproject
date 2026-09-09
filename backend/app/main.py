import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.routers import (
    auth_router,
    products_router,
    orders_router,
    complaints_router,
    ratings_router,
    admin_router
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kisan2consumer")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure uploads directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Startup: Create tables
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")

    # Check and auto-seed if empty or ensure admin exists
    db = SessionLocal()
    try:
        from app.models.user import User, UserRole
        from app.utils.security import get_password_hash

        # Ensure Admin account exists
        admin_user = db.query(User).filter(User.email == "admin@kisan2consumer.in").first()
        if not admin_user:
            logger.info("Creating default Platform Admin account (admin@kisan2consumer.in)...")
            admin_user = User(
                email="admin@kisan2consumer.in",
                hashed_password=get_password_hash("Admin@123"),
                full_name="Chief Ombudsman & Admin",
                phone="9876500000",
                role=UserRole.ADMIN,
                is_verified=True
            )
            db.add(admin_user)
            db.commit()
            logger.info("Admin account seeded.")

        if db.query(User).count() <= 1:
            logger.info("No demo farmers/consumers found. Running initial data seeding...")
            from seed_data import seed_initial_data
            seed_initial_data(db)
            logger.info("Database successfully seeded with demo farmers, consumers, and crops!")
    except Exception as e:
        logger.warning(f"Note during auto-seed: {e}")
    finally:
        db.close()

    yield
    logger.info("Shutting down Kisan2Consumer API server.")

app = FastAPI(
    title="Kisan2Consumer API",
    description="Direct Farmer-to-Consumer Agricultural Supply Chain & Marketplace",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for seamless frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for dev/testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Uploads directory for produce images
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Mount Frontend directory if available (for unified single-port hosting on Render)
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/site", StaticFiles(directory=frontend_dir, html=True), name="site")

# Include Routers
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(complaints_router)
app.include_router(ratings_router)
app.include_router(admin_router)

@app.get("/")
def root():
    from fastapi.responses import RedirectResponse
    if os.path.exists(frontend_dir):
        return RedirectResponse(url="/site/index.html")
    return {
        "platform": "Kisan2Consumer",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs",
        "support_email": "kisan2consumerhelp@gmail.com",
        "message": "Welcome to Kisan2Consumer Direct Agricultural Platform API"
    }

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "database": str(engine.url).split("@")[-1], "helpdesk": "kisan2consumerhelp@gmail.com"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
