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
    knowledge = [k for k in knowledge.split("\n") if k]
    for element in knowledge:
        if "entity" in element:
            if "livingbeing" in element:
                element = {
                    "operation_type": element.split("|")[2],
                    "name": element.split("|")[3],
                    "species": element.split("|")[4],
                    "date_of_birth": element.split("|")[5],
                    "additional_infos": element.split("|")[6][:-1] # [:-1] to remove the closing parenthesis of the entity/relationship
                }
                if element["operation_type"] == "Deleted":
                    query_neo4j_graph("MATCH (n:`__Entity__`:`LivingBeing`) where n.name=$name and n.species=$species DETACH DELETE n", params=element)
                
                elif element["operation_type"] == "Updated":
                    query_neo4j_graph("MATCH (n:`__Entity__`:`LivingBeing`) where n.name=$name and n.species=$species SET n.date_of_birth=$date_of_birth, n.additional_infos=$additional_infos", params=element)
                
                elif (result := query_neo4j_graph("MATCH (n:`__Entity__`:`LivingBeing`) where n.name=$name and n.species=$species RETURN n.date_of_birth as date_of_birth, n.additional_infos as additional_infos", params=element)) != []:
                    # Additional check because LLM not perfect and might create multiple times same element
                    for key in ["date_of_birth", "additional_infos"]:
                        if key in result[0] and result[0][key] is not None:
                            element[key] = result[0][key]
                    
                    query_neo4j_graph("MATCH (n:`__Entity__`:`LivingBeing`) where n.name=$name and n.species=$species SET n.date_of_birth=$date_of_birth, n.additional_infos=$additional_infos", params=element)
                
                elif element["operation_type"] == "Created":
                    query_neo4j_graph("CREATE (n:`__Entity__`:`LivingBeing` {name: $name, species:$species, date_of_birth:$date_of_birth, additional_infos: $additional_infos})", params=element)
                
                else:
                    return f"Invalid operation type for livingbeing '{element['name']}': either Created, Updated or Deleted needs to be put in second position <entity_type>|<operation_type>|..."
            
            elif "location" in element:
                element = {
                    "operation_type": element.split("|")[2],
                    "name": element.split("|")[3],
                    "city": element.split("|")[4],
                    "country": element.split("|")[5],
                    "continent": element.split("|")[6],
                    "additional_infos": element.split("|")[7][:-1] # [:-1] to remove the closing parenthesis of the entity/relationship
                }
                if element["operation_type"] == "Deleted":
                    query_neo4j_graph("MATCH (n:`__Entity__`:`Location`) where n.name=$name DETACH DELETE n", params=element)
                
                elif element["operation_type"] == "Updated":
                    query_neo4j_graph("MATCH (n:`__Entity__`:`Location`) where n.name=$name SET n.city=$city, n.country=$country, n.continent=$continent, n.additional_infos=$additional_infos", params=element)
                
                elif (result := query_neo4j_graph("MATCH (n:`__Entity__`:`Location`) where n.name=$name RETURN n.city as city, n.country as country, n.continent as continent,  n.additional_infos as additional_infos", params=element)) != []:
                    # Additional check because LLM not perfect and might create multiple times same element
                    for key in ["city", "country", "continent", "additional_infos"]:
                        if key in result[0] and result[0][key] is not None:
                            element[key] = result[0][key]
                    
                    query_neo4j_graph("MATCH (n:`__Entity__`:`Location`) where n.name=$name SET n.city=$city, n.country=$country, n.continent=$continent, n.additional_infos=$additional_infos", params=element)
                
                elif element["operation_type"] == "Created":
                    query_neo4j_graph("CREATE (n:`__Entity__`:`Location` {name: $name, city:$city, country:$country, continent:$continent, additional_infos: $additional_infos})", params=element)
                
                else:
                    return f"Invalid operation type for location '{element['name']}': either Created, Updated or Deleted needs to be put in second position <entity_type>|<operation_type>|..."
            
            elif "event" in element:
                element = {
                    "operation_type": element.split("|")[2],
                    "name": element.split("|")[3],
                    "date": element.split("|")[4],
                    "additional_infos": element.split("|")[5][:-1] # [:-1] to remove the closing parenthesis of the entity/relationship
                }
                if element["operation_type"] == "Deleted":
                    query_neo4j_graph("MATCH (n:`__Entity__`:`Event`) where n.name=$name and n.date=$date DETACH DELETE n", params=element)
                
                elif element["operation_type"] == "Updated":
                    query_neo4j_graph("MATCH (n:`__Entity__`:`Event`) where n.name=$name and n.date=$date SET n.additional_infos=$additional_infos", params=element)
                
                elif (result := query_neo4j_graph("MATCH (n:`__Entity__`:`Event`) where n.name=$name and n.date=$date RETURN n.additional_infos as additional_infos", params=element)) != []:
                    # Additional check because LLM not perfect and might create multiple times same element
                    for key in ["additional_infos"]:
                        if key in result[0] and result[0][key] is not None:
                            element[key] = result[0][key]
                    
                    query_neo4j_graph("MATCH (n:`__Entity__`:`Event`) where n.name=$name and n.date=$date SET n.additional_infos=$additional_infos", params=element)
                
                elif element["operation_type"] == "Created":
                    query_neo4j_graph("CREATE (n:`__Entity__`:`Event` {name: $name, date:$date, additional_infos: $additional_infos})", params=element)
                
                else:
                    return f"Invalid operation type for event '{element['name']}': either Created, Updated or Deleted needs to be put in second position <entity_type>|<operation_type>|..."
            
            elif "object" in element:
                element = {
                    "operation_type": element.split("|")[2],
                    "name": element.split("|")[3],
                    "type": element.split("|")[4],
                    "additional_infos": element.split("|")[5][:-1] # [:-1] to remove the closing parenthesis of the entity/relationship
                }
                if element["operation_type"] == "Deleted":
                    query_neo4j_graph("MATCH (n:`__Entity__`:`Object`) where n.name=$name DETACH DELETE n", params=element)
                
                elif element["operation_type"] == "Updated":
                    query_neo4j_graph("MATCH (n:`__Entity__`:`Object`) where n.name=$name SET n.type=$type, n.additional_infos=$additional_infos", params=element)
                
                elif (result := query_neo4j_graph("MATCH (n:`__Entity__`:`Object`) where n.name=$name RETURN n.type as type,  n.additional_infos as additional_infos", params=element)) != []:
                    # Additional check because LLM not perfect and might create multiple times same element
                    for key in ["type", "additional_infos"]:
                        if key in result[0] and result[0][key] is not None:
                            element[key] = result[0][key]
                    
                    query_neo4j_graph("MATCH (n:`__Entity__`:`Object`) where n.name=$name SET n.type=$type, n.additional_infos=$additional_infos", params=element)
                
                elif element["operation_type"] == "Created":
                    query_neo4j_graph("CREATE (n:`__Entity__`:`Object` {name: $name, type:$type, additional_infos: $additional_infos})", params=element)
                
                else:
                    return f"Invalid operation type for object '{element['name']}': either Created, Updated or Deleted needs to be put in second position <entity_type>|<operation_type>|..."
            
            elif "image" in element:
                element = {
                    "operation_type": element.split("|")[2],
                    "name": element.split("|")[3],
                    "date": element.split("|")[4],
                    "path": element.split("|")[5],
                    "additional_infos": element.split("|")[6][:-1] # [:-1] to remove the closing parenthesis of the entity/relationship
                }
                if element["operation_type"] == "Deleted":
                    query_neo4j_graph("MATCH (n:`__Entity__`:`Image`) where n.name=$name DETACH DELETE n", params=element)
                
                elif element["operation_type"] == "Updated":
                    query_neo4j_graph("MATCH (n:`__Entity__`:`Image`) where n.name=$name SET n.date=$date, n.additional_infos=$additional_infos", params=element)
                
                elif (result := query_neo4j_graph("MATCH (n:`__Entity__`:`Image`) where n.name=$name RETURN n.date as date,  n.additional_infos as additional_infos", params=element)) != []:
                    # Additional check because LLM not perfect and might create multiple times same element
                    for key in ["date", "additional_infos"]:
                        if key in result[0] and result[0][key] is not None:
                            element[key] = result[0][key]
                    
                    query_neo4j_graph("MATCH (n:`__Entity__`:`Image`) where n.name=$name SET n.date=$date, n.additional_infos=$additional_infos", params=element)
                
                elif element["operation_type"] == "Created":
                    query_neo4j_graph("CREATE (n:`__Entity__`:`Image` {name: $name, date:$date, additional_infos: $additional_infos})", params=element)
                
                else:
                    return f"Invalid operation type for image '{element['name']}': either Created, Updated or Deleted needs to be put in second position <entity_type>|<operation_type>|..."
            
            else:
                return f"Invalid entity type: either livingbeing, location, event, object or image needs to be put in second position entity|<entity_type>|<operation_type>|..."
        elif "relationship" in element:
            element = {
                "relation_type": element.split("|")[1],
                "operation_type": element.split("|")[2],
                "from": element.split("|")[3],
                "to": element.split("|")[4],
                "description": element.split("|")[5][:-1] # [:-1] to remove the closing parenthesis of the entity/relationship
            }
            if element["relation_type"] not in ['CUSTOM','WENT_TO','LIVE_IN','BORN_IN','LIKE','DISLIKE','BELONG_TO','TOOK_PLACE_IN','REPRESENT','PARTICIPATED_IN','FAMILY','COUPLE','FRIEND','ACQUAINTANCE']:
                return f"Invalid relation type {element['relation_type']}: either LIVE_IN, BORN_IN, LIKE, DISLIKE, BELONG_TO, TOOK_PLACE_IN, REPRESENT, PARTICIPATED_IN, FAMILY, COUPLE, FRIEND or ACQUAINTANCE needs to be put in second position relationship|<relation_type>|<operation_type>|..."
                            
            if element["operation_type"] == "Deleted":
                query_neo4j_graph(f"MATCH (m:__Entity__)-[r:"+element['relation_type']+"]->(n:__Entity__) where m.name=$from and n.name=$to DELETE r", params=element)
            elif element["operation_type"] == "Updated":
                query_neo4j_graph(f"MATCH (m:__Entity__)-[r:"+element['relation_type']+"]->(n:__Entity__) where m.name=$from and n.name=$to SET r.description=$description", params=element)
            elif (result := query_neo4j_graph("MATCH (m:__Entity__)-[r:"+element['relation_type']+"]->(n:__Entity__) where m.name=$from and n.name=$to RETURN r.description as description", params=element)) != []:
                # Additional check because LLM not perfect and might create multiple times same element
                for key in ["description"]:
                        if key in result[0] and result[0][key] is not None:
                            element[key] = result[0][key]
                query_neo4j_graph(f"MATCH (m:__Entity__)-[r:"+element['relation_type']+"]->(n:__Entity__) where m.name=$from and n.name=$to SET r.description=$description", params=element)
            elif element["operation_type"] == "Created":
                query_neo4j_graph("MATCH (m:__Entity__), (n:__Entity__) where m.name=$from and n.name=$to CREATE (m)-[:"+element['relation_type']+" {description: $description}]->(n)", params=element)
            else:
                return "Invalid operation type: either Created, Updated or Deleted needs to be put in second position relationship|<operation_type>|..."
        else:
            return f"Invalid format {element}: the first word of each line should be either entity or relationship entity|... or relationship|..."
    
    # Update the embeddings of the entities
    Neo4jVector.from_existing_graph(
        embedding=OpenAIEmbeddings(),
        node_label='__Entity__',
        text_node_properties=['name', 'additional_infos', 'date','species','city','country','continent','type'],
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
    # Delete nodes without embeddings for potential errors
    query_neo4j_graph("""
        MATCH (n:__Entity__) 
        WHERE n.embedding is null
        detach delete n""")
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
            labels(t) AS entityLabel,
            t.additional_infos AS entityAdditional_infos,
            t.location AS entityLocation,
            t.date AS entityDate,
            t.image_path AS imagePath,
            t.species as entitySpecies,
            t.date_of_birth AS entityBirthday,
            t.city as entityCity,
            t.country as entityCountry,
            t.continent as entityContinent,
            t.type as entityType
            LIMIT 3
        """
    )
    
    query_neo4j_graph("MATCH (q:Query) DELETE q")
        
    top_3["entityLabel"] = top_3["entityLabel"].apply(lambda x: next((s for s in x if s != "__Entity__"), None))
    
    format_mapping = {
        "LivingBeing": "(entity|livingbeing|None|{entityName}|{entitySpecies}|{entityBirthday}|{entityAdditional_infos})",
        "Location": "(entity|location|None|{entityName}|{entityCity}|{entityCountry}|{entityContinent}|{entityAdditional_infos})",
        "Event": "(entity|event|None|{entityName}|{entityDate}|{entityAdditional_infos})",
        "Object": "(entity|object|None|{entityName}|{entityType}|{entityAdditional_infos})",
        "Image": "(entity|image|None|{entityName}|{entityDate}|{imagePath}|{entityAdditional_infos})"
    }

    result = "\n"
    for _, row in top_3.iterrows():
        entity_label = row["entityLabel"]
        if entity_label in format_mapping:
            result += format_mapping[entity_label].format(**row) + "\n"
        else:
            print(entity_label)
            result += f"(entity|{entity_label}|None|{row['entityName']}|{row['entityAdditional_infos']})\n"
    
    result += "\n"
    for idx, row in top_3.iterrows():
        relations = query_neo4j_graph(
            "MATCH (m)-[r]-(n) WHERE m.name=$entityName RETURN type(r) as relationType, m.name as from, n.name as to, r.description as description",
            params=row.to_dict()
        )
        for relation in relations:
            result += f"(relationship|{relation['relationType']}|None|{relation['from']}|{relation['to']}|{relation['description']})\n"
            
    return result if result.strip() else "No results found."