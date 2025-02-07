from tools import search_neo4j_graph, update_neo4j_graph

search_neo4j_graph.invoke("Who is Sophie?")

quit()
update_neo4j_graph.invoke("""
("entity"|Created|Sophie|Person|Sophie is the narrator of the text. She comes from Wuhan, went to Paris in the winter, has a boyfriend named Noé, and a dog named Rookie.)
("entity"|Created|Wuhan|Location|A city where Sophie comes from.)
("entity"|Created|Paris|Location|A city Sophie visited this winter.)
("entity"|Created|Winter|Date|The season when Sophie visited Paris.)
("entity"|Created|Noé|Person|Sophie\'s boyfriend who designed an app.)
("entity"|Created|Rookie|Person|Sophie\'s Shiba Inu dog.)
                   
("relationship"|Created|Sophie|Wuhan|Sophie comes from Wuhan.|100)
("relationship"|Created|Sophie|Paris|Sophie visited Paris this winter.|95)
("relationship"|Created|Sophie|Winter|Sophie\'s trip to Paris happened in the winter.|90)
("relationship"|Created|Sophie|Noé|Noé is Sophie\'s boyfriend.|98)
("relationship"|Created|Noé|App|Noé designed an app.|100)
("relationship"|Created|Sophie|Rookie|Rookie is Sophie\'s dog.|98)
""")
