from tools import update_neo4j_graph

update_neo4j_graph.invoke("(entity|livingbeing||Rookie|Dog||)\n(relationship||BELONG_TO|Rookie|Sophie|Rookie belongs to Sophie)")