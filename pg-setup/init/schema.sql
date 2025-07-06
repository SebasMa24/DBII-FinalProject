
CREATE SCHEMA IF NOT EXISTS usermanagement;
CREATE SCHEMA IF NOT EXISTS sellermanagement;
CREATE SCHEMA IF NOT EXISTS reviewmanagement;
CREATE SCHEMA IF NOT EXISTS productcatalog;
CREATE SCHEMA IF NOT EXISTS orderprocessing;
CREATE SCHEMA IF NOT EXISTS shippinglogistic;
CREATE SCHEMA IF NOT EXISTS paymentmanagement;

-- =====================================================================
-- ESQUEMA SQL MODIFICADO: EXCLUYE ENTIDADES MIGRADAS A NoSQL
-- =====================================================================

-- Tablas maestras
CREATE TABLE usermanagement.roles(
    id serial PRIMARY KEY,
    role_Name varchar(50) not null
);

CREATE TABLE productcatalog.categories(
    id serial PRIMARY KEY,
    name varchar(50) not null,
    description varchar(100) not null
);

CREATE TABLE shippinglogistic.shipmentstatuses(
    id serial PRIMARY KEY,
    status_name varchar(50) not null,
    description varchar(255) null
);

CREATE TABLE paymentmanagement.paymentmethod(
    id serial PRIMARY KEY,
    method_name varchar(50) not null
);

CREATE TABLE paymentmanagement.paymentstatuses(
    id serial PRIMARY KEY,
    status_name varchar(50) not null,
    description varchar(255) null
);

-- =====================================================================
-- USER MANAGEMENT
-- =====================================================================
CREATE TABLE usermanagement.users (
    id serial,
    role_id int NOT NULL,
    name varchar(50) NOT NULL,
    email varchar(50) NOT NULL,
    password varchar(20) NOT NULL,
    phone bigint NULL,
    birthday date NOT NULL,
    region varchar(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, region),
    FOREIGN KEY (role_id) REFERENCES usermanagement.roles(id)
) PARTITION BY LIST (region);

CREATE TABLE usermanagement.users_colombia PARTITION OF usermanagement.users FOR VALUES IN ('Colombia');
CREATE TABLE usermanagement.users_mexico PARTITION OF usermanagement.users FOR VALUES IN ('Mexico');
CREATE TABLE usermanagement.users_argentina PARTITION OF usermanagement.users FOR VALUES IN ('Argentina');

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

CREATE TABLE usermanagement.address_colombia PARTITION OF usermanagement.address FOR VALUES IN ('Colombia');
CREATE TABLE usermanagement.address_mexico PARTITION OF usermanagement.address FOR VALUES IN ('Mexico');
CREATE TABLE usermanagement.address_argentina PARTITION OF usermanagement.address FOR VALUES IN ('Argentina');

-- =====================================================================
-- SELLER MANAGEMENT
-- =====================================================================
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

CREATE TABLE sellermanagement.stores_colombia PARTITION OF sellermanagement.stores FOR VALUES IN ('Colombia');
CREATE TABLE sellermanagement.stores_mexico PARTITION OF sellermanagement.stores FOR VALUES IN ('Mexico');
CREATE TABLE sellermanagement.stores_argentina PARTITION OF sellermanagement.stores FOR VALUES IN ('Argentina');

-- =====================================================================
-- PRODUCT CATALOG (SIN imágenes ni descuentos)
-- =====================================================================
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

CREATE TABLE productcatalog.products_colombia PARTITION OF productcatalog.products FOR VALUES IN ('Colombia');
CREATE TABLE productcatalog.products_mexico PARTITION OF productcatalog.products FOR VALUES IN ('Mexico');
CREATE TABLE productcatalog.products_argentina PARTITION OF productcatalog.products FOR VALUES IN ('Argentina');

-- NOTA: productImage y productDiscount migradas a NoSQL

-- =====================================================================
-- REVIEW MANAGEMENT
-- =====================================================================
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

