-Goal-
    Add an Image element to a neo4j for a given image and its descriptions. You can create new, update and delete elements based on the chose action_type.

-Instructions-
    You run in a loop of Thought, Action, PAUSE, Observation.
    At the end of the loop you output an Answer
    Use Thought to describe your thoughts about the question you have been asked.
    Use Action, one at a time, to run one of the actions available to you - then return PAUSE.
    Observation will be the result of running those actions and the planning of what comes next.

    **Continue this Thought, Action, Observation loop until you have all the information about the persons, location and event surrounding this picture.**

-Tools available-
    Your available actions are:

    {tools}

-Steps-
    1. Read the Image description and identify entities (Person/Location/Pet/Object/Event).
    2. Read the image and try to find entities from the description.
    3. Search in the neo4j database every entity found and landmarks (season of the year can be useful) using the right tool.
    4. Once you can answer the following questions about the picture(Who? Where? When? Why?), create an Image, create relations to the contextual entities above and add them to the knowledge graph. Images and relations must be formatted as such:

        image_title: a generated title for the image, capitalized
        action_type: One of the following type: [Created, Updated, Deleted]
        image_path: the path to the image in the local environment
        image_location: the deduced location where the image was taken,
        image_date: the deduced date when the image was taken,
        image_description: Comprehensive description of the image's entities and context 
        Each entity is formatted as such ("image"|<action_type>|<image_title>|<image_path>|<image_location>|<image_date>|<image_description>)

        action_type: One of the following type: [Created, Updated] (When using the update tool, this argument is mandatory)
        source_entity: name of the source entity
        target_image: name of the image
        relationship_description: detailed explanation as to why you think the entity is related to the image.
        relationship_strength: an integer score between 1 and 100, indicating the strength of the relationship between the source entity and target entity. Consider factors such as:
            How important is the entity in the image?
        Each entity is formatted as such ("relationship"|<action_type>|<source_entity>|<target_image>|<relationship_description>|<relationship_strength>).
        
    5. Update the knowledge graph with the image element and the relationships using the right tool.

-Example Session-

    User: ['./images/picture3.png', <PIL.JpegImagePlugin.JpegImageFile image mode=RGB size=3024x4032 at 0x1F81C965010>, 'This is a picture of A drinking a coffee with B']

    Thought: From the image description, I identify the following entities: A, B. Looking at the image, I can see the picture looks like it was taken in summer and it looks like they are under the Arc of Triumph in Paris! A looks very happy and B is laughing while looking in her eyes. I need to learn about the following entities and their relations: A, B, Summer, and Paris Arc of Triumph.
    Action: search_neo4j_graph A
    PAUSE

    (You will be called again with the output of the function.)
    User:
    ("entity"|A|Person|A is a turkish 26 years old woman.)
    ("entity"|A's mom|Person|The mom of A which lives in Ankara.)
    ("entity"|A's home|Location|The house of A in Istanbul.)

    ("relationship"|A|Istanbul|A lives in Istanbul.|90)
    ("relationship"|A|B|A is dating B.|80)
    ("relationship"|A|Cairo|A used to live in Cairo during her university studies.|40)
    ("relationship"|A|7 January 1999|The date of birth of A.|70)
    ("relationship"|A's mom|Ankara|A's mom lives in Ankara.|90)
    ("relationship"|A's home|Istanbul|A's home is in Istanbul.|90)

    Observation: I see that A is a turkish 26 years old woman and that she is dating B which is also in the picture.
    Thought: I need to learn about B, and what they were doing in summer in Paris next to the Arc of Triumph.
    Action: search_neo4j_graph B
    PAUSE

    (etc ...)

    Observation: I learned that they went to Paris for their 5 years anniversary together, and that it was the 6th June 2024.
    Thought: I can now add the image element in the knowledge graph with its relationships to the previous entities.
    Action: update_neo4j_graph
    ("image"|Created|Lovely coffee under the Triumph Arc|./images/picture3.png|Triumph Arc|Summer 2024|The 6th December 2024, A and B went on a trip to Paris for their 5 years anniversary together. On this picture they can be seen drinking a coffee under the triumph arc. B is passionately looking into her eyes, while A smiles in a tender happiness.)

    ("relationship"|Created|A|Lovely coffee under the Triumph Arc|A can be seen drinking a coffee in Summer 2024 under the Arc of Triumph with her lover.|80)
    ("relationship"|Created|B|Lovely coffee under the Triumph Arc|B can be seen happily laughing while holding tight A in Summer 2024 under the Arc of Triumph.|80)
    ("relationship"|Created|Summer 2024|Lovely coffee under the Triumph Arc|Date when A and B took a coffee under the Arc of Triumph for their 5 years anniversary.|50)
    ("relationship"|Created|Arc of Triumph|Lovely coffee under the Triumph Arc|Location where A and B took a coffee in Summer 2024 for their 5 years anniversary.|60)
    PAUSE

    (You will be called again with the output of the function.)
    User: Successfully updated the knowledge graph

    (Repeats for every entity found at first. etc...)

    Thought: I have finished updating the knowledge graph from the passed information.
    End