import pytest
from unittest.mock import MagicMock, patch
from process_for_graph import extract_and_load_graph_data, ES_INDEX

@pytest.fixture(autouse=True)
def mock_clients():
    """Mocks Elasticsearch and Neo4j clients for all tests in this module."""
    with patch('process_for_graph.es_client') as mock_es_client, \
         patch('process_for_graph.neo4j_client') as mock_neo4j_client:
        yield mock_es_client, mock_neo4j_client

def test_extract_and_load_graph_data_no_es_data(mock_clients, capsys):
    mock_es_client, mock_neo4j_client = mock_clients
    mock_es_client.search.return_value = {"hits": {"hits": []}} # No hits from ES

    extract_and_load_graph_data()

    mock_es_client.search.assert_called_once_with(index=ES_INDEX, body={"query": {"match_all": {}}, "size": 100})
    mock_neo4j_client.merge_node.assert_not_called()
    mock_neo4j_client.create_relationship.assert_not_called()
    captured = capsys.readouterr()
    assert "Starting graph data extraction and loading..." in captured.out
    assert "Graph data extraction and loading completed." in captured.out

def test_extract_and_load_graph_data_single_process(mock_clients):
    mock_es_client, mock_neo4j_client = mock_clients
    sample_process_data = {
        "numeroProcesso": "12345",
        "dataAjuizamento": "2023-01-01",
        "uf": "SP",
        "grau": "1",
        "orgaoJulgador": {"nome": "TJSP", "codigo": "123"},
        "classe": {"nome": "Procedimento Comum Cível", "codigo": "111"},
        "partes": [
            {"pessoa": {"nome": "Alice", "tipoPessoa": "FISICA", "documento": "111.222.333-44"}, "tipoParticipacao": "AUTOR"},
            {"pessoa": {"nome": "Bob", "tipoPessoa": "FISICA"}, "tipoParticipacao": "REU", "advogados": [{"nome": "Advogado X", "oab": "SP12345"}]}
        ]
    }
    mock_es_client.search.return_value = {"hits": {"hits": [{"_source": sample_process_data}]}

    extract_and_load_graph_data()

    # Assert Process node creation
    mock_neo4j_client.merge_node.assert_any_call("Processo", "numeroProcesso", {
        "numeroProcesso": "12345", "dataAjuizamento": "2023-01-01", "uf": "SP", "grau": "1"
    })

    # Assert Tribunal node and relationship
    mock_neo4j_client.merge_node.assert_any_call("Tribunal", "codigo", {"nome": "TJSP", "codigo": "123"})
    mock_neo4j_client.create_relationship(
        "Processo", "numeroProcesso", "12345",
        "Tribunal", "codigo", "123",
        "JULGADO_POR"
    )

    # Assert ClasseProcessual node and relationship
    mock_neo4j_client.merge_node.assert_any_call("ClasseProcessual", "codigo", {"nome": "Procedimento Comum Cível", "codigo": "111"})
    mock_neo4j_client.create_relationship(
        "Processo", "numeroProcesso", "12345",
        "ClasseProcessual", "codigo", "111",
        "PERTENCE_A_CLASSE"
    )

    # Assert Parte (Alice) node and relationship
    mock_neo4j_client.merge_node.assert_any_call("PessoaFisica", "nome", {"nome": "Alice", "tipoPessoa": "FISICA", "documento": "111.222.333-44"})
    mock_neo4j_client.create_relationship(
        "Processo", "numeroProcesso", "12345",
        "PessoaFisica", "nome", "Alice",
        "TEM_PARTE", {"tipoParticipacao": "AUTOR"}
    )

    # Assert Parte (Bob) node and relationship
    mock_neo4j_client.merge_node.assert_any_call("PessoaFisica", "nome", {"nome": "Bob", "tipoPessoa": "FISICA"})
    mock_neo4j_client.create_relationship(
        "Processo", "numeroProcesso", "12345",
        "PessoaFisica", "nome", "Bob",
        "TEM_PARTE", {"tipoParticipacao": "REU"}
    )

    # Assert Advogado (Advogado X) node and relationships
    mock_neo4j_client.merge_node.assert_any_call("Advogado", "oab", {"nome": "Advogado X", "oab": "SP12345"})
    mock_neo4j_client.create_relationship(
        "Advogado", "oab", "SP12345",
        "PessoaFisica", "nome", "Bob",
        "REPRESENTA"
    )
    mock_neo4j_client.create_relationship(
        "Advogado", "oab", "SP12345",
        "Processo", "numeroProcesso", "12345",
        "ATUA_EM"
    )

def test_extract_and_load_graph_data_missing_process_number(mock_clients, capsys):
    mock_es_client, mock_neo4j_client = mock_clients
    sample_process_data = {
        "dataAjuizamento": "2023-01-01" # Missing numeroProcesso
    }
    mock_es_client.search.return_value = {"hits": {"hits": [{"_source": sample_process_data}]}

    extract_and_load_graph_data()

    mock_neo4j_client.merge_node.assert_not_called()
    mock_neo4j_client.create_relationship.assert_not_called()
    captured = capsys.readouterr()
    assert "Skipping record due to missing 'numeroProcesso':" in captured.out
