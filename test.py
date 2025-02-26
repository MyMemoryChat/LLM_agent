from backup import restore, backup, stop_neo4j, start_neo4j
from tools import search_neo4j_graph, update_neo4j_graph
from agent import AnswerAgent

# backup()
# start_neo4j(r"C:\Users\jager\.Neo4jDesktop\relate-data\dbmss\dbms-6feab08e-8790-4ddd-9be3-b9d01fe197ae", "neo4j")
restore(r"C:\Users\jager\Desktop\github\my_memory\LLM_agent\backups\20250224-141636")
# stop_neo4j(r"C:\Users\jager\.Neo4jDesktop\relate-data\dbmss\dbms-6feab08e-8790-4ddd-9be3-b9d01fe197ae")

# search_neo4j_graph.invoke("Sophie's dog")
# update_neo4j_graph.invoke("(entity|livingbeing|Updated|Noé|Human|26-11-2001|Sophie's boyfriend, met in December 2023.  He accompanied her on a trip to Europe.)")

# answer = AnswerAgent()
# answer("Who is Sophie's dog?", verbose=True)