# 📦 Backend - DBII Final Project

This directory contains the core backend logic of the **DBII-FinalProject**, developed in Python with FastAPI, using a modular and decoupled architecture to enable integration with multiple databases (PostgreSQL, MongoDB, Redis).

## 📂 Project Structure

- `config/` - General system configuration files (e.g., environment variables).
- `database/` - Contains connection adapters for PostgreSQL, MongoDB, and Redis, as well as a base class to standardize operations.
- `models/` - Data model definitions used for requests and responses.
- `utils/` - Utility functions such as the logging system (`logger.py`).
- `main.py` - Entry point of the FastAPI application.
- `.env` - Configuration file with environment variables (e.g., database credentials and URLs).
- `log.txt` - Output file for the logging system.

## ▶️ Running the Application

1. Navigate to the `src` folder of the project:
   ```bash
   cd ..\Github\DBII-FinalProject\backend\src
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create the `.env` file based on `.env.example`.

5. Run the application:
   ```bash
   python -m uvicorn main:app --reload
   ```