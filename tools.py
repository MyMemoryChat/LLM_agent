from langchain_neo4j import Neo4jGraph
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Neo4jVector
from graphdatascience import GraphDataScience
from langchain.agents import tool
from agent import OptimizerAgent
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
    element["type_element"] = type_element.lower()
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
        os.getenv("NEO4J_URI"),
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
    if type_element == "livingbeing":
        type_element = "LivingBeing"
    else:
        type_element = type_element.capitalize()
    synonyms = embedding_search(element, type_element=type_element, limit=1, similarity_rate=0.96, delete_query=False)
    if type(synonyms) == str:
        return ("", "", "")
    
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
    for entity in [entities for entities in knowledge if "entity" in entities]:
        if "livingbeing" in entity:
            entity = format_extraction(entity, type_element='LivingBeing')
        elif "object" in entity or "location" in entity or "event" in entity:
            entity = format_extraction(entity, type_element=[type_element.capitalize() for type_element in ["event", "object", "location"] if type_element in entity][0])
        elif "image" in entity:
            # In case it is an image, we don't do any similarity search and just create it with its relationships.
            entity = format_extraction(entity, type_element='Image')
            element.pop("operation_type", None)
            element.pop("type_element", None)
            query_neo4j_graph("MERGE (n:__Entity__:Image {{image_path=$image_path}}) SET n = $entity", {"image_path":entity["image_path"], "entity":entity})
            for relationship in [relationships for relationships in knowledge if "relationship" in relationships and entity["name"] in relationships]:
                relationship = format_extraction(relationship, type_element='relationship')
                element.pop("operation_type", None)
                element.pop("type_element", None)
                query_neo4j_graph("MATCH (m:__Entity__), (n:__Entity__) where m.name=$from and n.name=$to CREATE (m)-[:"+element['relation_type']+" {description: $description}]->(n)", params=element)
            continue
        else:
            return f"Entity type not recognized {entity}: Only [livingbeing, object, location, event, image] are accepted."
        
        if entity["operation_type"] == "Updated":
            entity.pop("operation_type", None)
            if entity["type_element"] == "livingbeing":
                element_type = "LivingBeing"
            else:
                element_type = entity["type_element"].capitalize()
            entity.pop("type_element", None)
            query_neo4j_graph(f"MERGE (n:`__Entity__`:{element_type} {{name=$name}}) SET n = $entity", {"name":entity["name"], "entity":entity})
            
            for relationship in [relationships for relationships in knowledge if "relationship" in relationships and entity["name"] in relationships]:
                element = format_extraction(relationship, type_element='relationship')
                element.pop("operation_type", None)
                element.pop("type_element", None)
                query_neo4j_graph("MATCH (m:__Entity__), (n:__Entity__) where m.name=$from and n.name=$to CREATE (m)-[:"+element['relation_type']+" {description: $description}]->(n)", params=element)
            
        elif entity["operation_type"] == "Deleted":
            query_neo4j_graph("MATCH (n) where n.name=$name DETACH DELETE n", {"name":entity["name"]})
        elif entity["operation_type"] == "Created":
            # Check if similar entities already exists.
            entity_relationships = "\n"
            for relationship in [relationships for relationships in knowledge if "relationship" in relationships and entity["name"] in relationships]:
                entity_relationships+=relationship+"\n"
            
            print("Entity to update: "+entity)
            print("Relations to update: "+entity_relationships)
            
            # Do a embedding similarity search to find similar entities
            synonyms, n1Name, n2Name = similar_entities(entity, entity["type_element"], "\n".join(entity_relationships))
            print("Synonyms: ",synonyms)
            if synonyms != "":
                # If there exists synonyms, pass it to an agent to check if the entities are the same or not, eg. two livingbeing with same description but different names.
                optimizer = OptimizerAgent()
                modelAnswer = optimizer(synonyms)
                print(modelAnswer)
            
            if synonyms == "" or modelAnswer.strip() == "Nothing to merge.":
                # Simply add the new relationships to the new entity
                if entity_relationships != "":
                    for relation in entity_relationships.strip().split("\n"):
                        element = format_extraction(relation, type_element='relationship')
                        print(element)
                        element.pop("operation_type", None)
                        element.pop("type_element", None)
                        query_neo4j_graph("MATCH (m:__Entity__), (n:__Entity__) where m.name=$from and n.name=$to CREATE (m)-[:"+element['relation_type']+" {description: $description}]->(n)", params=element)
            else:
                # Delete the old and new entity and create a new "merged" one
                query_neo4j_graph("MATCH (n) where n.name=$n1Name or n.name=$n2Name DETACH DELETE n", {"n1Name":n1Name, "n2Name":n2Name})
                for answer in [line for line in modelAnswer.strip().split("\n") if "entity" in line]:
                    print(answer)
                    if "livingbeing" in answer:
                        element = format_extraction(answer, type_element='LivingBeing')
                        element.pop("operation_type", None)
                        element_type = "LivingBeing"
                        element.pop("type_element", None)
                        query_neo4j_graph(f"CREATE (n:__Entity__:{element_type}) SET n = $element", {"element":element})
                    else:
                        element = format_extraction(answer, type_element=[type_element.capitalize() for type_element in ["event", "object", "location"] if type_element in answer][0])
                        element.pop("operation_type", None)
                        element_type = element["type_element"].capitalize()
                        element.pop("type_element", None)
                        query_neo4j_graph(f"CREATE (n:__Entity__:{element_type}) SET n = $element", {"element":element})
                    
                    for relationship in [line for line in modelAnswer.strip().split("\n") if "relationship" in line and element["name"] in line]:
                        element = format_extraction(answer, type_element='relationship')
                        element.pop("operation_type", None)
                        query_neo4j_graph("MATCH (m:__Entity__), (n:__Entity__) where m.name=$from and n.name=$to CREATE (m)-[:"+element['relation_type']+" {description: $description}]->(n)", params=element)

            Neo4jVector.from_existing_graph(
                    embedding=OpenAIEmbeddings(),
                    node_label='__Entity__',
                    text_node_properties=['name', 'additional_infos', 'date','species','city','country','continent','type', 'date_of_birth'],
                    embedding_node_property='embedding'
                )
        else:
            return f"Operation type not recognized {entity['operation_type']}: Only [Updated, Deleted, Created] are accepted."
            
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