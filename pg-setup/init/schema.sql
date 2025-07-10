
-- ============================================================================
-- DATABASE SCHEMA: E-COMMERCE MULTI-REGIONAL SYSTEM
-- ============================================================================
-- This schema supports a multi-region e-commerce platform. The architecture 
-- uses PostgreSQL for structured and relational data and partitions by region.
-- NoSQL is used for images, discounts, Q&A, chats, recommendations, and ads.
-- ============================================================================

-- ============================================================================
-- SCHEMAS (Namespaces)
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS usermanagement;       -- Users, addresses, roles
CREATE SCHEMA IF NOT EXISTS sellermanagement;     -- Stores and seller accounts
CREATE SCHEMA IF NOT EXISTS reviewmanagement;     -- Product reviews
CREATE SCHEMA IF NOT EXISTS productcatalog;       -- Products and categories
CREATE SCHEMA IF NOT EXISTS orderprocessing;      -- Orders, coupons, details
CREATE SCHEMA IF NOT EXISTS shippinglogistic;     -- Shipments and tracking
CREATE SCHEMA IF NOT EXISTS paymentmanagement;    -- Payments and methods

-- ============================================================================
-- MASTER TABLES (Static data used as foreign key references)
-- ============================================================================
-- User roles (Admin, Customer, Seller, etc.)
CREATE TABLE usermanagement.roles(
    id serial PRIMARY KEY,
    role_Name varchar(50) NOT NULL
);

-- Product categories
CREATE TABLE productcatalog.categories(
    id serial PRIMARY KEY,
    name varchar(50) NOT NULL,
    description varchar(100) NOT NULL
);

-- Shipment status types (e.g., Shipped, In Transit, Delivered)
CREATE TABLE shippinglogistic.shipmentstatuses(
    id serial PRIMARY KEY,
    status_name varchar(50) NOT NULL,
    description varchar(255)
);

-- Payment methods (e.g., Credit Card, Bank Transfer)
CREATE TABLE paymentmanagement.paymentmethod(
    id serial PRIMARY KEY,
    method_name varchar(50) NOT NULL
);

-- Payment statuses (e.g., Paid, Pending, Failed)
CREATE TABLE paymentmanagement.paymentstatuses(
    id serial PRIMARY KEY,
    status_name varchar(50) NOT NULL,
    description varchar(255)
);

-- ============================================================================
-- USER MANAGEMENT
-- ============================================================================
-- Registered users (partitioned by region)
CREATE TABLE usermanagement.users (
    id serial,
    role_id int NOT NULL,
    name varchar(50) NOT NULL,
    email varchar(50) NOT NULL,
    password varchar(20) NOT NULL,
    phone bigint,
    birthday date NOT NULL,
    region varchar(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, region),
    FOREIGN KEY (role_id) REFERENCES usermanagement.roles(id)
) PARTITION BY LIST (region);

-- Regional partitions
CREATE TABLE usermanagement.users_colombia PARTITION OF usermanagement.users FOR VALUES IN ('Colombia');
CREATE TABLE usermanagement.users_mexico PARTITION OF usermanagement.users FOR VALUES IN ('Mexico');
CREATE TABLE usermanagement.users_argentina PARTITION OF usermanagement.users FOR VALUES IN ('Argentina');

-- User addresses (partitioned by region)
CREATE TABLE usermanagement.address (
    id serial,
    user_id int NOT NULL,
    region varchar(20) NOT NULL,
    address varchar(100) NOT NULL,
    city varchar(60) NOT NULL,
    zipCode int NOT NULL,
    PRIMARY KEY (id, region),
    FOREIGN KEY (user_id, region) REFERENCES usermanagement.users(id, region)
) PARTITION BY LIST (region);

-- Regional partitions
CREATE TABLE usermanagement.address_colombia PARTITION OF usermanagement.address FOR VALUES IN ('Colombia');
CREATE TABLE usermanagement.address_mexico PARTITION OF usermanagement.address FOR VALUES IN ('Mexico');
CREATE TABLE usermanagement.address_argentina PARTITION OF usermanagement.address FOR VALUES IN ('Argentina');

-- ============================================================================
-- SELLER MANAGEMENT
-- ============================================================================
-- Store listings managed by sellers (partitioned by region)
CREATE TABLE sellermanagement.stores (
    id serial,
    user_id int NOT NULL,
    region varchar(20) NOT NULL,
    name varchar(60) NOT NULL,
    is_Official bool NOT NULL DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, region),
    FOREIGN KEY (user_id, region) REFERENCES usermanagement.users(id, region)
) PARTITION BY LIST (region);

