import pytest
import requests
import requests_mock
from cnj_api_client import CNJAPIClient

@pytest.fixture
def cnj_client():
    return CNJAPIClient()

def test_search_success(cnj_client, requests_mock):
    mock_response = {"hits": {"hits": [{"_source": {"numeroProcesso": "123"}}]}}
    requests_mock.post(
        f"{cnj_client.BASE_URL}api_publica_tjsp/_search",
        json=mock_response,
        status_code=200
    )
    query = {"query": {"match_all": {}}}
    response = cnj_client.search("api_publica_tjsp/_search", query)
    assert response == mock_response

def test_search_http_error(cnj_client, requests_mock, capsys):
    requests_mock.post(
        f"{cnj_client.BASE_URL}api_publica_tjsp/_search",
        status_code=404,
        text="Not Found"
    )
    query = {"query": {"match_all": {}}}
    response = cnj_client.search("api_publica_tjsp/_search", query)
    assert response is None
    captured = capsys.readouterr()
    assert "HTTP error occurred: 404 Client Error: Not Found for url" in captured.out

def test_search_connection_error(cnj_client, requests_mock, capsys):
    requests_mock.post(
        f"{cnj_client.BASE_URL}api_publica_tjsp/_search",
        exc=requests.exceptions.ConnectionError("Mocked connection error")
    )
    query = {"query": {"match_all": {}}}
    response = cnj_client.search("api_publica_tjsp/_search", query)
    assert response is None
    captured = capsys.readouterr()
    assert "Connection error occurred: Mocked connection error" in captured.out

def test_search_timeout_error(cnj_client, requests_mock, capsys):
    requests_mock.post(
        f"{cnj_client.BASE_URL}api_publica_tjsp/_search",
        exc=requests.exceptions.Timeout("Mocked timeout error")
    )
    query = {"query": {"match_all": {}}}
    response = cnj_client.search("api_publica_tjsp/_search", query)
    assert response is None
    captured = capsys.readouterr()
    assert "Timeout error occurred: Mocked timeout error" in captured.out

def test_search_generic_request_error(cnj_client, requests_mock, capsys):
    requests_mock.post(
        f"{cnj_client.BASE_URL}api_publica_tjsp/_search",
        exc=requests.exceptions.RequestException("Mocked generic error")
    )
    query = {"query": {"match_all": {}}}
    response = cnj_client.search("api_publica_tjsp/_search", query)
    assert response is None
    captured = capsys.readouterr()
    assert "An unexpected error occurred: Mocked generic error" in captured.out
