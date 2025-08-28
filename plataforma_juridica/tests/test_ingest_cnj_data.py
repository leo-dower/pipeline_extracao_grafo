import pytest
from unittest.mock import MagicMock, patch
from ingest_cnj_data import ensure_index_exists, ingest_data_for_tribunal, ES_INDEX

@pytest.fixture(autouse=True)
def mock_clients():
    """Mocks Elasticsearch and CNJAPIClient for all tests in this module."""
    with patch('ingest_cnj_data.es_client') as mock_es_client, \
         patch('ingest_cnj_data.cnj_client') as mock_cnj_client:
        yield mock_es_client, mock_cnj_client

def test_ensure_index_exists_creates_index(mock_clients, capsys):
    mock_es_client, _ = mock_clients
    mock_es_client.indices.exists.return_value = False
    
    ensure_index_exists()
    
    mock_es_client.indices.exists.assert_called_once_with(index=ES_INDEX)
    mock_es_client.indices.create.assert_called_once_with(index=ES_INDEX)
    captured = capsys.readouterr()
    assert f"Elasticsearch index '{ES_INDEX}' created." in captured.out

def test_ensure_index_exists_does_not_create_if_exists(mock_clients, capsys):
    mock_es_client, _ = mock_clients
    mock_es_client.indices.exists.return_value = True
    
    ensure_index_exists()
    
    mock_es_client.indices.exists.assert_called_once_with(index=ES_INDEX)
    mock_es_client.indices.create.assert_not_called()
    captured = capsys.readouterr()
    assert f"Elasticsearch index '{ES_INDEX}' already exists." in captured.out

def test_ingest_data_for_tribunal_no_data(mock_clients, capsys):
    mock_es_client, mock_cnj_client = mock_clients
    mock_cnj_client.search.return_value = None # No data from API
    
    ingest_data_for_tribunal("api_publica_test/_search")
    
    mock_cnj_client.search.assert_called_once()
    mock_es_client.index.assert_not_called()
    captured = capsys.readouterr()
    assert "No more data or error for api_publica_test/_search." in captured.out
    assert "Total new records indexed: 0" in captured.out

def test_ingest_data_for_tribunal_single_page_new_records(mock_clients, capsys):
    mock_es_client, mock_cnj_client = mock_clients
    mock_cnj_client.search.return_value = {
        "hits": {
            "hits": [
                {"_source": {"numeroProcesso": "proc1"}, "sort": [1]},
                {"_source": {"numeroProcesso": "proc2"}, "sort": [2]}
            ],
            "total": {"value": 2}
        }
    }
    mock_es_client.exists.return_value = False # Records do not exist
    
    ingest_data_for_tribunal("api_publica_test/_search")
    
    mock_cnj_client.search.assert_called_once()
    assert mock_es_client.index.call_count == 2
    mock_es_client.index.assert_any_call(index=ES_INDEX, id="proc1", document={"numeroProcesso": "proc1"})
    mock_es_client.index.assert_any_call(index=ES_INDEX, id="proc2", document={"numeroProcesso": "proc2"})
    captured = capsys.readouterr()
    assert "Total new records indexed: 2" in captured.out

def test_ingest_data_for_tribunal_deduplication(mock_clients, capsys):
    mock_es_client, mock_cnj_client = mock_clients
    mock_cnj_client.search.return_value = {
        "hits": {
            "hits": [
                {"_source": {"numeroProcesso": "proc1"}, "sort": [1]},
                {"_source": {"numeroProcesso": "proc2"}, "sort": [2]}
            ],
            "total": {"value": 2}
        }
    }
    # proc1 exists, proc2 does not
    mock_es_client.exists.side_effect = [True, False] 
    
    ingest_data_for_tribunal("api_publica_test/_search")
    
    mock_cnj_client.search.assert_called_once()
    assert mock_es_client.index.call_count == 1 # Only proc2 should be indexed
    mock_es_client.index.assert_called_once_with(index=ES_INDEX, id="proc2", document={"numeroProcesso": "proc2"})
    captured = capsys.readouterr()
    assert "Total new records indexed: 1" in captured.out

def test_ingest_data_for_tribunal_pagination(mock_clients, capsys):
    mock_es_client, mock_cnj_client = mock_clients
    # First page
    mock_cnj_client.search.side_effect = [
        {
            "hits": {
                "hits": [
                    {"_source": {"numeroProcesso": "proc1"}, "sort": [1]},
                    {"_source": {"numeroProcesso": "proc2"}, "sort": [2]}
                ],
                "total": {"value": 3} # Indicate more data
            }
        },
        # Second page
        {
            "hits": {
                "hits": [
                    {"_source": {"numeroProcesso": "proc3"}, "sort": [3]}
                ],
                "total": {"value": 3}
            }
        }
    ]
    mock_es_client.exists.return_value = False # All new records
    
    ingest_data_for_tribunal("api_publica_test/_search", max_records=2) # Simulate max_records for pagination test
    
    assert mock_cnj_client.search.call_count == 2 # Two API calls for pagination
    assert mock_es_client.index.call_count == 3
    mock_es_client.index.assert_any_call(index=ES_INDEX, id="proc1", document={"numeroProcesso": "proc1"})
    mock_es_client.index.assert_any_call(index=ES_INDEX, id="proc2", document={"numeroProcesso": "proc2"})
    mock_es_client.index.assert_any_call(index=ES_INDEX, id="proc3", document={"numeroProcesso": "proc3"})
    captured = capsys.readouterr()
    assert "Total new records indexed: 3" in captured.out

def test_ingest_data_for_tribunal_missing_process_number(mock_clients, capsys):
    mock_es_client, mock_cnj_client = mock_clients
    mock_cnj_client.search.return_value = {
        "hits": {
            "hits": [
                {"_source": {"someOtherField": "value"}, "sort": [1]} # Missing numeroProcesso
            ],
            "total": {"value": 1}
        }
    }
    
    ingest_data_for_tribunal("api_publica_test/_search")
    
    mock_es_client.index.assert_not_called()
    captured = capsys.readouterr()
    assert "Skipping record due to missing 'numeroProcesso': {'someOtherField': 'value'}" in captured.out
    assert "Total new records indexed: 0" in captured.out
