from elasticsearch import Elasticsearch
from neo4j_client import Neo4jClient
import os

# Elasticsearch Configuration (same as ingest_cnj_data.py)
ES_HOST = "localhost"
ES_PORT = 9200
ES_INDEX = "cnj_processes"
es_client = Elasticsearch(hosts=[{"host": ES_HOST, "port": ES_PORT, "scheme": "http"}])

# Neo4j Configuration (PLACEHOLDERS - USER WILL PROVIDE)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password") # IMPORTANT: Change this!

neo4j_client = Neo4jClient(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

def extract_and_load_graph_data():
    print("Starting graph data extraction and loading...")
    
    # Iterate through all documents in Elasticsearch
    # For simplicity, let's fetch a limited number of documents for now
    # In a real scenario, you'd use scroll API for large datasets
    query = {
        "query": {"match_all": {}},
        "size": 100 # Process 100 documents at a time
    }
    
    response = es_client.search(index=ES_INDEX, body=query)
    hits = response["hits"]["hits"]

    for hit in hits:
        process_data = hit["_source"]
        process_id = process_data.get("numeroProcesso")
        
        if not process_id:
            print(f"Skipping record due to missing 'numeroProcesso': {process_data}")
            continue

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
                    # Use a combination of name and type for unique identification if no document
                    # For simplicity, let's use name for now, but in real app, need better unique ID
                    # Or, if document is available and not sensitive, use it.
                    
                    # Decide on label based on tipoPessoa
                    label = "PessoaFisica" if tipo_pessoa == "FISICA" else "PessoaJuridica"
                    
                    # Use nome as identifier for now, but ideally a unique ID like CPF/CNPJ
                    # For production, handle sensitive data carefully (masking, hashing, or not storing)
                    parte_node_props = {"nome": nome_parte, "tipoPessoa": tipo_pessoa}
                    if documento:
                        parte_node_props["documento"] = documento # Store if not sensitive

                    # Merge the party node
                    neo4j_client.merge_node(label, "nome", parte_node_props) # Using nome as identifier for MERGE

                    # Create relationship between Processo and Parte
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

                            # Relationship between Advogado and Parte
                            neo4j_client.create_relationship(
                                "Advogado", "oab", oab,
                                label, "nome", nome_parte,
                                "REPRESENTA"
                            )
                            # Relationship between Advogado and Processo
                            neo4j_client.create_relationship(
                                "Advogado", "oab", oab,
                                "Processo", "numeroProcesso", process_id,
                                "ATUA_EM"
                            )
    
    print("Graph data extraction and loading completed.")

if __name__ == "__main__":
    try:
        extract_and_load_graph_data()
    finally:
        neo4j_client.close()