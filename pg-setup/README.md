### 📁 `pg-setup/README.md`

# 🐘 PostgreSQL Setup - DBII Final Project

Este directorio contiene la configuración necesaria para levantar el entorno completo de la arquitectura de la base de datos con balanceo de carga utilizando **Pgpool-II**, para la base de datos relacional **PostgreSQL**, ideal para entornos de desarrollo y pruebas,  bases de datos no relacionales como **MongoDB** y un servidor de cache **REDIS**.

## 📂 Estructura

- `data/` - Carpetas de persistencia de datos para los contenedores PostgreSQL (`master/`) y Pgpool (`pgpool/`).
- `mongo-init/` - Ejecuta automaticamente un script JS para la creación de las colecciones.
- `docker-compose.yml` - Archivo principal de orquestación para levantar los servicios de base de datos con Docker Compose.
- `.env` - Archivo con variables de entorno necesarias para configurar los contenedores.

## ▶️ Instrucciones para levantar el entorno

1. Navegar al directorio raíz del proyecto:
   ```bash
   cd pg-setup

2. Levantar los contenedores
   docker-compose up -d

3. Verificar servicios:
   PostgreSQL Master: localhost:5432
   Pgpool-II: localhost:9999 (balanceador de carga)
   MongoDB:  localhost:27018
   REDIS: localhost:6379

4. Insertar data sintetica Disponible en [Google Drive](https://drive.google.com/drive/folders/1jUZXU4HzO4oqksMzTFWZDLdHYX4m4Yew?usp=drive_link),en el siguiente orden:
   Users (No considerar id ni created_at al importar)
   Address (No considerar id al importar)
   Stores
   Products
   Orders
   OrderDetails
   Shipments
   Payments
