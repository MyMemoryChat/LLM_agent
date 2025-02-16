from langchain_neo4j import Neo4jGraph
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Neo4jVector
from graphdatascience import GraphDataScience
from langchain.agents import tool
import pandas as pd

import base64
import re
import emoji

import os
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
global format_mapping
format_mapping = {
        "LivingBeing": "(entity|livingbeing||{name}|{species}|{date_of_birth}|{additional_infos})",
        "Location": "(entity|location||{name}|{city}|{country}|{continent}|{additional_infos})",
        "Event": "(entity|event||{name}|{date}|{additional_infos})",
        "Object": "(entity|object||{name}|{type}|{additional_infos})",
        "Image": "(entity|image||{name}|{date}|{image_path}|{additional_infos})",
        "relationship": "(relationship||{relation_type}|{from}|{to}|{description})"
}

def format_conversion(element: dict[str], type_element: str) -> str:
    return format_mapping[type_element].format(**element)

def format_extraction(element: str, type_element: str) -> dict[str]:
    pattern = re.compile(r"[(){}\[\]]")
    if type_element != "relationship":
        keys = ['operation_type']+[pattern.sub("", key) for key in format_mapping[type_element].split("|")[3:]]
        values = [pattern.sub("", value) for value in element.split("|")[2:]]
    else:
        keys = ['operation_type']+[pattern.sub("", key) for key in format_mapping[type_element].split("|")[2:]]
        values = [pattern.sub("", value) for value in element.split("|")[1:]]
    element = {key: value for key, value in zip(keys, values)}
    element["type"] = type_element.lower()
    return element

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

def embedding_search(element: dict[str], type_element: str = "", limit: int=5, similarity_rate:float = 0.94, synonym_type_filter: str = "", delete_query: bool = True) -> pd.DataFrame:
    query_neo4j_graph("MATCH (q:Query) DELETE q")
    query_neo4j_graph("""
        MATCH (n:__Entity__) 
        WHERE n.embedding is null
        detach delete n""")

    if type_element != "":
        query_neo4j_graph(f"""
            CREATE (n:Query:__Entity__:{type_element} $element)
        """, params={"element": element})
    else:
        query_neo4j_graph(f"""
            CREATE (n:Query:__Entity__ $element)
        """, params={"element": element})
    
    Neo4jVector.from_existing_graph(
        embedding=OpenAIEmbeddings(),
        node_label='Query',
        text_node_properties=['name', 'additional_infos', 'date','species','city','country','continent','type', 'date_of_birth'],
        embedding_node_property='embedding'
    )
    
    gds = GraphDataScience(
        "bolt://localhost:7687",
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
    )
    
    if gds.graph.exists("synonyms").exists:
        gds.graph.drop("synonyms")
    
    gds.graph.project(
        "synonyms",
        ["LivingBeing", "Location", "Event", "Object"],
        "*",
        nodeProperties=["embedding"]
    )

    synonyms = gds.run_cypher(
        f"""
            CALL gds.knn.stream("synonyms", {{nodeProperties: "embedding", topk: 2}})
            YIELD node1, node2, similarity
            WHERE similarity > {similarity_rate}
            WITH gds.util.asNode(node1) AS n1, 
                gds.util.asNode(node2) AS n2,
                similarity
            WHERE n1:Query {"and n2:"+synonym_type_filter if synonym_type_filter!= "" else ""}
            RETURN labels(n1) AS n1Label,
                labels(n2) AS n2Label,
                n1 {{ .*, embedding: NULL }} AS entity1, 
                n2 {{ .*, embedding: NULL }} AS entity2,
                similarity
            ORDER BY similarity DESC
            LIMIT {limit}
        """
    )
    if delete_query:
        query_neo4j_graph("MATCH (n:Query) DELETE n")
    else:
        query_neo4j_graph("MATCH (n:Query) REMOVE n:Query RETURN n")
    
    synonyms["n1Label"] = synonyms["n1Label"].map(lambda labels: next((s for s in labels if s not in {"__Entity__", "Query"}), None))
    synonyms["n2Label"] = synonyms["n2Label"].map(lambda labels: next((s for s in labels if s != "__Entity__"), None))

    synonyms.drop(columns=["similarity"], inplace=True)
    
    if synonyms.empty:
        return f"No similar {synonym_type_filter if synonym_type_filter!='' else 'entities'} found."
    return synonyms

