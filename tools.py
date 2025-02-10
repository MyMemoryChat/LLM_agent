from langchain_neo4j import Neo4jGraph
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Neo4jVector
from graphdatascience import GraphDataScience
from langchain.agents import tool

import base64
import re
import emoji

import os
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

def encode_image(image_path):
    """Convert image file to a Base64 string."""
    if not os.path.exists(image_path):  # Handle missing files
        return None
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")
    
def replace_emotes(text):
    """Finds (:emote:) patterns and replaces them with actual emojis."""
    def emote_replacer(match):
        emote_name = match.group(1)  # Extract emote name inside (:...:)
        return emoji.emojize(f":{emote_name}:", language="alias")  # Convert to emoji
    
    # Replace all matches
    return re.sub(r":([a-zA-Z0-9_]+):", emote_replacer, text)

def query_neo4j_graph(query, params=None):
    # Load LangChain Neo4jGraph instance 
    graph = Neo4jGraph(url=os.getenv("NEO4J_URI"), username=os.getenv("NEO4J_USERNAME"), password=os.getenv("NEO4J_PASSWORD"))
    return graph.query(query, params)

@tool
def load_image(image_path: str) -> Image.Image:
    """Process an image from a given path and return a Pillow Image object. Use it when ask about information on an image and you already have access to its path."""
    image_path = image_path.strip()
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"No such file: '{image_path}'")
    return Image.open(image_path)

@tool
def update_neo4j_graph(knowledge: str) -> str:
    "Takes a string of knowledge of correct format and updates the Neo4j graph with the entities and relationships."
    knowledge = knowledge.split("\n")
    for element in knowledge:
        if "entity" in element:
            element = {
                "action_type": element.split("|")[1],
                "name": element.split("|")[2],
                "type": element.split("|")[3],
                "description": element.split("|")[4][:-1] # [:-1] to remove the closing parenthesis of the entity/relationship
            }
            if element["action_type"] == "Deleted":
                query_neo4j_graph(f"MATCH (n:{':'.join(['__Entity__',element['type']])}) where n.name=$name DETACH DELETE n", params=element)
            elif element["action_type"] == "Updated":
                query_neo4j_graph(f"MATCH (n:{':'.join(['__Entity__',element['type']])}) where n.name=$name SET n.description=$description", params=element)
            elif (result := query_neo4j_graph(f"MATCH (n:{':'.join(['__Entity__',element['type']])}) where n.name=$name RETURN n.description as description", params=element)) != []:
                # Additional check because LLM not perfect and might create multiple times same element
                element["description"] = result[0]["description"] + " " + element["description"]
                query_neo4j_graph(f"MATCH (n:{':'.join(['__Entity__',element['type']])}) where n.name=$name SET n.description=$description", params=element)
            elif element["action_type"] == "Created":
                query_neo4j_graph(f"CREATE (n:{':'.join(['__Entity__',element['type']])} {{name: $name, description: $description}})", params=element)
            else:
                return "Invalid action type: either Created, Updated or Deleted needs to be put in second position entity|<action_type>|..."
        elif "relationship" in element:
            element = {
                "action_type": element.split("|")[1],
                "from": element.split("|")[2],
                "to": element.split("|")[3],
                "description": element.split("|")[4],
                "strength": element.split("|")[5][:-1] # [:-1] to remove the closing parenthesis of the entity/relationship
            }
            if element["action_type"] == "Deleted":
                query_neo4j_graph(f"MATCH (m:__Entity__)-[r]->(n) where m.name=$from and n.name=$to DELETE r", params=element)
            elif element["action_type"] == "Updated":
                query_neo4j_graph(f"MATCH (m:__Entity__)-[r]->(n) where m.name=$from and n.name=$to SET r.description=$description, r.strength=$strength", params=element)
            elif (result := query_neo4j_graph(f"MATCH (m:__Entity__)-[r]->(n) where m.name=$from and n.name=$to RETURN r.description as description", params=element)) != []:
                # Additional check because LLM not perfect and might create multiple times same element
                element["description"] = result[0]["description"] + " " + element["description"]
                query_neo4j_graph(f"MATCH (m:__Entity__)-[r]->(n) where m.name=$from and n.name=$to SET r.description=$description, r.strength=$strength", params=element)
            elif element["action_type"] == "Created":
                query_neo4j_graph(f"MATCH (m:__Entity__), (n) where m.name=$from and n.name=$to CREATE (m)-[:RELATED_TO {{description: $description, strength: $strength}}]->(n)", params=element)
            else:
                return "Invalid action type: either Created, Updated or Deleted needs to be put in second position relationship|<action_type>|..."
        elif "image" in element:
            element = {
                "action_type": element.split("|")[1],
                "image_title": element.split("|")[2],
                "image_path": element.split("|")[3],
                "location": element.split("|")[4],
                "date": element.split("|")[5],
                "description": element.split("|")[6][:-1] # [:-1] to remove the closing parenthesis of the entity/relationship
            }
            if element["action_type"] == "Deleted":
                query_neo4j_graph(f"MATCH (m:Image) where m.name=$image_title and m.image_path=$image_path DETACH DELETE m", params=element)
            elif element["action_type"] == "Updated":
                query_neo4j_graph(f"MATCH (m:Image) where m.name=$image_title SET m.image_path=$image_path, m.location=$location, m.date=$date, m.description=$description", params=element)
            elif (result := query_neo4j_graph(f"MATCH (m:Image) where m.image_path=$image_path RETURN m", params=element)) != []:
                # Additional check because LLM not perfect and might create multiple times same element
                query_neo4j_graph(f"MATCH (m:Image) where m.image_path=$image_path SET m.name=$image_title, m.image_path=$image_path, m.location=$location, m.date=$date, m.description=$description", params=element)
            elif element["action_type"] == "Created":
                query_neo4j_graph(f"CREATE (n:__Entity__:Image {{name: $image_title, image_path: $image_path, location: $location, date: $date, description: $description}})", params=element)
            else:
                return "Invalid action type: either Created, Updated or Deleted needs to be put in second position image|<action_type>|..."
        elif not element.strip():
            continue
        else:
            return "Invalid knowledge element: either entity, relationship or image."
    
    # Update the embeddings of the entities
    Neo4jVector.from_existing_graph(
        embedding=OpenAIEmbeddings(),
        node_label='__Entity__',
        text_node_properties=['name', 'description'],
        embedding_node_property='embedding'
    )   
    
    return "Successfully updated the Neo4j graph."

