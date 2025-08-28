import pytest
from unittest.mock import MagicMock, patch
from neo4j_client import Neo4jClient
import logging # Import logging

# Ensure logging is set up for tests
import logging_config

# Mock the GraphDatabase driver at the module level
@pytest.fixture(autouse=True)
def mock_graph_database():
    with patch('neo4j_client.GraphDatabase') as mock_driver:
        # Mock the verify_connectivity method
        mock_driver.driver.return_value.verify_connectivity = MagicMock()
        yield mock_driver

@pytest.fixture
def neo4j_client_instance(mock_graph_database):
    # Initialize Neo4jClient with dummy credentials, as the driver is mocked
    client = Neo4jClient("bolt://localhost:7687", "user", "password")
    return client

# Fixture to capture logs
@pytest.fixture
def caplog_fixture(caplog):
    caplog.set_level(logging.DEBUG) # Capture all levels
    return caplog

def test_neo4j_client_initialization_success(mock_graph_database, caplog_fixture):
    client = Neo4jClient("bolt://localhost:7687", "user", "password")
    mock_graph_database.driver.assert_called_once_with("bolt://localhost:7687", auth=("user", "password"))
    assert client.driver is not None
    assert "Neo4j client initialized and connected successfully." in caplog_fixture.text
    assert caplog_fixture.records[0].levelname == "INFO"

def test_neo4j_client_initialization_failure(mock_graph_database, caplog_fixture):
    mock_graph_database.driver.side_effect = Exception("Connection failed")
    with pytest.raises(Exception, match="Connection failed"):
        Neo4jClient("bolt://localhost:7687", "user", "password")
    assert "Failed to connect to Neo4j" in caplog_fixture.text
    assert caplog_fixture.records[0].levelname == "ERROR"

def test_close_connection(neo4j_client_instance, caplog_fixture):
    neo4j_client_instance.driver.close = MagicMock()
    neo4j_client_instance.close()
    neo4j_client_instance.driver.close.assert_called_once()
    assert "Neo4j connection closed." in caplog_fixture.text
    assert caplog_fixture.records[0].levelname == "INFO"

def test_run_query_success(neo4j_client_instance, caplog_fixture):
    mock_session = MagicMock()
    mock_result = [MagicMock(record={"name": "test"})]
    mock_session.run.return_value = mock_result
    neo4j_client_instance.driver.session.return_value.__enter__.return_value = mock_session

    query = "MATCH (n) RETURN n"
    result = neo4j_client_instance.run_query(query)

    mock_session.run.assert_called_once_with(query, None)
    assert result == mock_result
    assert "Running Cypher query:" in caplog_fixture.text
    assert "Query executed successfully." in caplog_fixture.text

def test_run_query_failure(neo4j_client_instance, caplog_fixture):
    mock_session = MagicMock()
    mock_session.run.side_effect = Exception("Query execution error")
    neo4j_client_instance.driver.session.return_value.__enter__.return_value = mock_session

    query = "MATCH (n) RETURN n"
    result = neo4j_client_instance.run_query(query)

    assert result == []
    assert "Error running Cypher query:" in caplog_fixture.text
    assert caplog_fixture.records[0].levelname == "ERROR"

def test_create_node_success(neo4j_client_instance, caplog_fixture):
    mock_session = MagicMock()
    mock_record = MagicMock(record={"n": {"name": "TestNode"}})
    mock_session.run.return_value = [mock_record]
    neo4j_client_instance.driver.session.return_value.__enter__.return_value = mock_session

    label = "TestLabel"
    properties = {"name": "TestNode"}
    node = neo4j_client_instance.create_node(label, properties)

    assert node == {"name": "TestNode"}
    assert "Attempting to create node:" in caplog_fixture.text
    assert "Node 'TestLabel' created with properties:" in caplog_fixture.text
    assert caplog_fixture.records[0].levelname == "DEBUG"
    assert caplog_fixture.records[1].levelname == "INFO"

