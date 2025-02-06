-Goal- Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.

-Steps-

    1. Identify all entities. For each identified entity, extract the following information:

    entity_name: Name of the entity, capitalized
    entity_type: One of the following types: [Person, Location, Date, Event]
    entity_description: Comprehensive description of the entity's attributes and activities 
    Format each entity as ("entity"|<entity_name>|<entity_type>|<entity_description>)

    2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are clearly related to each other. For each pair of related entities, extract the following information:

    source_entity: name of the source entity, as identified in step 1
    target_entity: name of the target entity, as identified in step 1
    relationship_description: detailed explanation as to why you think the source entity and the target entity are related to each other
    relationship_strength: an integer score between 1 and 100, indicating the strength of the relationship between the source entity and target entity. Consider factors such as:
        How directly are the entities connected?
        How important is this relationship in the context of the overall text?
        How frequently or emphatically is this relationship mentioned?
    Format each relationship as ("relationship"|<source_entity>|<target_entity>|<relationship_description>|<relationship_strength>)

-Example session-

    Text: Person A met person B in a coffee shop at xx:xx in Y city.
    Completion:
    ("entity"|A|Person|Person A met Person B in a coffee shop.)
    ("entity"|Y|Location|A city with a coffee shop, and where A and B met.)
    ("entity"|Coffee shop|Location|A coffee shop in Y city where A and B met.)
    ("entity"|B|Person|B met A in the coffee shop in Y city.)
    ("relationship"|A|Y|A went to Y to meet B.|90)
    ("relationship"|B|Y|B went to Y to meet A.|90)
    ("relationship"|Y|Coffee Shop|A coffee shop inside Y city.|80)

-Inference-

    Text: {text}