def similar_entities(element: dict[str], type_element: str, n1Relations: str) -> tuple[str, str, str]:
    # Delete nodes without embeddings for potential errors
    synonyms = embedding_search(element, type_element=type_element, limit=1, similarity_rate=0.96, delete_query=False)
    if type(synonyms) == str:
        raise FileNotFoundError(synonyms)
    
    synonyms = synonyms.iloc[0]
    
    result ="\n"
    n1Label = synonyms["n1Label"]
    result+=format_conversion(synonyms["entity1"], n1Label)+"\n\n"
    
    result+=n1Relations + "\n"
        
    result+="-"*50+"\n"
    
    n2Label = synonyms["n2Label"]
    result+=format_conversion(synonyms["entity2"], n2Label)+"\n\n"
        
    n2Relations = query_neo4j_graph(f"Match (n:{synonyms['n2Label']})-[r]-(m) where m.name=$name return type(r) as relation_type, m.name as from, n.name as to, r.description as description", params=synonyms['entity2'])
    for n2Relation in n2Relations:
        result+=format_conversion(n2Relation, "relationship")+"\n"
    
    return (result, synonyms["entity1"]["name"], synonyms["entity2"]["name"])
    
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
                    query_neo4j_graph("MATCH (n:`__Entity__`:`Image`) where n.name=$name SET n.date=$date, n.image_path=$path, n.additional_infos=$additional_infos", params=element)
                
                elif (result := query_neo4j_graph("MATCH (n:`__Entity__`:`Image`) where n.name=$name RETURN n.date as date,  n.additional_infos as additional_infos", params=element)) != []:
                    # Additional check because LLM not perfect and might create multiple times same element
                    for key in ["date", "additional_infos"]:
                        if key in result[0] and result[0][key] is not None:
                            element[key] = result[0][key]
                    
                    query_neo4j_graph("MATCH (n:`__Entity__`:`Image`) where n.name=$name SET n.date=$date, n.image_path=$path, n.additional_infos=$additional_infos", params=element)
                
                elif element["operation_type"] == "Created":
                    query_neo4j_graph("CREATE (n:`__Entity__`:`Image` {name: $name, date:$date, image_path:$path, additional_infos: $additional_infos})", params=element)
                
                else:
                    return f"Invalid operation type for image '{element['name']}': either Created, Updated or Deleted needs to be put in second position <entity_type>|<operation_type>|..."
            
            else:
                return f"Invalid entity type: either livingbeing, location, event, object or image needs to be put in second position entity|<entity_type>|<operation_type>|..."
        elif "relationship" in element:
            if len(element.split("|"))!=6:
                return f"Invalid format {element}: relationships should follow the following format: (relationship|<relation_type>|<operation_type>|<from>|<to>|<description>)"
            element = {
                "relation_type": element.split("|")[1],
                "operation_type": element.split("|")[2],
                "from": element.split("|")[3],
                "to": element.split("|")[4],
                "description": element.split("|")[5][:-1] # [:-1] to remove the closing parenthesis of the entity/relationship
            }
            if element["relation_type"] not in ['CUSTOM','SEEN_IN','WENT_TO','LIVE_IN','BORN_IN','LIKE','DISLIKE','BELONG_TO','TOOK_PLACE_IN','REPRESENT','PARTICIPATED_IN','FAMILY','COUPLE','FRIEND','ACQUAINTANCE']:
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
        text_node_properties=['name', 'additional_infos', 'date','species','city','country','continent','type', 'date_of_birth'],
        embedding_node_property='embedding'
    )
    
    return "Successfully updated the Neo4j graph."

@tool
def search_neo4j_graph(question: str) -> str:
    """
    Returns the 5 nearest neighbours of a query embedding as well as their relations in the Neo4j graph.
    Args:
        question (str): The query string to search for in the Neo4j graph.
    Returns:
        str: A formatted string containing the top 5 nearest neighbours' names, descriptions, and similarity scores.
    Example:
        >>> search_neo4j_graph Who is John?
        '(entity|livingbeing||John|Human||)'
        >>> search_neo4j_graph Why did the family go to Brussels?
        '(entity|event||Family trip to Brussels|2022-07-15|)'
        >>> search_neo4j_graph What happened in 1945?
        '(entity|event||End of World War II|1945-05-08|)'
    """
    # Delete nodes without embeddings for potential errors
    top_5 = embedding_search({"name": question}, similarity_rate=0.92, delete_query=True)    
    result = "\n"
    for _, row in top_5.iterrows():
        entity_label = row["n2Label"]
        result += format_mapping[entity_label].format(**row["entity2"]) + "\n"
    
    result += "\n"
    for _, row in top_5.iterrows():
        relations = query_neo4j_graph(
            "MATCH (m)-[r]-(n) WHERE m.name=$name RETURN type(r) as type, m.name as from, n.name as to, r.description as description",
            params=row["entity2"]
        )
        for relation in relations:
            result += f"(relationship|{relation['type']}||{relation['from']}|{relation['to']}|{relation['description']})\n"
            
    return result if result.strip() else "No results found."

@tool
def find_image(name: str) -> str:
    """Searches for an image name in the Neo4j graph and returns the image name, date, image_path and additional informations in the right format."""
    # Delete nodes without embeddings for potential errors
    image_search = embedding_search({"name": name}, type_element="Image", limit=1, similarity_rate=0.94, delete_query=True)
    
    image_infos = image_search.iloc[0].to_dict()

    return f"(entity|image|None|{image_infos['name']}|{image_infos['date']}|{image_infos['image_path']}|{image_infos['additional_infos']})\n"