-- Regional partitions
CREATE TABLE sellermanagement.stores_colombia PARTITION OF sellermanagement.stores FOR VALUES IN ('Colombia');
CREATE TABLE sellermanagement.stores_mexico PARTITION OF sellermanagement.stores FOR VALUES IN ('Mexico');
CREATE TABLE sellermanagement.stores_argentina PARTITION OF sellermanagement.stores FOR VALUES IN ('Argentina');

-- ============================================================================
-- PRODUCT CATALOG (Images and Discounts moved to NoSQL)
-- ============================================================================
-- Product listing (partitioned by region)
CREATE TABLE productcatalog.products (
    id serial,
    store_id int NOT NULL,
    region varchar(20) NOT NULL,
    categorie_id int NOT NULL,
    title varchar(50) NOT NULL,
    description varchar(200) NOT NULL,
    price bigint NOT NULL,
    stock int NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, region),
    FOREIGN KEY (store_id, region) REFERENCES sellermanagement.stores(id, region),
    FOREIGN KEY (categorie_id) REFERENCES productcatalog.categories(id)
) PARTITION BY LIST (region);

-- Regional partitions
CREATE TABLE productcatalog.products_colombia PARTITION OF productcatalog.products FOR VALUES IN ('Colombia');
CREATE TABLE productcatalog.products_mexico PARTITION OF productcatalog.products FOR VALUES IN ('Mexico');
CREATE TABLE productcatalog.products_argentina PARTITION OF productcatalog.products FOR VALUES IN ('Argentina');

-- ============================================================================
-- REVIEW MANAGEMENT
-- ============================================================================
-- Product reviews by users (partitioned by region)
CREATE TABLE reviewmanagement.reviews (
    id serial,
    user_id int NOT NULL,
    product_id int NOT NULL,
    region varchar(20) NOT NULL,
    rating int CHECK (rating BETWEEN 1 AND 5),
    comment varchar(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, region),
    FOREIGN KEY (user_id, region) REFERENCES usermanagement.users(id, region),
    FOREIGN KEY (product_id, region) REFERENCES productcatalog.products(id, region)
) PARTITION BY LIST (region);

-- Regional partitions
CREATE TABLE reviewmanagement.reviews_colombia PARTITION OF reviewmanagement.reviews FOR VALUES IN ('Colombia');
CREATE TABLE reviewmanagement.reviews_mexico PARTITION OF reviewmanagement.reviews FOR VALUES IN ('Mexico');
CREATE TABLE reviewmanagement.reviews_argentina PARTITION OF reviewmanagement.reviews FOR VALUES IN ('Argentina');

-- ============================================================================
-- ORDER PROCESSING
-- ============================================================================
-- Discount coupons
CREATE TABLE orderprocessing.coupons (
    id serial PRIMARY KEY,
    code varchar(10) NOT NULL,
    value_Percentage int,
    value_Fixed int,
    max_Usage int NOT NULL,
    usage_Count int NOT NULL,
    expiration_Date date NOT NULL,
    is_Active bool NOT NULL
);

-- Orders (partitioned by region)
CREATE TABLE orderprocessing.orders (
    id serial,
    user_id int NOT NULL,
    region varchar(20) NOT NULL,
    coupon_id int,
    total_Price bigint NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, region),
    FOREIGN KEY (user_id, region) REFERENCES usermanagement.users(id, region),
    FOREIGN KEY (coupon_id) REFERENCES orderprocessing.coupons(id)
) PARTITION BY LIST (region);

-- Regional partitions
CREATE TABLE orderprocessing.orders_colombia PARTITION OF orderprocessing.orders FOR VALUES IN ('Colombia');
CREATE TABLE orderprocessing.orders_mexico PARTITION OF orderprocessing.orders FOR VALUES IN ('Mexico');
CREATE TABLE orderprocessing.orders_argentina PARTITION OF orderprocessing.orders FOR VALUES IN ('Argentina');

-- Order details (partitioned by region)
CREATE TABLE orderprocessing.orderDetails (
    id serial,
    order_id int NOT NULL,
    product_id int NOT NULL,
    region varchar(20) NOT NULL,
    quantity int NOT NULL,
    unit_Price int NOT NULL,
    PRIMARY KEY (id, region),
    FOREIGN KEY (order_id, region) REFERENCES orderprocessing.orders(id, region),
    FOREIGN KEY (product_id, region) REFERENCES productcatalog.products(id, region)
) PARTITION BY LIST (region);

