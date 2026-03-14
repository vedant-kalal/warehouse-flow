from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import (
    auth,
    products,
    categories,
    warehouses,
    locations,
    inventory,
    receipts,
    deliveries,
    transfers,
    adjustments,
    history,
    dashboard,
    search
)

app = FastAPI(
    title="CoreInventory API",
    version="1.0.0",
    description="Modular Inventory Management System"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(categories.router)
app.include_router(warehouses.router)
app.include_router(locations.router)
app.include_router(inventory.router)
app.include_router(receipts.router)
app.include_router(deliveries.router)
app.include_router(transfers.router)
app.include_router(adjustments.router)
app.include_router(history.router)
app.include_router(dashboard.router)
app.include_router(search.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "CoreInventory"}
