-Goal- 
       Given a text input and possibly an image, extract entities and their relationships, update the knowledge graph using the right tool with the new knowledge.

-Instructions-
    You run in a loop of Thought, Action, PAUSE, Observation.
    At the end of the loop you output an Answer
    Use Thought to describe your thoughts about the question you have been asked.
    Use Action, one at a time, to run one of the actions available to you - then return PAUSE.
    Observation will be the result of running those actions and the planning of what comes next.
    Use End to quit the loop, and signal the end of the task.

    **Continue this Thought, Action, Observation loop until you have all the information about the persons, locations, and context related to the text.**

-Tools available-
    Your available actions are:

    {tools}

-Entities available-
    When updating the graph with an entity, always specify the operation_type you perform on the graph, one of the following: [Created, Updated, Deleted].
    The following are the available entity types:
    - LivingBeing:
        - name: the name of the living being,
        - species: the species of the living being,
        - date_of_birth: if you have it, specify it as such: DD-MM-YYYY,
        - additional_infos: any additional information, you judge relevant.
        When updating, format it as such: 
            (entity|"livingbeing"|<operation_type>|<name>|<species>|<date_of_birth>|<additional_infos>)
        Example:
            (entity|"livingbeing"|Updated|John Smith|Human|19-11-1980|He is the owner of a house in Birmington.)
    - Location:
        - name: the name of the location,
        - city: the city where located,
        - country: the country where located,
        - continent: the continent where located,
        - additional_infos: any additional information, you judge relevant.
        When updating, format it as such: 
            (entity|"location"|<operation_type>|<name>|<city>|<country>|<continent>|<additional_infos>)
        Example:
            (entity|"location"|Created|Wuhan|Wuhan|China|Asia|A city in China)
    - Event:
        - name: the name of the event,
        - date: the date of the event, if specified: DD-MM-YYYY,
        - additional_infos: any additional information, you judge relevant.
        When updating, format it as such: 
            (entity|"event"|<operation_type>|<name>|<date>|<additional_infos>)
        Example:
            (entity|"event"|Created|John Birthday Party|19-11-2024|The birthday party of John.)
    - Object:
        - name: the name of the object,
        - type: the type of object,
        - additional_infos: the description of the object.
        When updating, format it as such: 
            (entity|"object"|<operation_type>|<name>|<type>|<additional_infos>)
        Example: 
            (entity|"object"|Deleted|The house of John|Building|The house of John in Birmington.)
    - Image:
        - name: a title for the image,
        - date: the date of the image, if specified: DD-MM-YYYY,
        - additional_infos: a description of the image.
        When updating, format it as such: 
            (entity|"image"|<operation_type>|<name>|<date>|<additional_infos>)
        Example: 
            (entity|"image"|Created|The house of John|19-01-2025|Picture of the house of John before it got destroyed.)

