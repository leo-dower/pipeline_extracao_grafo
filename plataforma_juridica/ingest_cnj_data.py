from cnj_api_client import CNJAPIClient
from elasticsearch import Elasticsearch
import time

# Configuration
ES_HOST = "localhost" # Assuming Elasticsearch is running locally
ES_PORT = 9200
ES_INDEX = "cnj_processes" # Elasticsearch index name

# Initialize clients
cnj_client = CNJAPIClient()
es_client = Elasticsearch(hosts=[{"host": ES_HOST, "port": ES_PORT, "scheme": "http"}])

def ensure_index_exists():
    """Ensures the Elasticsearch index exists."""
    if not es_client.indices.exists(index=ES_INDEX):
        es_client.indices.create(index=ES_INDEX)
        print(f"Elasticsearch index '{ES_INDEX}' created.")
    else:
        print(f"Elasticsearch index '{ES_INDEX}' already exists.")

def ingest_data_for_tribunal(tribunal_endpoint: str, max_records: int = 10000):
    """
    Fetches data from CNJ API and ingests into Elasticsearch.
    Handles pagination and deduplication.
    """
    print(f"Starting ingestion for {tribunal_endpoint}...")
    ensure_index_exists()

    query = {
        "query": {"match_all": {}},
        "size": 10000, # Max records per API call
        "sort": [{"@timestamp": {"order": "asc"}}]
    }
    
    indexed_count = 0
    total_fetched = 0
    search_after = None

    while True:
        if search_after:
            query["search_after"] = search_after

        response_data = cnj_client.search(tribunal_endpoint, query)

        if not response_data or not response_data.get("hits", {}).get("hits"):
            print(f"No more data or error for {tribunal_endpoint}.")
            break

        hits = response_data["hits"]["hits"]
        total_fetched += len(hits)

        for hit in hits:
            process_data = hit["_source"]
            process_id = process_data.get("numeroProcesso") # Assuming this is unique

            if not process_id:
                print(f"Skipping record due to missing 'numeroProcesso': {process_data}")
                continue

            try:
                # Check if document already exists
                if es_client.exists(index=ES_INDEX, id=process_id):
                    # print(f"Process {process_id} already exists. Skipping.")
                    continue # Skip if already exists
                
                es_client.index(index=ES_INDEX, id=process_id, document=process_data)
                indexed_count += 1
            except Exception as e:
                print(f"Error indexing process {process_id}: {e}")
        
        print(f"Fetched {len(hits)} records, indexed {indexed_count} new records so far. Total fetched: {total_fetched}")

        # Prepare for next page
        if len(hits) < query["size"]:
            break
        
        last_hit = hits[-1]
        search_after = last_hit["sort"]

        # Add a small delay to avoid hitting rate limits if any (though CNJ API is public key)
        time.sleep(0.5) 

    print(f"Ingestion for {tribunal_endpoint} completed. Total new records indexed: {indexed_count}")
    print(f"Total records fetched from API: {total_fetched}")

if __name__ == "__main__":
    # Example usage: Ingest data from TJSP
    # You need to have an Elasticsearch instance running at ES_HOST:ES_PORT
    # To run this, first install dependencies: pip install -r plataforma_juridica/requirements.txt
    
    # For testing, let's use a small number of records
    # ingest_data_for_tribunal("api_publica_tjsp/_search", max_records=100) 
    
    # For full ingestion (up to 10000 per call, with pagination)
    ingest_data_for_tribunal("api_publica_tjsp/_search")

    # You can add more calls for other tribunals here
    # ingest_data_for_tribunal("api_publica_stj/_search")