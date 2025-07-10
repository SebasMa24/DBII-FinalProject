"""
====================================================================================
  NexusBuy API - Main Application
====================================================================================

  Authors: 
            Luis Sebastian Martinez Guerrero
            Leidy Marcela Morales Segura  
  Class: Data Bases II - Final Project
  Date: July 2025 
  Objective: This FastAPI application serves as the main backend interface for the 
             NexusBuy system, integrating PostgreSQL (with Pgpool-II), MongoDB, 
             and Redis to manage users, products, orders, shipments, and payments 
             in a scalable and efficient e-commerce architecture.
====================================================================================
"""

# 1. Standard Python Imports
from datetime import datetime
from decimal import Decimal
import json
import re
from typing import Optional, List
import time

# 2. Third-Party Imports
from fastapi import FastAPI, HTTPException, Depends, Path, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

# 3. Local Project Imports
from config.config import db_settings
from database.postgres_adapter import PostgresAdapter
from database.mongo_adapter import MongoAdapter
from database.redis_adapter import RedisAdapter
from utils.logger import Logger
from models.Response import (
    UserResponse,
    AddressResponse,
    StoreResponse,
    CategoryResponse,
    QuestionResponse,
    AnswerResponse,
    OrderResponse,
    OrderDetailResponse,
    ShipmentResponse,
    PaymentResponse,
    ProductResponse,
    ProductBase,
)
from models.Request import (
    UserCreate,
    AddressCreate,
    OrderCreate,
    OrderDetailCreate,
    
)

# FastAPI App Configuration
app = FastAPI(
    title="NexusBuy API",
    description="API for NexusBuy system using PostgreSQL, Pgpool-II, MongoDB, and Redis",
    version="1.0.0"
)

# Enable CORS Middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global connection objects
postgres_adapter = PostgresAdapter()
mongo_client = MongoAdapter()
redis_pool = RedisAdapter()

# Logger instance for system-wide logging
logger = Logger()

@app.on_event("startup")
def startup():
    """Initialize database connections on application startup."""
    # Connect to PostgreSQL
    try:
        postgres_adapter.connect()
        print("PostgreSQL adapter connected")
    except Exception as e:
        print(f"Error connecting PostgreSQL adapter: {e}")
        raise
    # Connect to MongoDB
    try:
        mongo_client.connect()
        print("MongoDB adapter connected")
    except Exception as e:
        print(f"Error connecting Mongo adapter: {e}")
        raise
    # Connect to Redis
    try:
        redis_pool.connect()
        print("Redis adapter connected")
    except Exception as e:
        print(f"Error connecting Redis adapter: {e}")
        raise

@app.on_event("shutdown")
def shutdown():
    """
    Event triggered when the FastAPI application is shutting down.

    This function ensures that all active service connections 
    are gracefully closed before the application terminates.

    Responsibilities:
    - Disconnects from PostgreSQL using PostgresAdapter.
    - Disconnects from MongoDB using MongoAdapter.
    - Disconnects from Redis using RedisAdapter.
    - Logs a message to confirm successful disconnection.

    This prevents potential connection leaks or resource issues
    when the application restarts or shuts down.
    """
    postgres_adapter.disconnect()
    mongo_client.disconnect()
    redis_pool.disconnect()
    print("All connections closed")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log incoming HTTP requests.

    This asynchronous function intercepts every HTTP request to:
    - Extract endpoint path, HTTP method, and query parameters.
    - Log the request body for POST and PUT methods.
    - Log the query parameters for GET and DELETE methods.
    - Pass the request to the next handler in the middleware chain.

    Args:
        request (Request): The incoming HTTP request.
        call_next (Callable): Function to process the request and return a response.

    Returns:
        Response: The HTTP response returned by the next handler.
    """
    endpoint = request.url.path
    method = request.method
    params = dict(request.query_params)

    if method in ("POST", "PUT"):
        body = await request.body()
        body_str = body.decode("utf-8")
        logger.log_request(endpoint, method, body_str)
    else:
        logger.log_request(endpoint, method, params)

    response = await call_next(request)
    return response

@app.get("/stores/sales-ranking", tags=["Analytics"])
def get_store_sales_ranking(region: str = Query(...)):
    """
    Returns the sales ranking of stores based on total product sales in a given region.
    The result is cached in Redis for 1 month (30 days) to improve performance.

    Parameters:
    ----------
    region : str
        The geographical region to filter the sales data.

    Returns:
    --------
    dict:
        {
            "source": "redis" | "postgresql",
            "region": str,
            "cached_at": str (ISO timestamp, only if from PostgreSQL),
            "data": List[dict]
        }
    """
    start_time = time.time()
    cache_key = f"store_sales_ranking:{region}"
    ttl_seconds = 60 * 60 * 24 * 30  # 30 days

    if redis_pool.key_exists(cache_key):
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return {
            "source": "redis",
            "region": region,
            "data": redis_pool.get_value(cache_key)
        }
    print(f"[Redis] Cache miss for key: {cache_key}")
    query = """
        SELECT
    s.id,
    s.name AS store,
    SUM(od.unit_price * od.quantity) AS store_sales
FROM orderprocessing.orderdetails od
JOIN productcatalog.products p 
    ON od.product_id = p.id AND od.region = p.region
JOIN sellermanagement.stores s 
    ON p.store_id = s.id AND p.region = s.region
