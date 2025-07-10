### 📁 `pg-setup/README.md`

# 🐘 PostgreSQL Setup - DBII Final Project

This directory contains the necessary configuration to launch the complete database architecture environment with load balancing using **Pgpool-II**, for the relational database **PostgreSQL**. It is ideal for development and testing environments and includes non-relational databases like **MongoDB** and a **Redis** cache server.

## 📂 Structure

- `data/` - Persistent data directories for the PostgreSQL containers (`master/`) and Pgpool (`pgpool/`).
- `mongo-init/` - Automatically runs a JS script to create collections.
- `docker-compose.yml` - Main orchestration file to launch the database services using Docker Compose.
- `.env` - Environment variables file required to configure the containers.

## ▶️ Instructions to launch the environment

1. Navigate to the root directory of the project:
   ```bash
   cd pg-setup
   ```

2. Launch the containers:
   ```bash
   docker-compose up -d
   ```

3. Verify services:
   - PostgreSQL Master: localhost:5432  
   - Pgpool-II: localhost:9999 (load balancer)  
   - MongoDB: localhost:27018  
   - REDIS: localhost:6379  

4. Insert synthetic data available at [Google Drive](https://drive.google.com/drive/folders/1jUZXU4HzO4oqksMzTFWZDLdHYX4m4Yew?usp=drive_link), in the following order:
   - Users (Do not include `id` or `created_at` during import)
   - Address (Do not include `id` during import)
   - Stores (Do not include `id` or `isOfficial` during import)
   - Products (Do not include `id` during import)
   - Orders (Do not include `id` during import)
   - OrderDetails (Do not include `id` during import)
   - Shipments (Do not include `id` during import)
   - Payments (Do not include `id` during import)