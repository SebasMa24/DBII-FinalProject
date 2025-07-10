# 📦 Final Project – Database Systems II

This repository contains the final project developed for the **Database Systems II** course. It integrates both relational and non-relational database systems, showcasing real-world data modeling, querying, caching, and service orchestration.

## 🧑‍🏫 Supervisor

**Carlos Andrés Sierra**

## 👥 Authors

- **Luis Sebastián Martínez Guerrero**
- **Leidy Marcela Morales Segura**

---

## 📂 Project Structure

```
├── backend/                  # Backend implementation (FastAPI, Redis, APIs)
│   └── src/                 # Source code for services and endpoints
│   └── README.md            # Specific documentation for backend setup

├── Documentation/           # Project documentation and supporting files
│   └── .empty               # Placeholder file (no docs added yet)

├── pg-setup/                # PostgreSQL & MongoDB setup
│   ├── config/             # Config files (if needed)
│   ├── data/               # Datasets used for initial seeding
│   ├── init/               # Init scripts for both databases
│   │   ├── init.js         # MongoDB: creates collections and indexes
│   │   ├── schema.sql      # PostgreSQL: schema definition
│   │   └── seed.sql        # PostgreSQL: insert mock/demo data

│   ├── .env                 # Environment variables (Docker, DBs)
│   ├── .env.example         # Example of required environment setup
│   ├── docker-compose.yml   # Multi-container definition (PostgreSQL, MongoDB, Redis)
│   ├── Dockerfile           # Custom Docker image setup (if needed)
│   └── README.md            # Instructions for setting up the database services

├── .gitignore               # Files and folders ignored by Git
├── README.md                # General documentation for the entire project
```

---

## 🚀 Features

- ✅ **Hybrid database architecture** using PostgreSQL and MongoDB  
- ✅ **API development** with FastAPI for data interaction  
- ✅ **Data caching** using Redis to improve performance  
- ✅ **Containerized services** via Docker for easy deployment  
- ✅ **Custom data seeding** for testing and analytics  
- ✅ **Indexing** in PostgreSQL and MongoDB for optimized search and aggregation  

---

## 🔧 Technologies Used

| Technology     | Description                                 |
|----------------|---------------------------------------------|
| **PostgreSQL** | Relational database for structured data     |
| **MongoDB**    | NoSQL database for flexible data modeling   |
| **Redis**      | Key-value store for fast in-memory caching  |
| **FastAPI**    | Python web framework for APIs               |
| **Docker**     | Containerization of all services            |
| **SQL & JS**   | Scripting for schema creation and data load |

---

## 📦 How to Run

Look into backend folder and pg-setup for more information. 

## 📅 Final Delivery

This repository is the **final submission** for the **Database Systems II** course project.