@tool
def search_neo4j_graph(question: str, filter = "") -> str:
    """
    Returns the 3 nearest neighbours of a query embedding as well as their relations in the Neo4j graph.
    Args:
        question (str): The query string to search for in the Neo4j graph.
        filter (str): The filter string to search for in the Neo4j graph, can be __Chunk__ or __Entity__. Default is "".
    Returns:
        str: A formatted string containing the top 5 nearest neighbours' names, descriptions, and similarity scores.
    Example:
        >>> search_neo4j_graph Who is John?
        'Entity Name: John Doe\nEntity Description: A person named John Doe\nSimilarity: 0.95\n\n...'
        >>> search_neo4j_graph Why did the family go to Brussels?
        'Entity Name: Family trip to Brussels\nEntity Description: Uncle invited all the family for Christmas \nSimilarity: 0.80\n\n...'
        >>> search_neo4j_graph What happened in 1945?
        'Entity Name: May 1945\nEntity Description: The end of World War II in Europe \nSimilarity: 0.60\n\n...'
    """
    openai_embedding = OpenAIEmbeddings()
    gds = GraphDataScience(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
    )
    
    query_embedded = openai_embedding.embed_query(question)
    query_neo4j_graph("""CREATE (:Query {name: $name, embedding: $query_embedded})""", params={"name":question, "query_embedded": query_embedded})
    
    if gds.graph.exists("entities&query").exists:
        gds.graph.drop("entities&query")
        
    gds.graph.project(
        "entities&query",
        ["__Entity__", 'Query'],
        "*",
        nodeProperties=["embedding"]
    )

    top_3 = gds.run_cypher(
        """
            CALL gds.knn.stream("entities&query", {nodeProperties:"embedding", topk:3})
            YIELD node1, node2, similarity
            WITH gds.util.asNode(node1) AS s, 
            gds.util.asNode(node2) AS t,
            similarity
            WHERE s:Query and t:__Entity__
            RETURN t.name AS entityName,
            labels(t) AS entityType,
            t.description AS entityDescription,
            t.location AS imageLocation,
            t.date AS imageDate,
            t.image_path AS imagePath
            LIMIT 3
        """
    )
    top_3["entityType"] = top_3["entityType"].apply(lambda x: next((s for s in x if s != "__Entity__"), None))
    
    query_neo4j_graph("MATCH (q:Query) DELETE q")
    result = "\n"
    for _, row in top_3.iterrows():
        if row["entityType"] == 'Image':
            result += f'("image"|{row["entityName"]}|{row["imagePath"]}|{row["imageLocation"]}|{row["imageDate"]}|{row["entityDescription"]})\n'
        else:
            result += f'("entity"|{row["entityName"]}|{row["entityType"]}|{row["entityDescription"]})\n'
        
    result += "\n"
    for idx, row in top_3.iterrows():
        relations = query_neo4j_graph(f"MATCH (m)-[r]->(n) WHERE m.name=$entityName RETURN m.name as from, n.name as to, r.description as description, r.strength as strength", params=row.to_dict())
        for relation in relations:
            result += f'("relationship"|{relation["from"]}|{relation["to"]}|{relation["description"]}|{relation["strength"]})\n'
            
    return result if result.strip() else "No results found."