def test_create_node_failure(neo4j_client_instance, caplog_fixture):
    mock_session = MagicMock()
    mock_session.run.return_value = [] # Simulate no result
    neo4j_client_instance.driver.session.return_value.__enter__.return_value = mock_session

    label = "TestLabel"
    properties = {"name": "TestNode"}
    node = neo4j_client_instance.create_node(label, properties)

    assert node is None
    assert "Failed to create node:" in caplog_fixture.text
    assert caplog_fixture.records[0].levelname == "DEBUG"
    assert caplog_fixture.records[1].levelname == "ERROR"

def test_merge_node_success(neo4j_client_instance, caplog_fixture):
    mock_session = MagicMock()
    mock_record = MagicMock(record={"n": {"id_prop": "test_id", "other_prop": "value"}})
    mock_session.run.return_value = [mock_record]
    neo4j_client_instance.driver.session.return_value.__enter__.return_value = mock_session

    label = "TestLabel"
    identifier_property = "id_prop"
    properties = {"id_prop": "test_id", "other_prop": "value"}
    node = neo4j_client_instance.merge_node(label, identifier_property, properties)

    assert node == {"id_prop": "test_id", "other_prop": "value"}
    assert "Attempting to merge node:" in caplog_fixture.text
    assert "Node 'TestLabel' merged with identifier" in caplog_fixture.text
    assert caplog_fixture.records[0].levelname == "DEBUG"
    assert caplog_fixture.records[1].levelname == "INFO"

def test_merge_node_failure(neo4j_client_instance, caplog_fixture):
    mock_session = MagicMock()
    mock_session.run.return_value = [] # Simulate no result
    neo4j_client_instance.driver.session.return_value.__enter__.return_value = mock_session

    label = "TestLabel"
    identifier_property = "id_prop"
    properties = {"id_prop": "test_id", "other_prop": "value"}
    node = neo4j_client_instance.merge_node(label, identifier_property, properties)

    assert node is None
    assert "Failed to merge node:" in caplog_fixture.text
    assert caplog_fixture.records[0].levelname == "DEBUG"
    assert caplog_fixture.records[1].levelname == "ERROR"

def test_create_relationship_success(neo4j_client_instance, caplog_fixture):
    mock_session = MagicMock()
    mock_session.run.return_value = [MagicMock()] # Return a dummy record
    neo4j_client_instance.driver.session.return_value.__enter__.return_value = mock_session

    from_label = "NodeA"
    from_id_prop = "idA"
    from_id_val = "123"
    to_label = "NodeB"
    to_id_prop = "idB"
    to_id_val = "456"
    rel_type = "RELATES_TO"
    rel_properties = {"weight": 1}

    result = neo4j_client_instance.create_relationship(
        from_label, from_id_prop, from_id_val,
        to_label, to_id_prop, to_id_val,
        rel_type, rel_properties
    )

    assert result is not None
    assert "Attempting to create relationship:" in caplog_fixture.text
    assert "Relationship 'RELATES_TO' created between" in caplog_fixture.text
    assert caplog_fixture.records[0].levelname == "DEBUG"
    assert caplog_fixture.records[1].levelname == "INFO"

def test_create_relationship_failure(neo4j_client_instance, caplog_fixture):
    mock_session = MagicMock()
    mock_session.run.return_value = [] # Simulate no result
    neo4j_client_instance.driver.session.return_value.__enter__.return_value = mock_session

    from_label = "NodeA"
    from_id_prop = "idA"
    from_id_val = "123"
    to_label = "NodeB"
    to_id_prop = "idB"
    to_id_val = "456"
    rel_type = "RELATES_TO"
    rel_properties = {"weight": 1}

    result = neo4j_client_instance.create_relationship(
        from_label, from_id_prop, from_id_val,
        to_label, to_id_prop, to_id_val,
        rel_type, rel_properties
    )

    assert result is None
    assert "Failed to create relationship:" in caplog_fixture.text
    assert caplog_fixture.records[0].levelname == "DEBUG"
    assert caplog_fixture.records[1].levelname == "ERROR"