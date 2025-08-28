import requests
import json

class CNJAPIClient:
    BASE_URL = "https://api-publica.datajud.cnj.jus.br/"
    API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==" # This key is public as per CNJ documentation

    def __init__(self):
        self.headers = {
            "Authorization": f"APIKey {self.API_KEY}",
            "Content-Type": "application/json"
        }

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
        try:
            response = requests.post(url, headers=self.headers, json=query)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"An unexpected error occurred: {req_err}")
        return None