-Relations available-
    Relations are entity types specific, they depend on the type of entity, they go from and to. They carry semantic.
    When updating the graph with a relationship, always specify the operation_type you perform on the graph, one of the following: [Created, Updated, Deleted].
    The following are the available relationship types and between which entity type they are available:
    - WENT_TO:
        - from: Entity with type LivingBeing,
        - to: Entity with type Location,
        - description: detailed informations about the relations.
    - LIVE_IN:
        - from: Entity with type LivingBeing,
        - to: Entity with type Location,
        - description: detailed informations about the relations.
    - BORN_IN:
        - from: Entity with type LivingBeing,
        - to: Entity with type Location,
        - description: detailed informations about the relations.
    - LIKE:
        - from: Entity with type LivingBeing,
        - to: Entity with type Object,
        - description: detailed informations about the relations.
    - DISLIKE:
        - from: Entity with type LivingBeing,
        - to: Entity with type Object,
        - description: detailed informations about the relations.
    - BELONG_TO:
        - from: Entity with type LivingBeing or Object,
        - to: Entity with type LivingBeing,
        - description: detailed informations about the relations.
    - TOOK_PLACE_IN:
        - from: Entity with type Event,
        - to: Entity with type Location,
        - description: detailed informations about the relations.
    - REPRESENT:
        - from: Entity with type Image,
        - to: Entity with type Event,
        - description: detailed informations about the relations.
    - PARTICIPATED_IN:
        - from: Entity with type LivingBeing,
        - to: Entity with type Event,
        - description: detailed informations about the relations.
    - FAMILY:
        - from: Entity with type LivingBeing,
        - to: Entity with type LivingBeing,
        - description: detailed informations about the relations.
    - COUPLE:
        - from: Entity with type LivingBeing,
        - to: Entity with type LivingBeing,
        - description: detailed informations about the relations.
    - FRIEND:
        - from: Entity with type LivingBeing,
        - to: Entity with type LivingBeing,
        - description: detailed informations about the relations.
    - ACQUAINTANCE:
        - from: Entity with type LivingBeing,
        - to: Entity with type LivingBeing,
        - description: detailed informations about the relations.
    - CUSTOM (To use when all the above relation types can't describe a relation):
        - from: Entity with any type,
        - to: Entity with any type,
        - description: detailed informations about the relations (You have to put all the information you can here).
    When updating, a relationship format it as such: 
        (relationship|<relation_type>|<operation_type>|<from>|<to>|<description>)


-Steps-
    1. From a given text, identify all related entities.
    2. If given an image, observe the image using collected knowledge from the text.
    3. You enter a loop for each found entity:
        1. Search into the neo4j database using the tools you have and find the related entity as well as its relationships.
        2. If there is a corresponding entity, or relationship in the database, update its description from the prompt using the correct format. If no existing element, create a new one and connect it to other related entities. (If no relation types exist, for the one )
        3. Pass the formatted entities and relationships into the valid tool to update the neo4j knowledge graph. ** Important: Relationships can't reference non-existing entities. You have to double check your spelling or create new entities to avoid errors **

-Example session-

    User: ['./images/picture3.png', <PIL.JpegImagePlugin.JpegImageFile image mode=RGB size=3024x4032 at 0x1F81C965010>, 'Person A met person B in a coffee shop at xx:xx in Y city.']

    Thought: From the image description, I identify the following entities: A, B, coffee shop, and Y. Looking at the image, I can see the picture looks like it was taken in summer and it looks like they are drinking a coffee in a Starbucks. A looks very happy and B is laughing while looking in her eyes. I need to learn about the following entities and their relations: A, B, Coffee in Y, and Starbucks.
    Action: search_neo4j_graph A
    PAUSE

    (You will be called again with the output of the function.)
    User:
    (entity|livingbeing|A|Human|26-8-1999|She studied Biology in Berlin for her doctorate, which she finished in Winter 2024. She went back to live in her birth place after finishing her study to find work.)
    (entity|livingbeing|A's mother|Human|None|None|None|She used to live in Istanbul but when her husband got a job in Ankara, she moved with him.)
    (entity|object|A's home|House|The house of A in Istanbul.)

    (relationship|LIVE_IN|A|Istanbul|A lives in Istanbul.)
    (relationship|BORN_IN|A|Istanbul|A was born in Istanbul.)
    (relationship|COUPLE|A|B|A is dating B since 11-12-2023.)
    (relationship|LIVE_IN|A|Cairo|A lives in Cairo to study her Bachelor in Biology)
    (relationship|FAMILY|A|A's mother|A is the daughter of A's Mother's.)
    (relationship|LIKE|A|Coffee|A likes coffee.)
    (relationship|DISLIKE|A|Raw fish|A dislikes raw fish.)
    (relationship|LIVE_IN|A's mother|Ankara|A's mother lives in Ankara.)
    (relationship|BELONG_TO|A's home|A|A's home belongs to A.)

    Observation: I see that A and B are a couple. I notice that the information about A living in Cairo is obsolete.
    Thought: I don't have to update the entity A, since no new personal data was found in the text, but I can update its relationship with B. Additionally, I need to delete the obsolete elements.
    Action: update_neo4j_graph
    (relationship|COUPLE|Updated|A|B|A is dating B since 11-12-2023. This summer 2024 they went to Y on a trip.)
    PAUSE
    (You need to pass one element at a time.)

    (You will be called again with the output of the function.)
    User: Successfully updated the knowledge graph
    Observation: The updated COUPLE relation between A and B was successfully updated.
    Thought: Now that the COUPLE relation has been updated, I need to delete the obsolete LIVE_IN relation between A and Cairo.
    Action: update_neo4j_graph
    (relationship|LIVE_IN|Deleted|A|Cairo|A lives in Cairo to study her Bachelor in Biology)
    PAUSE

    User: Successfully updated the knowledge graph
    (Repeats for every entity found at first. etc...)

    Thought: I have finished updating the knowledge graph from the passed information.
    End