import pytest
from unittest.mock import MagicMock, patch
from neo4j_client import Neo4jClient

# Mock the GraphDatabase driver at the module level
@pytest.fixture(autouse=True)
def mock_graph_database():
    with patch('neo4j_client.GraphDatabase') as mock_driver:
        yield mock_driver

@pytest.fixture
def neo4j_client_instance(mock_graph_database):
    # Initialize Neo4jClient with dummy credentials, as the driver is mocked
    client = Neo4jClient("bolt://localhost:7687", "user", "password")
    return client

def test_neo4j_client_initialization(mock_graph_database):
    client = Neo4jClient("bolt://localhost:7687", "user", "password")
    mock_graph_database.driver.assert_called_once_with("bolt://localhost:7687", auth=("user", "password"))
    assert client.driver is not None

def test_close_connection(neo4j_client_instance):
    neo4j_client_instance.driver.close = MagicMock()
    neo4j_client_instance.close()
    neo4j_client_instance.driver.close.assert_called_once()

def test_run_query(neo4j_client_instance):
    mock_session = MagicMock()
    mock_result = [MagicMock(record={"name": "test"})]
    mock_session.run.return_value = mock_result
    neo4j_client_instance.driver.session.return_value.__enter__.return_value = mock_session

    query = "MATCH (n) RETURN n"
    result = neo4j_client_instance.run_query(query)

    mock_session.run.assert_called_once_with(query, None)
    assert result == mock_result

def test_create_node(neo4j_client_instance):
    mock_session = MagicMock()
    mock_record = MagicMock(record={"n": {"name": "TestNode"}})
    mock_session.run.return_value = [mock_record]
    neo4j_client_instance.driver.session.return_value.__enter__.return_value = mock_session

    label = "TestLabel"
    properties = {"name": "TestNode"}
    node = neo4j_client_instance.create_node(label, properties)

    expected_query = f"CREATE (n:{label} $properties) RETURN n"
    mock_session.run.assert_called_once_with(expected_query, {"properties": properties})
    assert node == {"name": "TestNode"}

def test_merge_node(neo4j_client_instance):
    mock_session = MagicMock()
    mock_record = MagicMock(record={"n": {"id_prop": "test_id", "other_prop": "value"}})
    mock_session.run.return_value = [mock_record]
    neo4j_client_instance.driver.session.return_value.__enter__.return_value = mock_session

    label = "TestLabel"
    identifier_property = "id_prop"
    properties = {"id_prop": "test_id", "other_prop": "value"}
    node = neo4j_client_instance.merge_node(label, identifier_property, properties)

    expected_query_start = f"MERGE (n:{label} {{{identifier_property}: $id_value}}) "
    mock_session.run.assert_called_once()
    args, kwargs = mock_session.run.call_args
    assert args[0].startswith(expected_query_start)
    assert kwargs["parameters"]["id_value"] == "test_id"
    assert kwargs["parameters"]["properties"] == {"id_prop": "test_id", "other_prop": "value"}
    assert node == {"id_prop": "test_id", "other_prop": "value"}

def test_create_relationship(neo4j_client_instance):
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

    neo4j_client_instance.create_relationship(
        from_label, from_id_prop, from_id_val,
        to_label, to_id_prop, to_id_val,
        rel_type, rel_properties
    )

    expected_query_start = f"MERGE (a:{from_label} {{{from_id_prop}: $from_id_val}}) MERGE (b:{to_label} {{{to_id_prop}: $to_id_val}}) MERGE (a)-[r:{rel_type} $rel_properties]->(b) RETURN a, r, b"
    mock_session.run.assert_called_once_with(expected_query_start, {
        "from_id_val": from_id_val,
        "to_id_val": to_id_val,
        "rel_properties": rel_properties
    })