CREATE TABLE reviewmanagement.reviews_colombia PARTITION OF reviewmanagement.reviews FOR VALUES IN ('Colombia');
CREATE TABLE reviewmanagement.reviews_mexico PARTITION OF reviewmanagement.reviews FOR VALUES IN ('Mexico');
CREATE TABLE reviewmanagement.reviews_argentina PARTITION OF reviewmanagement.reviews FOR VALUES IN ('Argentina');

-- =====================================================================
-- Q&A MIGRADO A NoSQL

-- =====================================================================
-- ORDER PROCESSING
-- =====================================================================
CREATE TABLE orderprocessing.coupons (
    id serial PRIMARY KEY,
    code varchar(10) NOT NULL,
    value_Percentage int NULL,
    value_Fixed int NULL,
    max_Usage int NOT NULL,
    usage_Count int NOT NULL,
    expiration_Date date NOT NULL,
    is_Active bool NOT NULL
);

CREATE TABLE orderprocessing.orders (
    id serial,
    user_id int NOT NULL,
    region varchar(20) NOT NULL,
    coupon_id int NULL,
    total_Price bigint NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, region),
    FOREIGN KEY (user_id, region) REFERENCES usermanagement.users(id, region),
    FOREIGN KEY (coupon_id) REFERENCES orderprocessing.coupons(id)
) PARTITION BY LIST (region);

CREATE TABLE orderprocessing.orders_colombia PARTITION OF orderprocessing.orders FOR VALUES IN ('Colombia');
CREATE TABLE orderprocessing.orders_mexico PARTITION OF orderprocessing.orders FOR VALUES IN ('Mexico');
CREATE TABLE orderprocessing.orders_argentina PARTITION OF orderprocessing.orders FOR VALUES IN ('Argentina');

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

CREATE TABLE orderprocessing.orderDetails_colombia PARTITION OF orderprocessing.orderDetails FOR VALUES IN ('Colombia');
CREATE TABLE orderprocessing.orderDetails_mexico PARTITION OF orderprocessing.orderDetails FOR VALUES IN ('Mexico');
CREATE TABLE orderprocessing.orderDetails_argentina PARTITION OF orderprocessing.orderDetails FOR VALUES IN ('Argentina');

-- =====================================================================
-- CHAT MIGRADO A NoSQL

-- =====================================================================
-- SHIPPING LOGISTIC
-- =====================================================================
CREATE TABLE shippinglogistic.shipments (
    id serial,
    order_id int NOT NULL,
    region varchar(20) NOT NULL,
    shipment_Status_id int NOT NULL,
    tracking_Number bigint NULL,
    carrier varchar(20) NULL,
    shipped_At date NULL,
    delivered_At date NULL,
    PRIMARY KEY (id, region),
    FOREIGN KEY (order_id, region) REFERENCES orderprocessing.orders(id, region),
    FOREIGN KEY (shipment_Status_id) REFERENCES shippinglogistic.shipmentstatuses(id)
) PARTITION BY LIST (region);

CREATE TABLE shippinglogistic.shipments_colombia PARTITION OF shippinglogistic.shipments FOR VALUES IN ('Colombia');
CREATE TABLE shippinglogistic.shipments_mexico PARTITION OF shippinglogistic.shipments FOR VALUES IN ('Mexico');
CREATE TABLE shippinglogistic.shipments_argentina PARTITION OF shippinglogistic.shipments FOR VALUES IN ('Argentina');

-- =====================================================================
-- PAYMENT MANAGEMENT
-- =====================================================================
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

CREATE TABLE paymentmanagement.payments_colombia PARTITION OF paymentmanagement.payments FOR VALUES IN ('Colombia');
CREATE TABLE paymentmanagement.payments_mexico PARTITION OF paymentmanagement.payments FOR VALUES IN ('Mexico');
CREATE TABLE paymentmanagement.payments_argentina PARTITION OF paymentmanagement.payments FOR VALUES IN ('Argentina');

-- =====================================================================
-- RECOMMENDATION & PUBLICITY MANAGEMENT MIGRADOS A NoSQL


