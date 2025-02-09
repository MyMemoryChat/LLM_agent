from tools import update_neo4j_graph

update_neo4j_graph.invoke("""
("image"|Created|Montreal Kitchen|./images/image0.jpg|Montreal, Canada|2024|This image depicts the modern kitchen shared by Noé and Sophie in their Montreal apartment.  The kitchen features stainless steel appliances, dark gray cabinets, and a black countertop.  The image was likely taken recently, given the context of their recent trip to Paris.  Sophie's Shiba Inu, Rookie, is partially visible in the bottom right corner, suggesting he was at home while they were away.|100)
("relationship"|Created|Noé|Montreal Kitchen|Noé shares this kitchen with Sophie in Montreal.|95)
("relationship"|Created|Sophie|Montreal Kitchen|Sophie shares this kitchen with Noé in Montreal.|95)
("relationship"|Created|Rookie|Montreal Kitchen|Rookie, Sophie's Shiba Inu, is present in the kitchen.|80)
("relationship"|Created|Montreal|Montreal Kitchen|The kitchen is located in Montreal, Canada.|100)
""")