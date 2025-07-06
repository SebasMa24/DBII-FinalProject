# 📦 Backend - DBII Final Project

Este directorio contiene la lógica principal del backend del proyecto **DBII-FinalProject**, desarrollado en Python con FastAPI, empleando una arquitectura modular y desacoplada para facilitar la integración con diferentes bases de datos (PostgreSQL, MongoDB, Redis).

## 📂 Estructura del Proyecto

- `config/` - Archivos de configuración general del sistema (p. ej. variables de entorno).
- `database/` - Contiene los adaptadores de conexión para PostgreSQL, MongoDB y Redis, así como la clase base para estandarizar las operaciones.
- `models/` - Definición de los modelos de datos utilizados en las peticiones y respuestas.
- `utils/` - Funciones utilitarias como el sistema de logging (`logger.py`).
- `main.py` - Punto de entrada de la aplicación FastAPI.
- `.env` - Archivo de configuración con variables de entorno (por ejemplo, credenciales y URLs de bases de datos).
- `log.txt` - Archivo de salida del sistema de logs.

## ▶️ Ejecución

1. Crear un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate

2. Instalar dependencias
   pip install -r requirements.txt

3. Ejecutar la Aplicación
   python -m uvicorn main:app --reload