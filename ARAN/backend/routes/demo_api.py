"""
ARAN — Demo Shopping API

This is the target API that ARAN protects.
It simulates a real e-commerce backend with lightweight endpoints.
The traffic simulator sends requests here; ARAN monitors and analyzes them.
"""
import random
import time
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Fake product catalog
PRODUCTS = [
    {"id": 1, "name": "Wireless Headphones", "price": 89.99, "stock": 142},
    {"id": 2, "name": "Mechanical Keyboard", "price": 129.99, "stock": 67},
    {"id": 3, "name": "USB-C Hub", "price": 49.99, "stock": 230},
    {"id": 4, "name": "Monitor Stand", "price": 39.99, "stock": 88},
    {"id": 5, "name": "Webcam HD", "price": 69.99, "stock": 55},
    {"id": 6, "name": "Desk Lamp", "price": 34.99, "stock": 190},
    {"id": 7, "name": "Mouse Pad XL", "price": 19.99, "stock": 320},
    {"id": 8, "name": "Cable Organizer", "price": 12.99, "stock": 500},
]


class LoginRequest(BaseModel):
    username: str
    password: str


class CheckoutRequest(BaseModel):
    cart_items: list
    payment_token: str = "demo_token"


@router.get("/products")
async def get_products():
    """Returns the full product catalog."""
    return {"products": PRODUCTS, "total": len(PRODUCTS)}


@router.get("/search")
async def search_products(q: str = ""):
    """Search products by name (case-insensitive)."""
    results = [p for p in PRODUCTS if q.lower() in p["name"].lower()]
    return {"query": q, "results": results, "count": len(results)}


@router.get("/product/{product_id}")
async def get_product(product_id: int):
    """Fetch a single product by ID."""
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/login")
async def login(body: LoginRequest):
    """
    Simulated login endpoint.
    ~35% of requests intentionally fail — this allows bots
    performing credential stuffing to rack up a high failure ratio.
    """
    valid = random.random() > 0.35
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": f"demo_token_{random.randint(10000, 99999)}", "user": body.username}


@router.get("/cart")
async def get_cart():
    """Returns a simulated cart."""
    cart = random.sample(PRODUCTS, k=random.randint(1, 4))
    total = sum(p["price"] for p in cart)
    return {"items": cart, "total": round(total, 2)}


@router.post("/checkout")
async def checkout(body: CheckoutRequest):
    """Simulated checkout."""
    order_id = f"ORD-{random.randint(100000, 999999)}"
    return {
        "order_id": order_id,
        "status": "confirmed",
        "items": len(body.cart_items),
        "message": "Order placed successfully.",
    }
