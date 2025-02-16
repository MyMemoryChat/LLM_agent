from agent import OptimizerAgent
from tools import similar_entities, query_neo4j_graph, format_extraction
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Neo4jVector

"""entity = {'name': 'Rookie', 'species': 'Dog', 'date_of_birth':'20-10-2022', 'additional_infos': 'Medium Shiba Inu; Can be cute, selfish, and dominant'}"""
entity = {'name': 'Newton', 'species': 'Cat', 'date_of_birth':'20-10-2014', 'additional_infos': 'An orange cat with a white belly and paws'}
entity_type = "LivingBeing"
relations = """"""
try:
    synonyms, n1Name, n2Name = similar_entities(entity, entity_type, relations)
except Exception as e:
    synonyms = ""
    
print("Synonyms: ",synonyms)

if synonyms != "":
    optimizer = OptimizerAgent()
    modelAnswer = optimizer(synonyms)
    print(modelAnswer)
    
if synonyms == "" or modelAnswer.strip() == "Nothing to merge.":
    if relations != "":
        for relation in relations.strip().split("\n"):
            element = format_extraction(relation, type_element='relationship')
            del element["operation_type"]
            query_neo4j_graph("MATCH (m:__Entity__), (n:__Entity__) where m.name=$from and n.name=$to CREATE (m)-[:"+element['relation_type']+" {description: $description}]->(n)", params=element)
else:
    query_neo4j_graph("MATCH (n) where n.name=$n1Name or n.name=$n2Name DETACH DELETE n", {"n1Name":n1Name, "n2Name":n2Name})
    for answer in [line for line in modelAnswer.strip().split("\n") if line]:
        print(answer)
        if "livingbeing" in answer:
            element = format_extraction(answer, type_element='LivingBeing')
            del element["operation_type"]
            element_type = "LivingBeing"
            del element["type"]
            query_neo4j_graph(f"CREATE (n:__Entity__:{element_type}) SET n = $element", {"element":element})
        elif "relationship" in answer:
            element = format_extraction(answer, type_element='relationship')
            del element["operation_type"]
            query_neo4j_graph("MATCH (m:__Entity__), (n:__Entity__) where m.name=$from and n.name=$to CREATE (m)-[:"+element['relation_type']+" {description: $description}]->(n)", params=element)
        else:
            element = format_extraction(answer, type_element=[type_element.capitalize() for type_element in ["event", "object", "location"] if type_element in answer][0])
            del element["operation_type"]
            element_type = element["type"].capitalize()
            del element["type"]
            query_neo4j_graph(f"CREATE (n:__Entity__:{element_type}) SET n = $element", {"element":element})

Neo4jVector.from_existing_graph(
        embedding=OpenAIEmbeddings(),
        node_label='__Entity__',
        text_node_properties=['name', 'additional_infos', 'date','species','city','country','continent','type', 'date_of_birth'],
        embedding_node_property='embedding'
    )

"""query_neo4j_graph("CREATE (n)")

print(query_neo4j_graph("Match (n) where n.name=$n1Name or n.name=$n2Name return n", {"n1Name":n1Name, "n2Name":n2Name}))"""
# Medium Shiba Inu; Can be cute, selfish, and dominant 20-10-2022