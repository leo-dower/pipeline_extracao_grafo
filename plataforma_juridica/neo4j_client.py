from neo4j import GraphDatabase
import logging # Import logging module
import logging_config # Import our logging configuration

# Get a logger instance for this module
logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self, uri, user, password):
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity() # Verify connection
            logger.info("Neo4j client initialized and connected successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j at {uri}: {e}", exc_info=True)
            raise # Re-raise to indicate connection failure

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed.")

    def run_query(self, query, parameters=None):
        """
        Executes a Cypher query.
        """
        if not self.driver:
            logger.error("Neo4j driver is not initialized. Cannot run query.")
            return []
        
        logger.debug(f"Running Cypher query: {query} with parameters: {parameters}")
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters)
                records = [record for record in result]
                logger.debug(f"Query executed successfully. Records returned: {len(records)}")
                return records
        except Exception as e:
            logger.error(f"Error running Cypher query: {query} - {e}", exc_info=True)
            return []

    def create_node(self, label, properties):
        """
        Creates a node with the given label and properties.
        Returns the created node's properties.
        """
        query = f"CREATE (n:{label} $properties) RETURN n"
        logger.debug(f"Attempting to create node: {label} with properties: {properties}")
        result = self.run_query(query, {"properties": properties})
        if result:
            logger.info(f"Node '{label}' created with properties: {properties}")
            return result[0]["n"]
        logger.error(f"Failed to create node: {label} with properties: {properties}")
        return None

    def merge_node(self, label, identifier_property, properties):
        """
        Merges a node, creating it if it doesn't exist, based on an identifier property.
        Returns the merged node's properties.
        """
        query = (
            f"MERGE (n:{label} {{{identifier_property}: $id_value}}) "
            f"ON CREATE SET n = $properties "
            f"ON MATCH SET n += $properties " # Update properties on match
            f"RETURN n"
        )
        properties_with_id = {**properties, identifier_property: properties[identifier_property]}
        logger.debug(f"Attempting to merge node: {label} with identifier {identifier_property}={properties[identifier_property]} and properties: {properties_with_id}")
        result = self.run_query(query, {"id_value": properties[identifier_property], "properties": properties_with_id})
        if result:
            logger.info(f"Node '{label}' merged with identifier {identifier_property}={properties[identifier_property]}")
            return result[0]["n"]
        logger.error(f"Failed to merge node: {label} with identifier {identifier_property}={properties[identifier_property]}")
        return None

    def create_relationship(self, from_label, from_id_prop, from_id_val,
                           to_label, to_id_prop, to_id_val,
                           rel_type, rel_properties=None):
        """
        Creates a relationship between two nodes. Nodes are merged if they don't exist.
        """
        query = (
            f"MERGE (a:{from_label} {{{from_id_prop}: $from_id_val}}) "
            f"MERGE (b:{to_label} {{{to_id_prop}: $to_id_val}}) "
            f"MERGE (a)-[r:{rel_type} $rel_properties]->(b) "
            f"RETURN a, r, b"
        )
        parameters = {
            "from_id_val": from_id_val,
            "to_id_val": to_id_val,
            "rel_properties": rel_properties if rel_properties else {}
        }
        logger.debug(f"Attempting to create relationship: ({from_label})-[:{rel_type}]->({to_label}) between {from_id_prop}={from_id_val} and {to_id_prop}={to_id_val}")
        result = self.run_query(query, parameters)
        if result:
            logger.info(f"Relationship '{rel_type}' created between {from_label} ({from_id_val}) and {to_label} ({to_id_val})")
            return result
        logger.error(f"Failed to create relationship: ({from_label})-[:{rel_type}]->({to_label}) between {from_id_prop}={from_id_val} and {to_id_prop}={to_id_val}")
        return None