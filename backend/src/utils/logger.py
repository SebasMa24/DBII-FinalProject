import os
from datetime import datetime
from typing import Dict, Union

class Logger:
    """
    Logger is a simple file-based logging utility for recording API requests or system events.

    Attributes:
        log_file (str): Path to the log file used for storing log entries.
    """
    def __init__(self, log_file: str = "log.txt"):
        """
        Initializes the Logger instance and ensures the log file exists.

        Args:
            log_file (str): Name or path of the log file. Defaults to "log.txt".
        """
        self.log_file = log_file
        self._ensure_log_file()

    def _ensure_log_file(self):
        """Creates the log file if it does not exist."""
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write("=== Log File Created ===\n")

    def log_request(self, endpoint: str, method: str, params: Union[Dict, str]):
        """
        Logs a request entry with a timestamp, endpoint, HTTP method, and parameters.

        Args:
            endpoint (str): The name or path of the endpoint being accessed.
            method (str): The HTTP method used (GET, POST, etc.).
            params (Union[Dict, str]): Parameters passed in the request. Can be a dictionary or string.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert parameters to string if they are provided as a dictionary
        if isinstance(params, dict):
            param_str = ", ".join(f"{k}={v}" for k, v in params.items())
        else:
            param_str = str(params)
        
        entry = f"[{timestamp}]: Endpoint:{endpoint} - Method: {method.upper()} - Params:{param_str}\n"

        with open(self.log_file, "a") as f:
            f.write(entry)

    def clear(self):
        """
        Clears the contents of the log file, resetting it with a header entry.
        """
        with open(self.log_file, "w") as f:
            f.write("=== Log Cleared ===\n")
