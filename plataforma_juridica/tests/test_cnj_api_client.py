import pytest
import requests
import requests_mock
from cnj_api_client import CNJAPIClient
import logging # Import logging

# Ensure logging is set up for tests
import logging_config

@pytest.fixture
def cnj_client():
    return CNJAPIClient()

# Fixture to capture logs
@pytest.fixture
def caplog_fixture(caplog):
    caplog.set_level(logging.DEBUG) # Capture all levels
    return caplog

def test_search_success(cnj_client, requests_mock, caplog_fixture):
    mock_response = {"hits": {"hits": [{"_source": {"numeroProcesso": "123"}}]}}
    requests_mock.post(
        f"{cnj_client.BASE_URL}api_publica_tjsp/_search",
        json=mock_response,
        status_code=200
    )
    query = {"query": {"match_all": {}}}
    response = cnj_client.search("api_publica_tjsp/_search", query)
    assert response == mock_response
    assert "Sending request to CNJ API" in caplog_fixture.text
    assert "Received response from CNJ API" in caplog_fixture.text

def test_search_http_error(cnj_client, requests_mock, caplog_fixture):
    requests_mock.post(
        f"{cnj_client.BASE_URL}api_publica_tjsp/_search",
        status_code=404,
        text="Not Found"
    )
    query = {"query": {"match_all": {}}}
    response = cnj_client.search("api_publica_tjsp/_search", query)
    assert response is None
    assert "HTTP error occurred during CNJ API call" in caplog_fixture.text
    assert caplog_fixture.records[0].levelname == "ERROR" # Check log level

def test_search_connection_error(cnj_client, requests_mock, caplog_fixture):
    requests_mock.post(
        f"{cnj_client.BASE_URL}api_publica_tjsp/_search",
        exc=requests.exceptions.ConnectionError("Mocked connection error")
    )
    query = {"query": {"match_all": {}}}
    response = cnj_client.search("api_publica_tjsp/_search", query)
    assert response is None
    assert "Connection error occurred during CNJ API call" in caplog_fixture.text
    assert caplog_fixture.records[0].levelname == "ERROR"

def test_search_timeout_error(cnj_client, requests_mock, caplog_fixture):
    requests_mock.post(
        f"{cnj_client.BASE_URL}api_publica_tjsp/_search",
        exc=requests.exceptions.Timeout("Mocked timeout error")
    )
    query = {"query": {"match_all": {}}}
    response = cnj_client.search("api_publica_tjsp/_search", query)
    assert response is None
    assert "Timeout error occurred during CNJ API call" in caplog_fixture.text
    assert caplog_fixture.records[0].levelname == "ERROR"

def test_search_generic_request_error(cnj_client, requests_mock, caplog_fixture):
    requests_mock.post(
        f"{cnj_client.BASE_URL}api_publica_tjsp/_search",
        exc=requests.exceptions.RequestException("Mocked generic error")
    )
    query = {"query": {"match_all": {}}}
    response = cnj_client.search("api_publica_tjsp/_search", query)
    assert response is None
    assert "An unexpected error occurred during CNJ API call" in caplog_fixture.text
    assert caplog_fixture.records[0].levelname == "ERROR"