WHERE od.region = :region
GROUP BY s.id, s.name
ORDER BY store_sales DESC
LIMIT 10;
    """

    result = postgres_adapter.execute_raw(query, params={"region": region})
    print(f"[PostgreSQL] Query executed for region: {region}")
    # 🔁 Convert all Decimal values recursively before storing in Redis
    def convert_decimals(obj):
        if isinstance(obj, list):
            return [convert_decimals(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj

    result = convert_decimals(result)

    now_iso = datetime.now().isoformat()
    redis_pool.set_value(cache_key, result, ttl=ttl_seconds)
    redis_pool.set_value(f"{cache_key}:timestamp", now_iso, ttl=ttl_seconds)

    duration = time.time() - start_time
    print(f"Query executed in {duration:.4f} seconds [postgresql]")
    return {
        "source": "postgresql",
        "region": region,
        "cached_at": now_iso,
        "data": result
    }


@app.get("/shipments/delivery-times", tags=["Analytics"])
def get_delivery_times(region: str = Query(..., description="Region to filter deliveries")):
    """
    Returns delivery time distributions in hours for completed shipments in the given region.
    Results are cached in Redis for 30 days.
    
    Parameters:
    -----------
    region : str
        Region identifier.
    
    Returns:
    --------
    dict
        {
            "source": "redis" | "postgresql",
            "cached_at": "...",
            "data": [...]
        }
    """
    start_time = time.time()
    cache_key = f"delivery_times:{region}"
    ttl_seconds = 60 * 60 * 24 * 30  # 30 days

    if redis_pool.key_exists(cache_key):
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds [redis]")
        return {
            "source": "redis",
            "region": region,
            "data": redis_pool.get_value(cache_key)
        }

    query = """
    SELECT
    EXTRACT(EPOCH FROM (delivered_at::timestamp - shipped_at::timestamp)) / 3600 AS delivery_hours,
    COUNT(*) AS shipments
FROM shippinglogistic.shipments
WHERE delivered_at IS NOT NULL
  AND region = :region
