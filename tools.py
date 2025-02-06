from langchain_neo4j import Neo4jGraph

import os
from dotenv import load_dotenv

load_dotenv()

def query_neo4j_graph(query, params=None):
    # Load LangChain Neo4jGraph instance 
    graph = Neo4jGraph(url=os.getenv("NEO4J_URI"), username=os.getenv("NEO4J_USERNAME"), password=os.getenv("NEO4J_PASSWORD"))
    return graph.query(query, params)