"""
EDAI4 - Neo4j Client
Optional Neo4j graph database integration
"""

from typing import Any, Optional
from src.utils import get_logger, config

logger = get_logger(__name__)


class Neo4jClient:
    """
    Neo4j database client for P&ID graph storage.
    This is an optional component - the system works with in-memory graphs.
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "neo4j",
    ):
        """
        Initialize Neo4j client.

        Args:
            uri: Neo4j connection URI (bolt://localhost:7687)
            user: Username
            password: Password
            database: Database name
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver = None
        self._connected = False

        # Try loading from config/env
        settings = config.get_settings()
        if settings:
            neo4j_config = settings.get("topology", {}).get("neo4j", {})
            self.uri = uri or neo4j_config.get("uri")
            self.database = neo4j_config.get("database", database)

        # Load from environment
        import os
        self.uri = self.uri or os.getenv("NEO4J_URI")
        self.user = self.user or os.getenv("NEO4J_USER", "neo4j")
        self.password = self.password or os.getenv("NEO4J_PASSWORD")

        logger.info("Neo4jClient initialized (not connected)")

    def connect(self) -> bool:
        """
        Connect to Neo4j database.

        Returns:
            True if connected successfully
        """
        if not self.uri or not self.password:
            logger.warning("Neo4j credentials not configured")
            return False

        try:
            from neo4j import GraphDatabase

            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )

            # Test connection
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1")

            self._connected = True
            logger.info(f"Connected to Neo4j at {self.uri}")
            return True

        except ImportError:
            logger.error("neo4j package not installed. Run: pip install neo4j")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False

    def disconnect(self) -> None:
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            self._connected = False
            logger.info("Disconnected from Neo4j")

    @property
    def is_connected(self) -> bool:
        """Check if connected to database."""
        return self._connected

    def save_graph(self, graph) -> bool:
        """
        Save a PIDGraph to Neo4j.

        Args:
            graph: PIDGraph object

        Returns:
            True if saved successfully
        """
        if not self._connected:
            if not self.connect():
                return False

        try:
            with self.driver.session(database=self.database) as session:
                # Clear existing data (optional)
                # session.run("MATCH (n) DETACH DELETE n")

                # Create nodes
                for node in graph.nodes.values():
                    cypher = """
                    CREATE (n:PIDNode {
                        id: $id,
                        type: $type,
                        label: $label,
                        tag: $tag,
                        x: $x,
                        y: $y
                    })
                    """
                    session.run(
                        cypher,
                        id=node.id,
                        type=node.node_type.value,
                        label=node.label,
                        tag=node.tag or "",
                        x=node.x,
                        y=node.y,
                    )

                # Create edges
                for edge in graph.edges:
                    cypher = """
                    MATCH (a:PIDNode {id: $source})
                    MATCH (b:PIDNode {id: $target})
                    CREATE (a)-[r:CONNECTED {type: $type, weight: $weight}]->(b)
                    """
                    session.run(
                        cypher,
                        source=edge.source_id,
                        target=edge.target_id,
                        type=edge.edge_type.value,
                        weight=edge.weight,
                    )

            logger.info(f"Saved graph to Neo4j: {graph.node_count} nodes, {graph.edge_count} edges")
            return True

        except Exception as e:
            logger.error(f"Failed to save graph: {e}")
            return False

    def query(self, cypher: str, parameters: dict = None) -> list[dict]:
        """
        Execute a Cypher query.

        Args:
            cypher: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        if not self._connected:
            if not self.connect():
                return []

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(cypher, parameters or {})
                return [record.data() for record in result]

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    def get_instruments(self) -> list[dict]:
        """Get all instrument nodes."""
        cypher = """
        MATCH (n:PIDNode)
        WHERE n.type = 'instrument'
        RETURN n
        """
        return self.query(cypher)

    def get_instrument_neighbors(self, tag: str) -> list[dict]:
        """Get neighbors of an instrument by tag."""
        cypher = """
        MATCH (n:PIDNode {tag: $tag})-[r]-(m:PIDNode)
        RETURN n, r, m
        """
        return self.query(cypher, {"tag": tag})

    def clear_database(self) -> bool:
        """Clear all data from the database."""
        try:
            self.query("MATCH (n) DETACH DELETE n")
            logger.info("Database cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            return False