GROUP BY 1
ORDER BY delivery_hours;
"""

    result = postgres_adapter.execute_raw(query, {"region": region})

    # Convert Decimal -> float
    def convert_decimals(obj):
        if isinstance(obj, list):
            return [convert_decimals(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, Decimal):
            return float(obj)
        return obj

    result = convert_decimals(result)
    now_iso = datetime.now().isoformat()

    redis_pool.set_value(cache_key, result, ttl=ttl_seconds)
    redis_pool.set_value(f"{cache_key}:timestamp", now_iso, ttl=ttl_seconds)

    duration = time.time() - start_time
    print(f"Query executed in {duration:.4f} seconds [postgresql]")
    return {
        "source": "postgresql",
        "region": region,
        "cached_at": now_iso,
        "data": result
    }

@app.get("/popular-products", tags=["Analytics"])
def get_popular_products(region: str = Query(...)):
    """
    Retrieves the 5 most popular products in a specific region over the last 30 days.

    Data is initially retrieved from Redis if cached. If not cached, the data is fetched 
    from PostgreSQL, enriched with product images and discount information from MongoDB, 
    then stored in Redis for future fast access.

    Parameters:
    ----------
    region : str
        The geographical region to filter the most sold products.

    Workflow:
    ---------
    1. Construct a Redis cache key using the region.
    2. Check if cached data exists:
        - If yes, return cached data as the response (source: redis).
    3. If not cached:
        - Query PostgreSQL to aggregate product sales in the last 30 days.
        - Use MongoDB to fetch image URLs and discount metadata.
        - Calculate discounted prices (if applicable).
        - Assemble the enriched response with title, prices, total sold, and images.
        - Cache the result and timestamp in Redis (TTL: 24 hours).
    4. Return the enriched product list with metadata (source: postgresql).

    Returns:
    --------
    dict:
        {
            "source": "redis" | "postgresql",
            "region": str,
            "cached_at": str (ISO timestamp, only if from PostgreSQL),
            "data": List[dict]
        }
    """
    start_time = time.time()
    cache_key = f"popular_products:{region}"

    if redis_pool.key_exists(cache_key):
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return {
            "source": "redis",
            "region": region,
            "data": redis_pool.get_value(cache_key)
        }

    query = f"""
    SELECT 
        p.id, 
        p.title,
        p.price,
        od.region,
        SUM(od.quantity) AS total_sold
    FROM orderprocessing.orderDetails od
    JOIN productcatalog.products p 
        ON od.product_id = p.id AND od.region = p.region
    JOIN orderprocessing.orders o 
        ON od.order_id = o.id AND od.region = o.region
    WHERE od.region = :region
        AND o.created_at >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY p.id, p.title, p.price, od.region
    ORDER BY total_sold DESC
    LIMIT 5;
    """

    result = postgres_adapter.execute_raw(query, params={"region": region})
    result_with_images = []
    for product in result:
        product_id = product["id"]
        doc = mongo_client.find_one("products", {"_id": product_id, "region": region})
        first_image = None
        if doc and isinstance(doc.get("images"), list) and doc["images"]:
            first_image = doc["images"][0].get("url")

        price = product["price"]
        discounted_price = price

        if doc and "discount" in doc:
            discount = doc["discount"]
        if discount.get("isActive"):
            percentage = discount.get("percentage", 0)
            discounted_price = int(price * (1 - percentage / 100))

        result_with_images.append({
            "id": product["id"],
            "title": product["title"],
            "price": product["price"],
            "discounted_price": discounted_price,
            "total_sold": product["total_sold"],
            "image": first_image
        })

    redis_pool.set_value(cache_key, result_with_images, ttl=86400)
    redis_pool.set_value(f"{cache_key}:timestamp", datetime.now().isoformat(), ttl=86400)
    duration = time.time() - start_time
    print(f"Query executed in {duration:.4f} seconds")
    return {
        "source": "postgresql",
        "cached_at": datetime.now().isoformat(),
        "region": region,
        "data": result_with_images
    }

@app.delete("/cache/delivery-times", tags=["Cache"])
def clear_all_delivery_times_cache():
    """
    Deletes cached delivery time data for all regions.

    This endpoint clears all Redis cache entries that store the delivery time analysis 
    for completed shipments across all regions.

    Returns:
    --------
    dict:
        {
            "message": "Cache cleared for all regions"
        }
    """
    start_time = time.time()

    # Get all delivery time cache keys (including timestamps)
    keys = redis_pool.client.keys("delivery_times:*")

    if keys:
        redis_pool.client.delete(*keys)

    duration = time.time() - start_time
    print(f"Cache deletion executed in {duration:.4f} seconds")

    return {"message": "Cache cleared for all regions"}

@app.delete("/cache/popular-products", tags=["Cache"])
def clear_popular_cache():
    """
    Deletes cached popular product data for all regions.

    This endpoint is used to manually clear the Redis cache entries related to 
    the most sold products across regions. It is typically used for cache invalidation 
    during admin operations or testing.

    Workflow:
    ---------
    1. Define the base cache key (`popular_products`).
    2. Remove both:
        - The cached product data.
        - The timestamp metadata.
    3. Log and return a confirmation message.

    Returns:
    --------
    dict:
        {
            "message": "Cache cleared for all regions"
        }
    """
    start_time = time.time()
    cache_key = f"popular_products"
    redis_pool.delete("popular_products")
    redis_pool.delete(f"{cache_key}:timestamp")
    duration = time.time() - start_time
    print(f"Query executed in {duration:.4f} seconds")
    return {"message": f"Caché eliminado para la todas las regiones"}

@app.delete("/cache/store-sales", tags=["Cache"])
def clear_store_sales_cache():
    """
    Deletes cached store sales ranking data.

    This is typically used by admins or during testing to clear Redis entries 
    associated with store-level aggregated sales.

    Returns:
    --------
    dict:
        {
            "message": "Cache cleared for store sales ranking"
        }
    """
    start_time = time.time()
    cache_key = f"store_sales_ranking"

    redis_pool.delete("store_sales_ranking")
    redis_pool.delete(f"{cache_key}:timestamp")

    print(f"[Redis] Cache cleared in {time.time() - start_time:.4f} seconds")
    return {
        "message": "Cache cleared for store sales ranking"
    }

@app.post("/users/", response_model=UserResponse, tags=["Users"])
def create_user(user: UserCreate):
    """
    Create a new user account in the system.

    This endpoint receives user data and stores a new user record 
    in the PostgreSQL database with default role assignment (role_id = 1).

    Parameters:
    -----------
    user : UserCreate
        A request body containing user attributes:
        - name (str): User's full name.
        - email (str): User's email address.
        - password (str): Plaintext password (hashed elsewhere, if needed).
        - phone (str): Contact phone number.
        - birthday (str): Date of birth in "YYYY-MM-DD" format.
        - region (str): Geographical region.

    Processing:
    -----------
    - Converts the birthday string to a `datetime` object.
    - Records the current timestamp as `created_at`.
    - Inserts the new user record into the `usermanagement.users` table.
    - Returns a user summary including the new `id`, `name`, `email`, `region`, and `created_at`.

    Returns:
    --------
    UserResponse (JSON):
        {
            "id": <int>,
            "name": <str>,
            "email": <str>,
            "region": <str>,
            "created_at": <datetime>
        }

    Raises:
    -------
    - HTTP 400: If the `birthday` format is invalid.
    - HTTP 500: If any other database error occurs.
    """
    start_time = time.time()
    try:
        from datetime import datetime
        birthday = datetime.strptime(user.birthday, "%Y-%m-%d")
        created_at = datetime.now()
        
        user_data = {
            "role_id": 1,
            "name": user.name,
            "email": user.email,
            "password": user.password,
            "phone": user.phone,
            "birthday": birthday,
            "region": user.region,
            "created_at": created_at
        }
        
        user_id = postgres_adapter.insert(
            table="usermanagement.users",
            data=user_data
        )
        
        return UserResponse(
            id=user_id,
            name=user.name,
            email=user.email,
            region=user.region,
            created_at=created_at
        )
    except ValueError as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/addresses/", response_model=AddressResponse, tags=["Addresses"])
def create_address(address: AddressCreate):
    """
    Create a new address for a user.

    This endpoint registers a new address linked to an existing user in a specified region.

    Parameters:
    -----------
    address : AddressCreate
        A request body containing:
        - user_id (int): The ID of the user to whom the address belongs.
        - address (str): Street or detailed address.
        - city (str): City name.
        - zipcode (str): Postal code.
        - country (str): Country name.
        - region (str): Region associated with the user and address.

    Processing:
    -----------
    - Verifies that the user exists and belongs to the specified region.
    - If validation passes, inserts the address into the `usermanagement.address` table.
    - Retrieves the inserted address and returns it as a structured response.

    Returns:
    --------
    AddressResponse (JSON):
        {
            "id": <int>,
            "user_id": <int>,
            "address": <str>,
            "city": <str>,
            "zipcode": <str>,
            "country": <str>,
            "region": <str>
        }

    Raises:
    -------
    - HTTP 404: If the user is not found or the region does not match.
    - HTTP 500: For any database-related error.
    """
    start_time = time.time()
    try:
        # Verificar que el usuario existe en la región
        user = postgres_adapter.get_by_id("usermanagement.users", address.user_id)
        if not user or user.get("region") != address.region:
            raise HTTPException(
                status_code=404,
                detail="User not found in the specified region"
            )
        
        address_id = postgres_adapter.insert(
            table="usermanagement.address",
            data={
                "user_id": address.user_id,
                "address": address.address,
                "city": address.city,
                "zipcode": address.zipcode,
                "country": address.country,
                "region": address.region
            }
        )
        
        new_address = postgres_adapter.get_by_id(
            table="usermanagement.address",
            id=address_id
        )
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return AddressResponse(**new_address)
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/users/{user_id}/addresses", response_model=List[AddressResponse], tags=["Users"])
def get_user_addresses(user_id: int, region: str):
    """
    Retrieve all addresses for a specific user within a given region.

    This endpoint fetches the list of addresses registered to a specific user,
    validating that the user exists and belongs to the requested region.

    Parameters:
    -----------
    user_id : int (path)
        The ID of the user whose addresses are being requested.
    
    region : str (query)
        The region to which the user must belong.

    Processing:
    -----------
    - Validates that the user exists and belongs to the specified region.
    - Queries the `usermanagement.address` table for all matching addresses.
    - Returns the list of addresses ordered by most recently created.

    Returns:
    --------
    List[AddressResponse] (JSON):
        A list of address objects with the following fields:
        - id (int)
        - user_id (int)
        - address (str)
        - city (str)
        - zipCode (str)
        - region (str)

    Raises:
    -------
    - HTTP 404: If the user does not exist or does not belong to the specified region.
    - HTTP 500: If a database or query execution error occurs.
    """
    start_time = time.time()
    try:
        # Verificar que el usuario existe y pertenece a la región
        user = postgres_adapter.get_by_id("usermanagement.users", user_id)
        if not user or user.get("region") != region:
            raise HTTPException(status_code=404, detail="User not found in the specified region")
        
        # Consulta optimizada
        query = """
            SELECT user_id, id, address, city, zipCode, region
            FROM usermanagement.address
            WHERE user_id = :user_id AND region = :region
            ORDER BY id DESC
        """
        addresses = postgres_adapter.execute_raw(
            query,
            {"user_id": user_id, "region": region}
        )
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return [AddressResponse(**addr) for addr in addresses]
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/addresses/{address_id}", response_model=AddressResponse, tags=["Addresses"])
def get_address(address_id: int, region: str):
    """
    Retrieve a specific address by ID and region.

    This endpoint returns the details of a single address if it exists and 
    belongs to the specified region.

    Parameters:
    -----------
    address_id : int (path)
        The ID of the address to retrieve.
    
    region : str (query)
        The region that the address must belong to.

    Processing:
    -----------
    - Fetches the address by ID from the `usermanagement.address` table.
    - Validates that the address exists and matches the provided region.

    Returns:
    --------
    AddressResponse (JSON):
        An object containing the address information:
        - id (int)
        - user_id (int)
        - address (str)
        - city (str)
        - zipCode (str)
        - region (str)

    Raises:
    -------
    - HTTP 404: If the address does not exist or does not match the region.
    - HTTP 500: If a database or query execution error occurs.
    """
    start_time = time.time()
    try:
        address = postgres_adapter.get_by_id(
            table="usermanagement.address",
            id=address_id
        )
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")
        if address.get("region") != region:
            raise HTTPException(
                status_code=404,
                detail="Address not found in the specified region"
            )
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return AddressResponse(**address)
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.get("/stores/{store_id}", response_model=StoreResponse, tags=["Stores"])
def get_store(store_id: int, region: str):
    """
    Retrieve store details by ID and region.

    This endpoint fetches detailed information about a specific store,
    validating that it belongs to the specified region.

    Parameters:
    -----------
    store_id : int (path)
        The ID of the store to retrieve.

    region : str (query)
        The region the store must belong to.

    Processing:
    -----------
    - Uses a helper method `get_by_id_with_region` to retrieve the store 
      from the `sellermanagement.stores` table by ID and region.
    - If no store is found matching both conditions, a 404 error is raised.

    Returns:
    --------
    StoreResponse (JSON):
        A structured object with the store's data, including:
        - id (int)
        - name (str)
        - description (str)
        - region (str)
        - created_at (datetime)

    Raises:
    -------
    - HTTP 404: If the store doesn't exist or does not match the region.
    - HTTP 500: On database connection or execution failure.
    """
    start_time = time.time()
    try:
        store = postgres_adapter.get_by_id_with_region(
            table="sellermanagement.stores",
            id=store_id,
            region=region
        )
        if not store:
            duration = time.time() - start_time
            print(f"Query executed in {duration:.4f} seconds")
            raise HTTPException(status_code=404, detail="Store not found in the specified region")
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return StoreResponse(**store)

    except HTTPException:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.get("/stores/{store_id}/products", response_model=List[ProductBase], tags=["Stores"])
def get_store_products(store_id: int, region: str, page: int = 1, per_page: int = 20):
    """
    Retrieve paginated list of products for a specific store in a given region.

    This endpoint returns a paginated list of products associated with a specific store
    and region. It supports pagination via `page` and `per_page` query parameters.

    Parameters:
    -----------
    store_id : int (path)
        The ID of the store whose products are to be retrieved.

    region : str (query)
        The region to which the store belongs.

    page : int = 1 (query, optional)
        The page number for pagination (default is 1).

    per_page : int = 20 (query, optional)
        The number of products to return per page (default is 20).

    Processing:
    -----------
    - Calculates the `OFFSET` based on the page number and page size.
    - Executes a parameterized SQL query to retrieve products from 
      the `productcatalog.products` table that match the store and region.
    - Sorts the results by creation date in descending order.

    Returns:
    --------
    List[ProductBase] (JSON):
        A list of product objects, each containing:
        - id (int)
        - title (str)
        - description (str)
        - price (float)
        - stock (int)
        - region (str)
        - created_at (datetime)

    Raises:
    -------
    - HTTP 500: On database connection or execution failure.
    """
    start_time = time.time()
    try:
        offset = (page - 1) * per_page
        query = """
            SELECT p.id, p.title, p.description, p.price, p.stock, p.region, p.created_at
            FROM productcatalog.products p
            WHERE p.store_id = :store_id AND p.region = :region
            ORDER BY p.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        
        products = postgres_adapter.execute_raw(
            query,
            {
                "store_id": store_id,
                "region": region,
                "limit": per_page,
                "offset": offset
            }
        )
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return [ProductBase(**prod) for prod in products]
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {str(e)}"
        )

