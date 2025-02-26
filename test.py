from backup import restore, backup, stop_neo4j, start_neo4j
from tools import search_neo4j_graph, update_neo4j_graph, similar_entities
from agent import AnswerAgent

# backup()
# start_neo4j(r"C:\Users\jager\.Neo4jDesktop\relate-data\dbmss\dbms-6feab08e-8790-4ddd-9be3-b9d01fe197ae", "neo4j")
restore(r"C:\Users\jager\Desktop\github\my_memory\LLM_agent\backups\20250226-160855")
# stop_neo4j(r"C:\Users\jager\.Neo4jDesktop\relate-data\dbmss\dbms-6feab08e-8790-4ddd-9be3-b9d01fe197ae")

# print(search_neo4j_graph.invoke("Sophie's dog"))
# update_neo4j_graph.invoke("(entity|livingbeing|Updated|3bcf5a68-026e-463a-86b6-47cb83ab3b1f|Noé|Human|26-11-2001|Also known as Noé Jager. Sophie's boyfriend, met in December 2023.  He accompanied her on a trip to Europe.)")

# print(similar_entities({'name': 'Sophie Zhang', 'species': 'Human', 'uuid': 'e06216de-7e89-4872-87de-672e8e3c24d1', 'embedding': None, 'date_of_birth': '16-10-2001', 'additional_infos': '', 'type_element': 'livingbeing', 'operation_type': 'Created'}))

# answer = AnswerAgent()
# answer("Who is Sophie's dog?", verbose=True)