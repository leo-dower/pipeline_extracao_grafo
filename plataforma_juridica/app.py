from fastapi import FastAPI, HTTPException
from elasticsearch import Elasticsearch
from pydantic import BaseModel
from typing import List, Optional
import os
from groq import Groq
import logging # Import logging module
import logging_config # Import our logging configuration

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# --- Configuration ---
ES_HOST = "localhost"
ES_PORT = 9200
ES_INDEX = "cnj_processes"

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY") # Load API key from environment variable
GROQ_MODEL = "llama3-8b-8192" # Default Groq model

# --- FastAPI App Initialization ---
app = FastAPI(
    title="CNJ DataJud Search API",
    description="API para buscar e analisar dados de processos judiciais do CNJ DataJud.",
    version="0.1.0"
)

# --- Elasticsearch Client ---
es_client = None
try:
    es_client = Elasticsearch(hosts=[{"host": ES_HOST, "port": ES_PORT, "scheme": "http"}])
    if not es_client.ping():
        raise ValueError("Connection to Elasticsearch failed!")
    logger.info("Connected to Elasticsearch successfully!")
except Exception as e:
    logger.critical(f"Could not connect to Elasticsearch: {e}", exc_info=True)

# --- Groq Client ---
groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        logger.info("Groq client initialized!")
    except Exception as e:
        logger.error(f"Could not initialize Groq client: {e}", exc_info=True)
else:
    logger.warning("GROQ_API_KEY not found in environment variables. Groq API functionality will be disabled.")


# --- Pydantic Models for Request/Response ---
class SearchQuery(BaseModel):
    query_string: Optional[str] = None
    tribunal: Optional[str] = None
    classe: Optional[str] = None
    page: int = 1
    size: int = 10

class ProcessResult(BaseModel):
    numeroProcesso: str
    dataAjuizamento: Optional[str]
    uf: Optional[str]
    grau: Optional[str]
    orgaoJulgador: Optional[dict]
    classe: Optional[dict]
    # Add other fields as needed from your ES documents

class SearchResponse(BaseModel):
    total: int
    hits: List[ProcessResult]

class AIAnalysisRequest(BaseModel):
    text: str
    prompt: Optional[str] = "Analyze the following legal text and provide a concise summary and key insights."
    model: Optional[str] = GROQ_MODEL

class AIAnalysisResponse(BaseModel):
    analysis: str
    model_used: str

# --- API Endpoints ---

@app.get("/")
async def read_root():
    logger.info("Root endpoint accessed.")
    return {"message": "Welcome to the CNJ DataJud Search API!"}

@app.post("/search", response_model=SearchResponse)
async def search_processes(search_query: SearchQuery):
    logger.info(f"Search request received: {search_query.dict()}")
    if not es_client:
        logger.error("Elasticsearch client not available for search.")
        raise HTTPException(status_code=500, detail="Elasticsearch connection not established.")

    # Build Elasticsearch query
    es_query = {
        "match_all": {}
    }
    
    must_clauses = []
    if search_query.query_string:
        must_clauses.append({
            "multi_match": {
                "query": search_query.query_string,
                "fields": ["numeroProcesso", "orgaoJulgador.nome", "classe.nome", "partes.pessoa.nome", "advogados.nome"]
            }
        })
    if search_query.tribunal:
        must_clauses.append({"match": {"orgaoJulgador.nome.keyword": search_query.tribunal}})
    if search_query.classe:
        must_clauses.append({"match": {"classe.nome.keyword": search_query.classe}})

    if must_clauses:
        es_query = {"bool": {"must": must_clauses}}

    # Pagination
    from_ = (search_query.page - 1) * search_query.size
    
    try:
        logger.debug(f"Executing ES search query: {es_query} from: {from_} size: {search_query.size}")
        response = es_client.search(
            index=ES_INDEX,
            body={
                "query": es_query,
                "from": from_,
                "size": search_query.size
            }
        )
        
        total_hits = response["hits"]["total"]["value"]
        results = []
        for hit in response["hits"]["hits"]:
            results.append(ProcessResult(**hit["_source"]))
            
        logger.info(f"Search completed. Total hits: {total_hits}, returned: {len(results)}")
        return SearchResponse(total=total_hits, hits=results)

    except Exception as e:
        logger.error(f"Error during Elasticsearch search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during search: {e}")

@app.post("/aggregations")
async def get_aggregations():
    logger.info("Aggregation request received.")
    if not es_client:
        logger.error("Elasticsearch client not available for aggregations.")
        raise HTTPException(status_code=500, detail="Elasticsearch connection not established.")
    
    try:
        response = es_client.search(
            index=ES_INDEX,
            body={
                "size": 0, # We only want aggregations, not hits
                "aggs": {
                    "tribunals": {
                        "terms": {"field": "orgaoJulgador.nome.keyword", "size": 10}
                    },
                    "classes": {
                        "terms": {"field": "classe.nome.keyword", "size": 10}
                    },
                    "uf": {
                        "terms": {"field": "uf.keyword", "size": 10}
                    }
                }
            }
        )
        
        logger.info("Aggregations completed.")
        return {
            "tribunals": [{"key": bucket["key"], "doc_count": bucket["doc_count"]} for bucket in response["aggregations"]["tribunals"]["buckets"]],
            "classes": [{"key": bucket["key"], "doc_count": bucket["doc_count"]} for bucket in response["aggregations"]["classes"]["buckets"]],
            "uf": [{"key": bucket["key"], "doc_count": bucket["doc_count"]} for bucket in response["aggregations"]["uf"]["buckets"]]
        }
    except Exception as e:
        logger.error(f"Error during aggregation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during aggregation: {e}")

@app.post("/ai-analyze", response_model=AIAnalysisResponse)
async def ai_analyze_text(request: AIAnalysisRequest):
    logger.info(f"AI analysis request received for text length: {len(request.text)}")
    if not groq_client:
        logger.error("Groq API client not initialized. GROQ_API_KEY might be missing.")
        raise HTTPException(status_code=503, detail="Groq API client not initialized. Please set GROQ_API_KEY environment variable.")
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": request.prompt,
                },
                {
                    "role": "user",
                    "content": request.text,
                },
            ],
            model=request.model,
            temperature=0.7,
            max_tokens=1024,
        )
        
        analysis_content = chat_completion.choices[0].message.content
        logger.info(f"AI analysis completed using model: {request.model}")
        return AIAnalysisResponse(analysis=analysis_content, model_used=request.model)

    except Exception as e:
        logger.error(f"Error during Groq API call: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during AI analysis: {e}")