@app.get("/products", tags=["Products"])
def get_products(region: str,limit: int = Query(10, ge=1, le=100), skip: int = 0):
    """
    Retrieve a list of products from the MongoDB collection based on region, with pagination.

    This endpoint fetches products stored in the MongoDB `products` collection, filtered by a specific region.
    It supports pagination through `limit` and `skip` query parameters.

    Parameters:
    -----------
    region : str (query, required)
        The region to filter products by.

    limit : int = 10 (query, optional)
        Maximum number of products to return (min: 1, max: 100).

    skip : int = 0 (query, optional)
        Number of products to skip (used for pagination).

    Processing:
    -----------
    - Builds a filter query using the specified region.
    - Executes a `find_many` operation on the MongoDB collection `products`.
    - Applies `limit` and `skip` for paginated results.

    Returns:
    --------
    JSONResponse:
        A list of product documents from MongoDB, filtered by region and paginated.

    Raises:
    -------
    - HTTP 500: On database or query execution failure.
    """
    start_time = time.time()
    try:
        filters = { "region": region }
        products = mongo_client.find_many(
            collection="products",
            filter_query=filters,
            limit=limit,
            skip=skip
        )
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return JSONResponse(content=products)
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/users/{user_id}/orders", tags=["Users"])
def get_user_orders(user_id: int, region: str, status: Optional[str] = None, page: int = 1, per_page: int = 10):
    """
    Retrieve a paginated list of orders placed by a specific user, optionally filtered by shipment status.

    This endpoint verifies the user's existence in the given region, and then retrieves the user's orders
    along with associated shipment and payment status. Pagination and optional shipment status filtering are supported.

    Parameters:
    -----------
    user_id : int (path, required)
        The unique ID of the user.

    region : str (query, required)
        The region to which the user belongs.

    status : str (query, optional)
        Filter by shipment status name (e.g., "Delivered", "Pending", etc.).

    page : int = 1 (query, optional)
        Page number for paginated results (default: 1).

    per_page : int = 10 (query, optional)
        Number of records to return per page (default: 10).

    Processing:
    -----------
    - Validates the user exists and belongs to the specified region.
    - Constructs an SQL query that joins orders with shipment and payment information.
    - Applies optional filter for shipment status if provided.
    - Supports pagination via `LIMIT` and `OFFSET`.

    Returns:
    --------
    List[Dict]:
        A list of orders containing:
        - Order ID
        - User ID
        - Coupon ID
        - Total Price
        - Created Date
        - Shipment Status (if available)
        - Payment Method (if available)

    Raises:
    -------
    - HTTP 404: If the user is not found in the specified region.
    - HTTP 500: If a database error occurs during query execution.
    """
    start_time = time.time()
    try:
        # Verificar que el usuario existe en la región
        user = postgres_adapter.get_by_id("usermanagement.users", user_id)
        if not user or user.get("region") != region:
            raise HTTPException(status_code=404, detail="User not found in the specified region")
        
        # Consulta optimizada con filtro opcional
        offset = (page - 1) * per_page
        base_query = """
            SELECT 
                o.id, 
                o.user_id, 
                o.coupon_id, 
                o.total_price, 
                o.created_at, 
                s.status_name AS shipment_status,
                p.method_name AS payment_method
            FROM orderprocessing.orders o
            LEFT JOIN shippinglogistic.shipments sh 
                ON o.id = sh.order_id 
            LEFT JOIN shippinglogistic.shipmentstatuses s 
                ON sh.shipment_status_id = s.id
            LEFT JOIN paymentmanagement.payments pm 
                ON o.id = pm.order_id 
            LEFT JOIN paymentmanagement.paymentmethod p 
                ON pm.payment_method_id = p.id
            WHERE o.user_id = :user_id AND o.region = :region
        """
        
        params = {
            "user_id": user_id,
            "region": region,
            "limit": per_page,
            "offset": offset
        }
        
        if status:
            base_query += " AND s.status_name = :status"
            params["status"] = status
        
        base_query += " ORDER BY o.created_at DESC LIMIT :limit OFFSET :offset"
        
        orders = postgres_adapter.execute_raw(base_query, params)
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return orders
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    

