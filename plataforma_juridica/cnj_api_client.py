import requests
import json
import logging # Import logging module
import logging_config # Import our logging configuration

# Get a logger instance for this module
logger = logging.getLogger(__name__)

class CNJAPIClient:
    BASE_URL = "https://api-publica.datajud.cnj.jus.br/"
    API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TREDyQk1RdnFKZGRQdw==" # This key is public as per CNJ documentation

    def __init__(self):
        self.headers = {
            "Authorization": f"APIKey {self.API_KEY}",
            "Content-Type": "application/json"
        }
        logger.info("CNJAPIClient initialized.")

    def search(self, tribunal_endpoint: str, query: dict):
        """
        Performs a search request to the CNJ DataJud API for a specific tribunal.

        Args:
            tribunal_endpoint (str): The specific tribunal endpoint (e.g., "api_publica_tjsp/_search").
            query (dict): The Elasticsearch-like query body.

        Returns:
            dict: The JSON response from the API, or None if an error occurs.
        """
        url = f"{self.BASE_URL}{tribunal_endpoint}"
        logger.debug(f"Sending request to CNJ API: {url} with query: {json.dumps(query)}")
        try:
            response = requests.post(url, headers=self.headers, json=query)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            logger.debug(f"Received response from CNJ API (status: {response.status_code}): {response.text[:200]}...") # Log first 200 chars
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred during CNJ API call: {http_err} - Response: {response.text}")
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"Connection error occurred during CNJ API call: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            logger.error(f"Timeout error occurred during CNJ API call: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            logger.error(f"An unexpected error occurred during CNJ API call: {req_err}")
        return None