-- Regional partitions
CREATE TABLE orderprocessing.orderDetails_colombia PARTITION OF orderprocessing.orderDetails FOR VALUES IN ('Colombia');
CREATE TABLE orderprocessing.orderDetails_mexico PARTITION OF orderprocessing.orderDetails FOR VALUES IN ('Mexico');
CREATE TABLE orderprocessing.orderDetails_argentina PARTITION OF orderprocessing.orderDetails FOR VALUES IN ('Argentina');

-- ============================================================================
-- SHIPPING LOGISTICS
-- ============================================================================
-- Shipment information (partitioned by region)
CREATE TABLE shippinglogistic.shipments (
    id serial,
    order_id int NOT NULL,
    region varchar(20) NOT NULL,
    shipment_Status_id int NOT NULL,
    tracking_Number bigint,
    carrier varchar(20),
    shipped_At date,
    delivered_At date,
    PRIMARY KEY (id, region),
    FOREIGN KEY (order_id, region) REFERENCES orderprocessing.orders(id, region),
    FOREIGN KEY (shipment_Status_id) REFERENCES shippinglogistic.shipmentstatuses(id)
) PARTITION BY LIST (region);

-- Regional partitions
CREATE TABLE shippinglogistic.shipments_colombia PARTITION OF shippinglogistic.shipments FOR VALUES IN ('Colombia');
CREATE TABLE shippinglogistic.shipments_mexico PARTITION OF shippinglogistic.shipments FOR VALUES IN ('Mexico');
CREATE TABLE shippinglogistic.shipments_argentina PARTITION OF shippinglogistic.shipments FOR VALUES IN ('Argentina');

-- ============================================================================
-- PAYMENT MANAGEMENT
-- ============================================================================
-- Payment records (partitioned by region)
CREATE TABLE paymentmanagement.payments (
    id serial,
    order_id int NOT NULL,
    region varchar(20) NOT NULL,
    payment_Method_id int NOT NULL,
    payment_Status_id int NOT NULL,
    amount int NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, region),
    FOREIGN KEY (order_id, region) REFERENCES orderprocessing.orders(id, region),
    FOREIGN KEY (payment_Method_id) REFERENCES paymentmanagement.paymentmethod(id),
    FOREIGN KEY (payment_status_id) REFERENCES paymentmanagement.paymentstatuses(id)
) PARTITION BY LIST (region);

-- Regional partitions
CREATE TABLE paymentmanagement.payments_colombia PARTITION OF paymentmanagement.payments FOR VALUES IN ('Colombia');
CREATE TABLE paymentmanagement.payments_mexico PARTITION OF paymentmanagement.payments FOR VALUES IN ('Mexico');
CREATE TABLE paymentmanagement.payments_argentina PARTITION OF paymentmanagement.payments FOR VALUES IN ('Argentina');

-- ============================================================================
-- NOTES
-- ============================================================================
-- Q&A, Product Images, Discounts, Chat, Recommendations, and Ads have been 
-- migrated to NoSQL for flexibility and scalability.


-- =====================================================================
-- INDEX DEFINITIONS
-- =====================================================================

-- Index to speed up user address lookups by user_id
CREATE INDEX idx_address_user_local ON usermanagement.address(user_id);

-- Index to improve queries filtering orders by user_id (e.g., for user order history)
CREATE INDEX idx_orders_user_local ON orderprocessing.orders(user_id);

-- Index on order ID for efficient primary key access (if not already created automatically)
CREATE INDEX idx_orders_id ON orderprocessing.orders(id);

-- Index to improve performance of joins or filters using order_id in orderdetails
CREATE INDEX idx_orders_ordersdetails_local ON orderprocessing.orderdetails(order_id);

-- Index to improve filtering and joins on product_id in orderdetails
CREATE INDEX idx_orderdetails_product_id ON orderprocessing.orderdetails(product_id);

-- Index to speed up lookups of shipments by order_id
CREATE INDEX idx_shipments_order_local ON shippinglogistic.shipments(order_id);

-- Index to improve filtering or joining by shipment_status_id
CREATE INDEX idx_shipments_status_id ON shippinglogistic.shipments(shipment_status_id);

-- Index to improve filtering or lookups on shipmentstatuses.id (e.g., status descriptions)
CREATE INDEX idx_shipmentstatuses_id ON shippinglogistic.shipmentstatuses(id);

-- Index to improve filtering and joining on order_id in payments
CREATE INDEX idx_payments_order_local ON paymentmanagement.payments(order_id);

-- Index to support lookups or joins on payment method ID (if table is large or frequently queried)
CREATE INDEX idx_paymentmethod_id ON paymentmanagement.paymentmethod(id);

-- Index to optimize queries retrieving products from a specific store
CREATE INDEX idx_product_store_local ON productcatalog.products(store_id);