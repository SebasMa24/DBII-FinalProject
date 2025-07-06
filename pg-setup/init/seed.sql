INSERT INTO usermanagement.roles(role_name) values('ROLE_CUSTOMER');
INSERT INTO usermanagement.roles(role_name) values('ROLE_SELLER');
INSERT INTO usermanagement.roles(role_name) values('ROLE_DBADMINISTRATOR');
INSERT INTO usermanagement.roles(role_name) values('ROLE_ADMINISTRATOR');
INSERT INTO usermanagement.roles(role_name) values('ROLE_PLATFORMMANAGER');

INSERT INTO productcatalog.categories(name, description) VALUES
('Electrónica', 'Productos electrónicos como celulares, computadoras y accesorios'),
('Celulares y Smartphones', 'Teléfonos móviles y accesorios'),
('Computadoras y Tablets', 'Laptops, desktops, tablets y periféricos'),
('Audio', 'Equipos de audio, parlantes, auriculares'),
('Televisores y Video', 'TVs, proyectores, reproductores de video'),
('Hogar y Muebles', 'Muebles, decoración, electrodomésticos para el hogar'),
('Cocina', 'Electrodomésticos y utensilios de cocina'),
('Deportes y Fitness', 'Equipamiento deportivo y ropa deportiva'),
('Moda', 'Ropa, calzado y accesorios de moda'),
('Juguetes y Juegos', 'Juguetes para niños y juegos de mesa'),
('Herramientas y Construcción', 'Herramientas manuales y eléctricas, materiales de construcción'),
('Autos, Motos y Otros', 'Vehículos, repuestos y accesorios'),
('Belleza y Cuidado Personal', 'Productos de belleza y cuidado personal'),
('Salud', 'Medicamentos, productos de salud y bienestar'),
('Libros, Revistas y Comics', 'Material de lectura y coleccionables'),
('Instrumentos Musicales', 'Guitarras, pianos, baterías y accesorios musicales'),
('Computación', 'Software, hardware y accesorios para computación'),
('Videojuegos y Consolas', 'Juegos, consolas y accesorios'),
('Bebés', 'Productos para bebés y maternidad'),
('Alimentos y Bebidas', 'Comestibles, bebidas y gourmet'),
('Mascotas', 'Alimentos y accesorios para mascotas');

INSERT INTO shippinglogistic.shipmentstatuses (status_name, description) VALUES
('Not Shipped', 'El pedido aún no ha sido enviado'),
('Preparing', 'El paquete se está preparando para el envío'),
('In Transit', 'El paquete está en tránsito'),
('Out for Delivery', 'El paquete está en reparto final'),
('Delivered', 'El paquete fue entregado'),
('Returned to Sender', 'El paquete fue devuelto al vendedor'),
('Lost', 'El envío se perdió en tránsito');

INSERT INTO paymentmanagement.paymentstatuses (status_name, description) VALUES
('Unpaid', 'El pago no ha sido recibido'),
('Pending', 'El pago está en proceso de verificación'),
('Paid', 'El pago fue realizado exitosamente'),
('Failed', 'El intento de pago falló'),
('Refunded', 'El pago fue reembolsado al cliente'),
('Disputed', 'El pago ha sido impugnado por el cliente o el banco');

INSERT INTO paymentmanagement.paymentmethod (method_name) VALUES
('Credit Card'),
('Debit Card'),
('Bank Transfer'),
('PayPal'),
('Cash on Delivery');

INSERT INTO orderprocessing.coupons (code, value_Percentage, value_Fixed, max_Usage, usage_Count, expiration_Date, is_Active) VALUES
('SAVE10', 10, NULL, 100, 25, '2025-12-31', TRUE),
('FREESHIP', NULL, 5000, 200, 50, '2025-11-30', TRUE),
('WELCOME5', 5, NULL, 500, 120, '2026-01-15', TRUE),
('HOLIDAY20', 20, NULL, 300, 190, '2025-12-25', TRUE),
('BLACKFRI', NULL, 15000, 100, 100, '2025-11-29', FALSE),
('SPRING15', 15, NULL, 150, 30, '2025-06-21', TRUE),
('EXTRA30', 30, NULL, 50, 45, '2025-07-15', TRUE),
('NEWYEAR', NULL, 10000, 80, 60, '2025-12-31', TRUE),
('FLASH50', 50, NULL, 20, 18, '2025-06-05', TRUE),
('GAMER10', 10, NULL, 1000, 150, '2026-05-01', TRUE),
('PETLOVE', NULL, 8000, 120, 95, '2025-09-30', TRUE),
('READ20', 20, NULL, 300, 170, '2026-03-01', TRUE),
('TECH25', 25, NULL, 60, 55, '2025-08-15', TRUE),
('BEAUTY5', 5, NULL, 200, 50, '2025-10-10', TRUE),
('FALLSALE', NULL, 3000, 100, 80, '2025-10-31', TRUE),
('STUDENT', 15, NULL, 500, 490, '2025-12-01', FALSE),
('WELCOME50', NULL, 5000, 100, 70, '2025-12-31', TRUE),
('FLASH25', 25, NULL, 30, 29, '2025-06-02', TRUE),
('JULY4TH', NULL, 4000, 100, 10, '2025-07-04', TRUE),
('VIP30', 30, NULL, 40, 20, '2025-12-31', TRUE);