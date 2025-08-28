from cnj_api_client import CNJAPIClient
from elasticsearch import Elasticsearch
import time
import logging # Import logging module
import logging_config # Import our logging configuration

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# Configuration
ES_HOST = "localhost" # Assuming Elasticsearch is running locally
ES_PORT = 9200
ES_INDEX = "cnj_processes" # Elasticsearch index name

# Initialize clients
cnj_client = CNJAPIClient()
es_client = Elasticsearch(hosts=[{"host": ES_HOST, "port": ES_PORT, "scheme": "http"}])

def ensure_index_exists():
    """Ensures the Elasticsearch index exists."""
    logger.info(f"Checking if Elasticsearch index '{ES_INDEX}' exists.")
    try:
        if not es_client.indices.exists(index=ES_INDEX):
            es_client.indices.create(index=ES_INDEX)
            logger.info(f"Elasticsearch index '{ES_INDEX}' created.")
        else:
            logger.info(f"Elasticsearch index '{ES_INDEX}' already exists.")
    except Exception as e:
        logger.error(f"Error checking/creating Elasticsearch index '{ES_INDEX}': {e}")
        raise # Re-raise to stop execution if ES is not available

def ingest_data_for_tribunal(tribunal_endpoint: str, max_records: int = 10000):
    """
    Fetches data from CNJ API and ingests into Elasticsearch.
    Handles pagination and deduplication.
    """
    logger.info(f"Starting ingestion for {tribunal_endpoint}...")
    ensure_index_exists()

    query = {
        "query": {"match_all": {}},
        "size": 10000, # Max records per API call
        "sort": [{"@timestamp": {"order": "asc"}}] # For pagination
    }
    
    indexed_count = 0
    total_fetched = 0
    search_after = None
    page_num = 0

    while True:
        page_num += 1
        logger.info(f"Fetching page {page_num} for {tribunal_endpoint}...")
        if search_after:
            query["search_after"] = search_after

        response_data = cnj_client.search(tribunal_endpoint, query)

        if not response_data or not response_data.get("hits", {}).get("hits"):
            logger.info(f"No more data or error for {tribunal_endpoint}. Breaking ingestion loop.")
            break

        hits = response_data["hits"]["hits"]
        total_fetched += len(hits)
        logger.info(f"Fetched {len(hits)} records from CNJ API for page {page_num}.")

        for hit in hits:
            process_data = hit["_source"]
            process_id = process_data.get("numeroProcesso") # Assuming this is unique

            if not process_id:
                logger.warning(f"Skipping record due to missing 'numeroProcesso': {process_data}")
                continue

            try:
                # Check if document already exists
                if es_client.exists(index=ES_INDEX, id=process_id):
                    logger.debug(f"Process {process_id} already exists. Skipping.")
                    continue # Skip if already exists
                
                es_client.index(index=ES_INDEX, id=process_id, document=process_data)
                indexed_count += 1
                logger.debug(f"Indexed new process: {process_id}")
            except Exception as e:
                logger.error(f"Error indexing process {process_id}: {e}", exc_info=True)
        
        logger.info(f"Processed page {page_num}. Indexed {indexed_count} new records so far. Total fetched: {total_fetched}")

        # Prepare for next page
        if len(hits) < query["size"]:
            logger.info(f"Less than {query["size"]} hits on page {page_num}, assuming last page.")
            break
        
        last_hit = hits[-1]
        search_after = last_hit["sort"] # Use sort values for search_after pagination

        # Add a small delay to avoid hitting rate limits if any (though CNJ API is public key)
        time.sleep(0.5) 

    logger.info(f"Ingestion for {tribunal_endpoint} completed. Total new records indexed: {indexed_count}")
    logger.info(f"Total records fetched from API: {total_fetched}")

if __name__ == "__main__":
    logger.info("Starting ingest_cnj_data.py script.")
    try:
        ingest_data_for_tribunal("api_publica_tjsp/_search")
    except Exception as e:
        logger.critical(f"Script terminated due to unhandled error: {e}", exc_info=True)
    logger.info("Finished ingest_cnj_data.py script.")
