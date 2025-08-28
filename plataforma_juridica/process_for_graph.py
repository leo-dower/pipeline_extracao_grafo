from elasticsearch import Elasticsearch
from neo4j_client import Neo4jClient
import os
import logging # Import logging module
import logging_config # Import our logging configuration

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# Elasticsearch Configuration (same as ingest_cnj_data.py)
ES_HOST = "localhost"
ES_PORT = 9200
ES_INDEX = "cnj_processes"

# Neo4j Configuration (PLACEHOLDERS - USER WILL PROVIDE)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password") # IMPORTANT: Change this!

# Initialize clients (moved inside main function or called once to handle potential connection errors)
# For now, keep global for simplicity, but better error handling for init in main
try:
    es_client = Elasticsearch(hosts=[{"host": ES_HOST, "port": ES_PORT, "scheme": "http"}])
    if not es_client.ping():
        raise ValueError("Elasticsearch connection failed during initialization!")
    logger.info("Elasticsearch client initialized for graph processing.")
except Exception as e:
    logger.critical(f"Could not initialize Elasticsearch client for graph processing: {e}", exc_info=True)
    es_client = None # Set to None if connection fails

neo4j_client = None
try:
    neo4j_client = Neo4jClient(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
except Exception as e:
    logger.critical(f"Could not initialize Neo4j client for graph processing: {e}", exc_info=True)
    # neo4j_client remains None


def extract_and_load_graph_data():
    logger.info("Starting graph data extraction and loading...")
    
    if not es_client:
        logger.error("Elasticsearch client not available. Cannot extract graph data.")
        return
    if not neo4j_client:
        logger.error("Neo4j client not available. Cannot load graph data.")
        return

    # Iterate through all documents in Elasticsearch
    # For simplicity, let's fetch a limited number of documents for now
    # In a real scenario, you'd use scroll API for large datasets
    query = {
        "query": {"match_all": {}},
        "size": 100 # Process 100 documents at a time
    }
    
    try:
        response = es_client.search(index=ES_INDEX, body=query)
        hits = response["hits"]["hits"]
        logger.info(f"Fetched {len(hits)} documents from Elasticsearch for graph processing.")
    except Exception as e:
        logger.error(f"Error fetching documents from Elasticsearch: {e}", exc_info=True)
        return

    processed_count = 0
    for hit in hits:
        process_data = hit["_source"]
        process_id = process_data.get("numeroProcesso")
        
        if not process_id:
            logger.warning(f"Skipping record due to missing 'numeroProcesso': {process_data}")
            continue

        try:
            # 1. Create/Merge Process Node
            process_node_props = {
                "numeroProcesso": process_id,
                "dataAjuizamento": process_data.get("dataAjuizamento"),
                "uf": process_data.get("uf"),
                "grau": process_data.get("grau")
                # Add other relevant process properties
            }
            neo4j_client.merge_node("Processo", "numeroProcesso", process_node_props)

            # 2. Create/Merge Tribunal Node and Relationship
            orgao_julgador = process_data.get("orgaoJulgador", {})
            if orgao_julgador:
                tribunal_name = orgao_julgador.get("nome")
                tribunal_codigo = orgao_julgador.get("codigo")
                if tribunal_name and tribunal_codigo:
                    tribunal_node_props = {"nome": tribunal_name, "codigo": tribunal_codigo}
                    neo4j_client.merge_node("Tribunal", "codigo", tribunal_node_props)
                    neo4j_client.create_relationship(
                        "Processo", "numeroProcesso", process_id,
                        "Tribunal", "codigo", tribunal_codigo,
                        "JULGADO_POR"
                    )

            # 3. Create/Merge Classe Processual Node and Relationship
            classe_processual = process_data.get("classe", {})
            if classe_processual:
                classe_nome = classe_processual.get("nome")
                classe_codigo = classe_processual.get("codigo")
                if classe_nome and classe_codigo:
                    classe_node_props = {"nome": classe_nome, "codigo": classe_codigo}
                    neo4j_client.merge_node("ClasseProcessual", "codigo", classe_node_props)
                    neo4j_client.create_relationship(
                        "Processo", "numeroProcesso", process_id,
                        "ClasseProcessual", "codigo", classe_codigo,
                        "PERTENCE_A_CLASSE"
                    )

            # 4. Extract and Create/Merge Parties and Relationships
            partes = process_data.get("partes", [])
            for parte in partes:
                pessoa = parte.get("pessoa", {})
                if pessoa:
                    nome_parte = pessoa.get("nome")
                    tipo_pessoa = pessoa.get("tipoPessoa") # FISICA or JURIDICA
                    documento = pessoa.get("documento") # CPF/CNPJ, often masked or sensitive

                    if nome_parte:
                        label = "PessoaFisica" if tipo_pessoa == "FISICA" else "PessoaJuridica"
                        parte_node_props = {"nome": nome_parte, "tipoPessoa": tipo_pessoa}
                        if documento:
                            parte_node_props["documento"] = documento # Store if not sensitive

                        neo4j_client.merge_node(label, "nome", parte_node_props)

                        neo4j_client.create_relationship(
                            "Processo", "numeroProcesso", process_id,
                            label, "nome", nome_parte,
                            "TEM_PARTE", {"tipoParticipacao": parte.get("tipoParticipacao")}
                        )

                        # Extract and Create/Merge Lawyers and Relationships
                        advogados = parte.get("advogados", [])
                        for advogado in advogados:
                            nome_advogado = advogado.get("nome")
                            oab = advogado.get("oab")
                            
                            if nome_advogado and oab:
                                advogado_node_props = {"nome": nome_advogado, "oab": oab}
                                neo4j_client.merge_node("Advogado", "oab", advogado_node_props)

                                neo4j_client.create_relationship(
                                    "Advogado", "oab", oab,
                                    label, "nome", nome_parte,
                                    "REPRESENTA"
                                )
                                neo4j_client.create_relationship(
                                    "Advogado", "oab", oab,
                                    "Processo", "numeroProcesso", process_id,
                                    "ATUA_EM"
                                )
            processed_count += 1
            logger.info(f"Successfully processed process {process_id} for graph.")
        except Exception as e:
            logger.error(f"Error processing process {process_id} for graph: {e}", exc_info=True)
    
    logger.info(f"Graph data extraction and loading completed. Total processes processed: {processed_count}")

if __name__ == "__main__":
    logger.info("Starting process_for_graph.py script.")
    try:
        extract_and_load_graph_data()
    except Exception as e:
        logger.critical(f"Script terminated due to unhandled error: {e}", exc_info=True)
    finally:
        if neo4j_client:
            neo4j_client.close()
    logger.info("Finished process_for_graph.py script.")
