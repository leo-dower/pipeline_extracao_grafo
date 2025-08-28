from neo4j import GraphDatabase

class Neo4jClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print("Neo4j client initialized.")

    def close(self):
        self.driver.close()
        print("Neo4j connection closed.")

    def run_query(self, query, parameters=None):
        """
        Executes a Cypher query.
        """
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]

    def create_node(self, label, properties):
        """
        Creates a node with the given label and properties.
        Returns the created node's properties.
        """
        query = f"CREATE (n:{label} $properties) RETURN n"
        result = self.run_query(query, {"properties": properties})
        return result[0]["n"] if result else None

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
        # Ensure the identifier property is part of the properties passed for creation/update
        properties_with_id = {**properties, identifier_property: properties[identifier_property]}
        result = self.run_query(query, {"id_value": properties[identifier_property], "properties": properties_with_id})
        return result[0]["n"] if result else None

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
        return self.run_query(query, parameters)
