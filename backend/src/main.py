# 1. Importaciones estándar de Python
from datetime import datetime
from typing import Optional, List
import time

# 2. Importaciones de terceros
from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 3. Importaciones del proyecto local
from config.config import db_settings
from database.postgres_adapter import PostgresAdapter
from database.mongo_adapter import MongoAdapter
from database.redis_adapter import RedisAdapter
from utils.logger import Logger
from models.Response import (
    ReviewStatsResponse,
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
    SearchHistoryResponse,
    CampaignResponse,
    AdResponse,
    ProductResponse,
    ProductBase,
)
from models.Request import (
    UserCreate,
    AddressCreate,
    OrderCreate,
    OrderDetailCreate,
    
)

app = FastAPI(
    title="NexusBuy API",
    description="API para sistema NexusBuy con PostgreSQL, Pgpool-II, MongoDB y Redis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Objetos de conexión globales
postgres_adapter = PostgresAdapter()
mongo_client = MongoAdapter()
redis_pool = RedisAdapter()

#Objeto para loggs 
logger = Logger()

@app.on_event("startup")
def startup():
    # Conectar PostgreSQL
    try:
        postgres_adapter.connect()
        print("PostgreSQL adapter connected")
    except Exception as e:
        print(f"Error connecting PostgreSQL adapter: {e}")
        raise
    # Conectar MongoDB
    try:
        mongo_client.connect()
        print("MongoDB adapter connected")
    except Exception as e:
        print(f"Error connecting Mongo adapter: {e}")
        raise
    # Conectar Redis
    try:
        redis_pool.connect()
        print("Redis adapter connected")
    except Exception as e:
        print(f"Error connecting Redis adapter: {e}")
        raise

@app.on_event("shutdown")
def shutdown():
    postgres_adapter.disconnect()
    print("All connections closed")

@app.middleware("http")
async def log_requests(request: Request, call_next):
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

@app.get("/popular-products", tags=["Cache"])
def get_popular_products(region: str = Query(...)):
    start_time = time.time()
    cache_key = f"popular_products:{region}"

    if redis_pool.key_exists(cache_key):
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

@app.delete("/cache/popular-products", tags=["Cache"])
def clear_popular_cache():
    start_time = time.time()
    cache_key = f"popular_products"
    redis_pool.delete("popular_products")
    redis_pool.delete(f"{cache_key}:timestamp")
    duration = time.time() - start_time
    print(f"Query executed in {duration:.4f} seconds")
    return {"message": f"Caché eliminado para la todas las regiones"}

@app.post("/users/", response_model=UserResponse, tags=["Users"])
def create_user(user: UserCreate):
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

@app.get("/users/{user_id}/orders", response_model=List[OrderResponse], tags=["Users"])
def get_user_orders(user_id: int, region: str, status: Optional[str] = None, page: int = 1, per_page: int = 10):
    start_time = time.time()
    try:
        # Verificar que el usuario existe en la región
        user = postgres_adapter.get_by_id("usermanagement.users", user_id)
        if not user or user.get("region") != region:
            raise HTTPException(status_code=404, detail="User not found in the specified region")
        
        # Consulta optimizada con filtro opcional
        offset = (page - 1) * per_page
        base_query = """
            SELECT o.id, o.user_id, o.coupon_id, o.total_price, o.created_at, o.region,
                s.status_name AS shipment_status,
                p.method_name AS payment_method
            FROM orderprocessing.orders o
            LEFT JOIN shippinglogistic.shipments sh ON o.id = sh.order_id AND o.region = sh.region
            LEFT JOIN shippinglogistic.shipmentstatuses s ON sh.shipment_status_id = s.id
            LEFT JOIN paymentmanagement.payments pm ON o.id = pm.order_id AND o.region = pm.region
            LEFT JOIN paymentmanagement.paymentmethod p ON pm.payment_method_id = p.id
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
        return [OrderResponse(**order) for order in orders]
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    

@app.get("/stores/{store_id}/orders", response_model=List[OrderResponse], tags=["Stores"])
def get_store_orders(store_id: int, region: str, period: str = "30d", page: int = 1, per_page: int = 20):
    start_time = time.time()
    try:
        # Verificar que la tienda existe en la región
        store = postgres_adapter.get_by_id("sellermanagement.stores", store_id)
        if not store or store.get("region") != region:
            raise HTTPException(status_code=404, detail="Store not found in the specified region")
        
        # Calcular fecha de inicio según el período
        from datetime import datetime, timedelta
        today = datetime.now()
        
        if period == "7d":
            start_date = today - timedelta(days=7)
        elif period == "90d":
            start_date = today - timedelta(days=90)
        else:  # 30d por defecto
            start_date = today - timedelta(days=30)
        
        # Consulta optimizada con filtro temporal
        offset = (page - 1) * per_page
        query = """
            SELECT DISTINCT o.id, o.user_id, o.total_price, o.created_at, o.region,
                   u.name AS user_name,
                   s.status_name AS shipment_status
            FROM orderprocessing.orders o
            JOIN orderprocessing.orderDetails od ON o.id = od.order_id AND o.region = od.region
            JOIN productcatalog.products p ON od.product_id = p.id AND o.region = p.region
            JOIN usermanagement.users u ON o.user_id = u.id AND o.region = u.region
            LEFT JOIN shippinglogistic.shipments sh ON o.id = sh.order_id AND o.region = sh.region
            LEFT JOIN shippinglogistic.shipmentstatuses s ON sh.shipment_status_id = s.id
            WHERE p.store_id = :store_id 
              AND o.region = :region
              AND o.created_at >= :start_date
            ORDER BY o.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        
        orders = postgres_adapter.execute_raw(
            query,
            {
                "store_id": store_id,
                "region": region,
                "start_date": start_date,
                "limit": per_page,
                "offset": offset
            }
        )
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        return [OrderResponse(**order) for order in orders]
    except Exception as e:
        duration = time.time() - start_time
        print(f"Query executed in {duration:.4f} seconds")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/products/categories/", response_model=List[CategoryResponse], tags=["Products"])
def get_categories():
    try:
        categories = postgres_adapter.get_all(
            table="productcatalog.categories"
        )
        return [CategoryResponse(**cat) for cat in categories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    

@app.get("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
def get_product(product_id: int, region: str):
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
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    
@app.post("/questions/", response_model=QuestionResponse, tags=["Q&A"])
def create_question(question: dict):
    try:
        # Validar que usuario y producto existen en la región
        user = postgres_adapter.get_by_id(
            table="usermanagement.users",
            id=question["user_id"]
        )
        if not user or user.get("region") != question["region"]:
            raise HTTPException(
                status_code=404,
                detail="User not found in the specified region"
            )
        
        product = postgres_adapter.get_by_id(
            table="productcatalog.products",
            id=question["product_id"]
        )
        if not product or product.get("region") != question["region"]:
            raise HTTPException(
                status_code=404,
                detail="Product not found in the specified region"
            )
        
        question_id = postgres_adapter.insert(
            table="qa.productQuestions",
            data=question
        )
        
        new_question = postgres_adapter.get_by_id(
            table="qa.productQuestions",
            id=question_id
        )
        return QuestionResponse(**new_question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.post("/answers/", response_model=AnswerResponse, tags=["Q&A"])
def create_answer(answer: dict):
    try:
        # Validar que tienda y pregunta existen en la región
        store = postgres_adapter.get_by_id(
            table="sellermanagement.stores",
            id=answer["store_id"]
        )
        if not store or store.get("region") != answer["region"]:
            raise HTTPException(
                status_code=404,
                detail="Store not found in the specified region"
            )
        
        question = postgres_adapter.get_by_id(
            table="qa.productQuestions",
            id=answer["question_id"]
        )
        if not question or question.get("region") != answer["region"]:
            raise HTTPException(
                status_code=404,
                detail="Question not found in the specified region"
            )
        
        answer_id = postgres_adapter.insert(
            table="qa.productAnswers",
            data=answer
        )
        
        new_answer = postgres_adapter.get_by_id(
            table="qa.productAnswers",
            id=answer_id
        )
        return AnswerResponse(**new_answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/orders/", response_model=OrderResponse, tags=["Orders"])
def create_order(order: OrderCreate):
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
        return OrderResponse(**new_order)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.post("/order-details/", response_model=OrderDetailResponse, tags=["Orders"])
def create_order_detail(detail: OrderDetailCreate):
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
        return OrderDetailResponse(**new_detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.get("/orders/{order_id}/details", response_model=List[OrderDetailResponse], tags=["Orders"])
def get_order_details(order_id: int, region: str):
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
        
        details = postgres_adapter.get_all(
            table="orderprocessing.orderDetails",
            filters={
                "order_id": order_id,
                "region": region
            }
        )
        return [OrderDetailResponse(**det) for det in details]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.post("/shipments/", response_model=ShipmentResponse, tags=["Shipments"])
def create_shipment(shipment: dict):
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
        return ShipmentResponse(**new_shipment)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.post("/payments/", response_model=PaymentResponse, tags=["Payments"])
def create_payment(payment: dict):
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
        return PaymentResponse(**new_payment)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.get("/search-history/{user_id}", response_model=List[SearchHistoryResponse], tags=["Recommendations"])
def get_search_history(user_id: int, region: str):
    try:
        # Verificar usuario en la región
        user = postgres_adapter.get_by_id(
            table="usermanagement.users",
            id=user_id
        )
        if not user or user.get("region") != region:
            raise HTTPException(
                status_code=404,
                detail="User not found in the specified region"
            )
        
        history = postgres_adapter.get_all(
            table="recommendationmanagement.usersearchhistory",
            filters={
                "user_id": user_id,
                "region": region
            },
            limit=100  # Últimas 100 búsquedas
        )
        return [SearchHistoryResponse(**item) for item in history]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.post("/campaigns/", response_model=CampaignResponse, tags=["Advertising"])
def create_campaign(campaign: dict):
    try:
        # Verificar tienda en la región
        store = postgres_adapter.get_by_id(
            table="sellermanagement.stores",
            id=campaign["store_id"]
        )
        if not store or store.get("region") != campaign["region"]:
            raise HTTPException(
                status_code=404,
                detail="Store not found in the specified region"
            )
        
        campaign_id = postgres_adapter.insert(
            table="publicitymanagement.campaign",
            data=campaign
        )
        
        new_campaign = postgres_adapter.get_by_id(
            table="publicitymanagement.campaign",
            id=campaign_id
        )
        return CampaignResponse(**new_campaign)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.post("/ads/", response_model=AdResponse, tags=["Advertising"])
def create_ad(ad: dict):
    try:
        # Verificar campaña y producto en la región
        campaign = postgres_adapter.get_by_id(
            table="publicitymanagement.campaign",
            id=ad["campaign_id"]
        )
        if not campaign or campaign.get("region") != ad["region"]:
            raise HTTPException(
                status_code=404,
                detail="Campaign not found in the specified region"
            )
        
        product = postgres_adapter.get_by_id(
            table="productcatalog.products",
            id=ad["product_id"]
        )
        if not product or product.get("region") != ad["region"]:
            raise HTTPException(
                status_code=404,
                detail="Product not found in the specified region"
            )
        
        ad_id = postgres_adapter.insert(
            table="publicitymanagement.ad",
            data=ad
        )
        
        new_ad = postgres_adapter.get_by_id(
            table="publicitymanagement.ad",
            id=ad_id
        )
        return AdResponse(**new_ad)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")