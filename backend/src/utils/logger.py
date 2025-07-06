import os
from datetime import datetime
from typing import Dict, Union

class Logger:
    def __init__(self, log_file: str = "log.txt"):
        self.log_file = log_file
        self._ensure_log_file()

    def _ensure_log_file(self):
        """Crea el archivo si no existe."""
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write("=== Log File Created ===\n")

    def log_request(self, endpoint: str, method: str, params: Union[Dict, str]):
        """Registra un log con formato: [timestamp]: endpoint - METHOD - params"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Convertir parámetros a string si es un diccionario
        if isinstance(params, dict):
            param_str = ", ".join(f"{k}={v}" for k, v in params.items())
        else:
            param_str = str(params)
        
        entry = f"[{timestamp}]: Endpoint:{endpoint} - Method: {method.upper()} - Params:{param_str}\n"

        with open(self.log_file, "a") as f:
            f.write(entry)

    def clear(self):
        """Borra el contenido del archivo log."""
        with open(self.log_file, "w") as f:
            f.write("=== Log Cleared ===\n")