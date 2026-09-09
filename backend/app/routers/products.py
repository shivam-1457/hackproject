import math
import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.config import settings
from app.database import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.utils.dependencies import require_farmer, get_current_user

router = APIRouter(prefix="/api/products", tags=["Products"])

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates distance between two geographic coordinates in kilometers."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None
    R = 6371.0 # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

@router.get("", response_model=List[ProductResponse])
def get_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    is_organic: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = "newest", # newest, price_asc, price_desc, rating, distance
    user_lat: Optional[float] = None,
    user_lng: Optional[float] = None,
    max_distance_km: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.is_active == True, Product.stock_quantity > 0)

    if search:
        search_fmt = f"%{search}%"
        query = query.filter(or_(Product.title.ilike(search_fmt), Product.description.ilike(search_fmt)))

    if category and category != "All":
        query = query.filter(Product.category == category)

    if is_organic is not None:
        query = query.filter(Product.is_organic == is_organic)

    if min_price is not None:
        query = query.filter(Product.price_per_unit >= min_price)

    if max_price is not None:
        query = query.filter(Product.price_per_unit <= max_price)

    products = query.all()
    results = []

    for prod in products:
        p_dict = {
            "id": prod.id,
            "farmer_id": prod.farmer_id,
            "title": prod.title,
            "description": prod.description,
            "category": prod.category,
            "unit": prod.unit,
            "price_per_unit": prod.price_per_unit,
            "stock_quantity": prod.stock_quantity,
            "harvest_date": prod.harvest_date,
            "image_url": prod.image_url,
            "is_organic": prod.is_organic,
            "farm_location_name": prod.farm_location_name,
            "farm_lat": prod.farm_lat,
            "farm_lng": prod.farm_lng,
            "average_rating": prod.average_rating or 0.0,
            "total_reviews": prod.total_reviews or 0,
            "is_active": prod.is_active,
            "created_at": prod.created_at,
            "updated_at": prod.updated_at,
            "farmer": prod.farmer
        }

        # Calculate distance if user passed coordinates
        if user_lat is not None and user_lng is not None and prod.farm_lat and prod.farm_lng:
            dist = calculate_haversine_distance(user_lat, user_lng, prod.farm_lat, prod.farm_lng)
            p_dict["distance_km"] = dist
        else:
            p_dict["distance_km"] = None

        if max_distance_km is not None and p_dict["distance_km"] is not None:
            if p_dict["distance_km"] > max_distance_km:
                continue

        results.append(p_dict)

    # Sorting
    if sort_by == "price_asc":
        results.sort(key=lambda x: x["price_per_unit"])
    elif sort_by == "price_desc":
        results.sort(key=lambda x: x["price_per_unit"], reverse=True)
    elif sort_by == "rating":
        results.sort(key=lambda x: x["average_rating"], reverse=True)
    elif sort_by == "distance" and user_lat is not None and user_lng is not None:
        results.sort(key=lambda x: x["distance_km"] if x["distance_km"] is not None else 999999)
    else:
        # Default newest
        results.sort(key=lambda x: x["created_at"] or 0, reverse=True)

    return results

@router.get("/farmer/my-products", response_model=List[ProductResponse])
def get_farmer_products(
    farmer: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    products = db.query(Product).filter(Product.farmer_id == farmer.id).order_by(Product.created_at.desc()).all()
    return products

@router.get("/{product_id}", response_model=ProductResponse)
def get_product_details(
    product_id: int,
    user_lat: Optional[float] = None,
    user_lng: Optional[float] = None,
    db: Session = Depends(get_db)
):
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    res = ProductResponse.model_validate(prod)
    if user_lat is not None and user_lng is not None and prod.farm_lat and prod.farm_lng:
        res.distance_km = calculate_haversine_distance(user_lat, user_lng, prod.farm_lat, prod.farm_lng)
    return res

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    farmer: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    # Use farmer profile defaults if farm coordinates are not provided
    farm_lat = data.farm_lat or farmer.farm_lat
    farm_lng = data.farm_lng or farmer.farm_lng
    farm_location_name = data.farm_location_name or farmer.farm_address or farmer.farm_city

    new_prod = Product(
        farmer_id=farmer.id,
        title=data.title,
        description=data.description,
        category=data.category,
        unit=data.unit,
        price_per_unit=data.price_per_unit,
        stock_quantity=data.stock_quantity,
        harvest_date=data.harvest_date,
        image_url=data.image_url,
        is_organic=data.is_organic,
        farm_location_name=farm_location_name,
        farm_lat=farm_lat,
        farm_lng=farm_lng,
        average_rating=0.0,
        total_reviews=0,
        is_active=True
    )
    db.add(new_prod)
    db.commit()
    db.refresh(new_prod)
    return new_prod

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    farmer: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    prod = db.query(Product).filter(Product.id == product_id, Product.farmer_id == farmer.id).first()
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or unauthorized.")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prod, key, value)

    db.commit()
    db.refresh(prod)
    return prod

@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(
    product_id: int,
    farmer: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    prod = db.query(Product).filter(Product.id == product_id, Product.farmer_id == farmer.id).first()
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or unauthorized.")

    # Soft delete / deactivate
    prod.is_active = False
    db.commit()
    return {"message": "Product removed from active marketplace listings."}

@router.post("/upload-image")
def upload_product_image(
    file: UploadFile = File(...),
    farmer: User = Depends(require_farmer)
):
    """
    Uploads a product image file from farmer, saves to uploads directory,
    and returns accessible static URL path.
    """
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image format '{ext}'. Allowed formats: {', '.join(allowed_extensions)}"
        )

    # Ensure upload directory exists
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename to avoid collision
    unique_filename = f"prod_{farmer.id}_{uuid.uuid4().hex[:10]}{ext}"
    target_path = os.path.join(upload_dir, unique_filename)

    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded image: {str(e)}"
        )

    image_url = f"/uploads/{unique_filename}"
    return {
        "status": "success",
        "image_url": image_url,
        "filename": unique_filename,
        "message": "Product image uploaded successfully."
    }