@app.get("/stores/{store_id}/orders", tags=["Stores"])
def get_store_orders(
    store_id: int, 
    region: str, 
):
    """
    Retrieve all orders associated with a specific store in a given region, including shipment and payment status
    as well as detailed product-level information.

    This endpoint first verifies that the store exists in the specified region. It then performs an optimized
    SQL query that aggregates order data with related shipment and payment details, along with associated
    products per order. Orders are returned in ascending order by ID.

    Parameters:
    -----------
    store_id : int (path, required)
        The unique identifier of the store.

    region : str (query, required)
        The region the store is located in.

    Returns:
    --------
    List[Dict]:
        A list of orders including:
        - Order ID, User ID, Total Price, Creation Date
        - Shipment ID, Status ID, and Status Name
        - Payment ID, Status ID, and Status Name
        - List of product details (product_id, product_name, quantity, price_per_unit)

    Raises:
    -------
    - HTTP 404: If the store is not found in the specified region.
    - HTTP 500: If a database error occurs during execution.
    """
    start_time = time.time()
    try:
        # Verificación rápida de existencia de tienda en región
        store_exists = postgres_adapter.execute_raw(
            """
            SELECT 1 
            FROM sellermanagement.stores 
            WHERE id = :store_id AND region = :region
            """,
            {"store_id": store_id, "region": region}
        )
        if not store_exists:
            raise HTTPException(status_code=404, detail="Store not found in the specified region")

        # Consulta optimizada con paginación basada en cursor
        query = """
            WITH order_base AS (
    SELECT 
        o.id AS order_id,
        o.user_id,
        o.total_price,
        o.created_at,
        o.region,
        s.id AS shipment_id,
        s.shipment_status_id,
        ss.status_name AS shipment_status,
        pm.id AS payment_id,
        pm.payment_status_id,
        ps.status_name AS payment_status
    FROM orderprocessing.orders o
    JOIN shippinglogistic.shipments s ON o.id = s.order_id AND o.region = s.region
    JOIN shippinglogistic.shipmentstatuses ss ON s.shipment_status_id = ss.id
    JOIN paymentmanagement.payments pm ON o.id = pm.order_id AND o.region = pm.region
    JOIN paymentmanagement.paymentstatuses ps ON pm.payment_status_id = ps.id
    WHERE EXISTS (
        SELECT 1
        FROM orderprocessing.orderdetails od
        JOIN productcatalog.products p ON od.product_id = p.id AND od.region = p.region
        WHERE od.order_id = o.id
          AND p.store_id = :store_id
    )
    AND o.region = :region
    ORDER BY o.id ASC
)
SELECT 
    ob.*,
    json_agg(json_build_object(
        'product_id', p.id,
        'product_name', p.title,
        'quantity', od.quantity,
        'price_per_unit', od.unit_price
    )) AS order_details
FROM order_base ob
JOIN orderprocessing.orderdetails od ON ob.order_id = od.order_id AND ob.region = od.region
JOIN productcatalog.products p ON od.product_id = p.id AND od.region = p.region
GROUP BY 
    ob.order_id, 
    ob.user_id, 
    ob.total_price, 
    ob.created_at, 
    ob.region,
    ob.shipment_id,
    ob.shipment_status_id,
    ob.shipment_status,
    ob.payment_id,
    ob.payment_status_id,
    ob.payment_status
ORDER BY ob.order_id ASC;
        """

        params = {
            "store_id": store_id,
            "region": region,
        }

        print(f"Executing paginated order query with params: {params}")
        orders = postgres_adapter.execute_raw(query, params)

        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")

        return orders

    except Exception as e:
        duration = time.time() - start_time
        print(f"Error after {duration:.4f} seconds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/products/categories/", response_model=List[CategoryResponse], tags=["Products"])
