from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import Base, engine
from .config import settings
from .routers import auth, products, orders, reviews, complaints, admin

Base.metadata.create_all(bind=engine)
app=FastAPI(title="Kisan2Consumer API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=[settings.frontend_url,"http://localhost:5500","http://127.0.0.1:5500"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
Path("uploads").mkdir(exist_ok=True)
app.mount("/uploads",StaticFiles(directory="uploads"),name="uploads")
app.include_router(auth.router); app.include_router(products.router); app.include_router(orders.router); app.include_router(reviews.router); app.include_router(complaints.router); app.include_router(admin.router)
@app.get("/")
def root(): return {"message":"Kisan2Consumer API is running"}
@app.get("/health")
def health(): return {"status":"ok"}