def get_categories():
    """
    Retrieve the full list of product categories available in the catalog.

    This endpoint queries the `productcatalog.categories` table in PostgreSQL to return all
    available product categories, including their ID and name. It's useful for populating dropdowns
    or filters in user interfaces.

    Returns:
    --------
    List[CategoryResponse]:
        A list of category objects, each containing:
        - id (int): Unique category identifier
        - name (str): Category name
        - region (str): Associated region, if applicable

    Raises:
    -------
    - HTTP 500: If a database error occurs during query execution.
    """
    start_time = time.time()
    try:
        categories = postgres_adapter.get_all(
            table="productcatalog.categories"
        )
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return [CategoryResponse(**cat) for cat in categories]
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    

@app.get("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
def get_product(product_id: int, region: str):
    """
    Retrieve detailed product information, including relational and NoSQL data.

    This endpoint fetches a single product's data by its ID and region. It combines:
    - Core product details from PostgreSQL (title, description, price, stock, store, category).
    - Associated category and store metadata.
    - Image URLs and discount details from MongoDB.

    Parameters:
    -----------
    - product_id (int): Unique product identifier.
    - region (str): Region code used to scope the product search.

    Returns:
    --------
    ProductResponse:
        A structured response including:
        - Basic product data (title, description, price, stock, created_at).
        - Store and category information.
        - Active discounts (if any), with dynamically calculated `discounted_price`.
        - List of image URLs.
        - Placeholder for review stats (currently set to zero).

    Raises:
    -------
    - HTTP 404: If the product is not found in the specified region.
    - HTTP 500: If a database or MongoDB error occurs.
    """
    start_time = time.time()
    try:
        # --- Consulta principal solo desde PostgreSQL (sin imágenes ni descuentos) ---
        query = """
            SELECT 
                p.id, p.title, p.description, p.price, p.stock, p.region, p.created_at,
                c.id AS category_id, c.name AS category_name, c.description AS category_description,
                s.id AS store_id, s.name AS store_name, s.is_official AS store_is_official
            FROM productcatalog.products p
            JOIN productcatalog.categories c ON p.categorie_id = c.id
            JOIN sellermanagement.stores s ON p.store_id = s.id
            WHERE p.id = :product_id AND p.region = :region
        """

        result = postgres_adapter.execute_raw(
            query,
            {"product_id": product_id, "region": region}
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Producto no encontrado en la región especificada"
            )

        product = result[0]

        # --- Cargar datos desde MongoDB: imágenes y descuentos ---
        mongo_doc = mongo_client.find_one("products", {"_id": product_id, "region": region})

        # Imágenes desde Mongo
        images = []
        if mongo_doc and isinstance(mongo_doc.get("images"), list):
            images = [{"id": idx, "url": img.get("url")} for idx, img in enumerate(mongo_doc["images"]) if img.get("url")]

        # Descuento desde Mongo
        active_discounts = []
        discounted_price = product["price"]

        if mongo_doc and "discount" in mongo_doc:
            discount = mongo_doc["discount"]
            now = datetime.now().date()

            if (
                discount.get("isActive") and
                "start_date" in discount and
                "end_date" in discount and
                datetime.fromisoformat(discount["start_date"]).date() <= now <= datetime.fromisoformat(discount["end_date"]).date()
            ):
                active_discounts.append(discount)
                percentage = discount.get("percentage", 0)
                discounted_price = int(product["price"] * (1 - percentage / 100))

        # --- Construcción de objetos anidados ---
        category = CategoryResponse(
            id=product["category_id"],
            name=product["category_name"],
            description=product["category_description"]
        )

        store = StoreResponse(
            id=product["store_id"],
            name=product["store_name"],
            is_official=product["store_is_official"]
        )
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return ProductResponse(
            id=product["id"],
            title=product["title"],
            description=product["description"],
            price=product["price"],
            discounted_price=discounted_price,
            stock=product["stock"],
            region=product["region"],
            created_at=product["created_at"],
            category=category,
            store=store,
            images=images,
            active_discounts=active_discounts,
            review_stats = {"average_rating": 0.0, "total_reviews": 0}
        )

    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    
@app.get("/questions/{product_id}")
def get_question_by_product(
    product_id: int = Path(..., example=48263, description="Product ID to search question for"),
    region: str = Query(..., example="Colombia", description="Region to filter the question (e.g., 'Mexico')")
):
    """
    Retrieve a question document by product_id and region from the 'Q&A' collection.

    Parameters:
        product_id (int): The ID of the product for which the question was asked.
        region (str): The region to filter the question.

    Returns:
        dict: The question document with question and answer.

    Raises:
        HTTPException: 404 if no matching question is found.
    """
    start_time = time.time()
    query = {
        "product_id": product_id,
        "region": region
    }

    question_doc = mongo_client.find_one("Q&A", query)
    if question_doc is None:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(
            status_code=404,
            detail=f"No question found for product_id {product_id} in region '{region}'"
        )
    duration = time.time() - start_time
    print(f"Query executed in {duration:.4f} seconds")
    return question_doc

@app.post("/orders/", response_model=OrderResponse, tags=["Orders"])
def create_order(order: OrderCreate):
    """
    Create a new order for a user.

    This endpoint inserts a new order into the system after validating that the user 
    exists in the specified region. It supports applying a coupon and stores the order 
    metadata, including the total price and timestamp.

    Parameters:
    -----------
    - order (OrderCreate): An object containing:
        - user_id (int): ID of the user placing the order.
        - coupon_id (Optional[int]): Applied coupon ID, if any.
        - total_price (float): Total value of the order.
        - region (str): Region where the order is placed.

    Returns:
    --------
    OrderResponse:
        A representation of the newly created order including order ID, user ID, coupon (if any),
        total price, region, and creation timestamp.

    Raises:
    -------
    - HTTP 404: If the user is not found in the specified region.
    - HTTP 500: On database or server errors.
    """
    start_time = time.time()
    try:
        # Verificar usuario en la región
        user = postgres_adapter.get_by_id(
            table="usermanagement.users",
            id=order.user_id
        )
        if not user or user.get("region") != order.region:
            raise HTTPException(
                status_code=404,
                detail="User not found in the specified region"
            )
        
        order_data = {
            "user_id": order.user_id,
            "coupon_id": order.coupon_id,
            "total_price": order.total_price,
            "region": order.region,
            "created_at": datetime.now()
        }
        
        order_id = postgres_adapter.insert(
            table="orderprocessing.orders",
            data=order_data
        )
        
        new_order = postgres_adapter.get_by_id(
            table="orderprocessing.orders",
            id=order_id
        )
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return OrderResponse(**new_order)
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.post("/order-details/", response_model=OrderDetailResponse, tags=["Orders"])
def create_order_detail(detail: OrderDetailCreate):
    """
    Create a new order detail (product added to a specific order).

    This endpoint verifies that both the order and the product exist 
    in the specified region before inserting a new order detail into 
    the `orderprocessing.orderDetails` table.

    Parameters
    ----------
    detail : OrderDetailCreate
        Pydantic model containing the order ID, product ID, quantity, 
        unit price, and region.

    Returns
    -------
    OrderDetailResponse
        A response model containing the created order detail information.

    Raises
    ------
    HTTPException
        - 404: If the order or product does not exist in the specified region.
        - 500: If a database error occurs during the insertion process.
    """
    start_time = time.time()
    try:
        # Verificar que orden y producto existen en la región
        order = postgres_adapter.get_by_id(
            table="orderprocessing.orders",
            id=detail.order_id
        )
        if not order or order.get("region") != detail.region:
            raise HTTPException(
                status_code=404,
                detail="Order not found in the specified region"
            )
        
        product = postgres_adapter.get_by_id(
            table="productcatalog.products",
            id=detail.product_id
        )
        if not product or product.get("region") != detail.region:
            raise HTTPException(
                status_code=404,
                detail="Product not found in the specified region"
            )
        
        detail_id = postgres_adapter.insert(
            table="orderprocessing.orderDetails",
            data={
                "order_id": detail.order_id,
                "product_id": detail.product_id,
                "quantity": detail.quantity,
                "unit_price": detail.unit_price,
                "region": detail.region
            }
        )
        
        new_detail = postgres_adapter.get_by_id(
            table="orderprocessing.orderDetails",
            id=detail_id
        )
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return OrderDetailResponse(**new_detail)
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.get("/orders/{order_id}/details", response_model=List[OrderDetailResponse], tags=["Orders"])
def get_order_details(order_id: int, region: str):
    """
    Retrieve all order details for a specific order in a given region.

    This endpoint checks whether the order exists in the specified region
    and returns the list of associated products (order details) such as 
    quantity and unit price.

    Parameters
    ----------
    order_id : int
        The ID of the order for which details are requested.

    region : str
        The region to which the order must belong.

    Returns
    -------
    List[OrderDetailResponse]
        A list of order detail records including product ID, quantity,
        unit price, and region.

    Raises
    ------
    HTTPException
        - 404: If the order does not exist in the specified region.
        - 500: If an internal server or database error occurs.
    """
    start_time = time.time()
    try:
        # Verificar que la orden existe en la región
        order = postgres_adapter.get_by_id(
            table="orderprocessing.orders",
            id=order_id
        )
        if not order or order.get("region") != region:
            raise HTTPException(
                status_code=404,
                detail="Order not found in the specified region"
            )
        
        print(f"Fetching details for order {order_id} in region {region}")
        details = postgres_adapter.get_all(
            table="orderprocessing.orderdetails",
            filters={
                "order_id": order_id,
                "region": region
            }
        )
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return [OrderDetailResponse(**det) for det in details]
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.post("/shipments/", response_model=ShipmentResponse, tags=["Shipments"])
def create_shipment(shipment: dict):
    """
    Create a new shipment record for an existing order.

    This endpoint validates that the referenced order exists and belongs
    to the specified region before creating the shipment in the
    `shippinglogistic.shipments` table.

    Parameters
    ----------
    shipment : dict
        A dictionary containing shipment data. Must include:
        - order_id (int): ID of the order to associate the shipment.
        - region (str): Region the shipment belongs to.
        - Other shipment-related fields as required by the schema.

    Returns
    -------
    ShipmentResponse
        An object representing the newly created shipment with full data.

    Raises
    ------
    HTTPException
        - 404: If the referenced order does not exist in the specified region.
        - 500: If an internal error occurs during insertion or retrieval.
    """
    start_time = time.time()
    try:
        # Verificar que la orden existe en la región
        order = postgres_adapter.get_by_id(
            table="orderprocessing.orders",
            id=shipment["order_id"]
        )
        if not order or order.get("region") != shipment["region"]:
            raise HTTPException(
                status_code=404,
                detail="Order not found in the specified region"
            )
        
        shipment_id = postgres_adapter.insert(
            table="shippinglogistic.shipments",
            data=shipment
        )
        
        new_shipment = postgres_adapter.get_by_id(
            table="shippinglogistic.shipments",
            id=shipment_id
        )
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return ShipmentResponse(**new_shipment)
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.post("/payments/", response_model=PaymentResponse, tags=["Payments"])
def create_payment(payment: dict):
    """
    Create a new payment record for an existing order.

    This endpoint validates that the specified order exists and belongs
    to the given region before inserting a new payment into the
    `paymentmanagement.payments` table.

    Parameters
    ----------
    payment : dict
        A dictionary containing payment information. Required fields include:
        - order_id (int): ID of the order associated with the payment.
        - region (str): Region where the payment is registered.
        - payment_method_id (int), payment_status_id (int), total_amount (float), etc.

    Returns
    -------
    PaymentResponse
        A serialized representation of the newly created payment record.

    Raises
    ------
    HTTPException
        - 404: If the specified order does not exist in the given region.
        - 500: If a database error occurs during insertion or retrieval.
    """
    start_time = time.time()
    try:
        # Verificar que la orden existe en la región
        order = postgres_adapter.get_by_id(
            table="orderprocessing.orders",
            id=payment["order_id"]
        )
        if not order or order.get("region") != payment["region"]:
            raise HTTPException(
                status_code=404,
                detail="Order not found in the specified region"
            )
        
        payment_id = postgres_adapter.insert(
            table="paymentmanagement.payments",
            data=payment
        )
        
        new_payment = postgres_adapter.get_by_id(
            table="paymentmanagement.payments",
            id=payment_id
        )
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return PaymentResponse(**new_payment)
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")



@app.get("/conversations/{order_id}")
def get_conversation_by_order(
    order_id: int = Path(..., example=1, description="Order ID to search the conversation for"),
    region: str = Query(..., example="Colombia", description="Region to filter the conversation")
):
    """
    Get a conversation document by its associated order_id and region
    from the 'conversations' collection.

    Parameters:
        order_id (int): The order ID to search the conversation for.
        region (str): The region to filter the conversation.

    Returns:
        dict: The conversation document if found.

    Raises:
        HTTPException: 404 if no conversation is found for the given order_id and region.
    """
    start_time = time.time()
    query = {
        "order_id": order_id,
        "region": region
    }

    conversation = mongo_client.find_one("conversations", query)
    if conversation is None:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(
            status_code=404,
            detail=f"No conversation found for order_id {order_id} in region '{region}'"
        )
    duration = time.time() - start_time
    print(f"Query executed in {duration:.4f} seconds")
    return conversation

@app.get("/recommendations/")
def get_recommendations_by_user(
    user_id: int = Query(..., example=1, description="User ID for which to fetch search-based recommendations"),
    region: str = Query(..., example="Colombia", description="Region to filter search history")
):
    """
    Generate search-based product recommendations for a user based on recent searches.

    Returns a list of products that match keywords from the user's recent search history.
    """
    start_time = time.time()
    # Obtener las últimas 5 búsquedas del usuario en esa región
    searches = mongo_client.find_many(
        collection="user_search_history",
        filter_query={"user_id": user_id, "region": region},
        sort={"date": -1},
        limit=5
    )

    if not searches:
        raise HTTPException(status_code=404, detail=f"No search history found for user_id {user_id} in region '{region}'")

    # Obtener las palabras clave de las búsquedas
    search_keywords = []
    for s in searches:
        if "search" in s:
            # Tokenizar cada término de búsqueda
            words = re.findall(r'\b\w+\b', s["search"].lower())
            search_keywords.extend(words)

    if not search_keywords:
        raise HTTPException(status_code=404, detail="No valid search keywords found.")

    # Crear patrón de búsqueda para MongoDB
    regex_filters = [{"title": {"$regex": word, "$options": "i"}} for word in search_keywords]
    description_filters = [{"description": {"$regex": word, "$options": "i"}} for word in search_keywords]
    combined_filters = {"$or": regex_filters + description_filters, "region": region}

    # Buscar productos que coincidan con alguna palabra clave
    matched_products = mongo_client.find_many(
        collection="products",
        filter_query=combined_filters,
        limit=50  # se puede ajustar o eliminar si se desea más de 5
    )

    if not matched_products:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(status_code=404, detail="No matching products found based on search history.")
    duration = time.time() - start_time
    print(f"Query executed in {duration:.4f} seconds")
    return {
        "user_id": user_id,
        "region": region,
        "keywords_used": list(set(search_keywords)),
        "recommended_products": matched_products[:5]  # retornar al menos 5
    }

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj