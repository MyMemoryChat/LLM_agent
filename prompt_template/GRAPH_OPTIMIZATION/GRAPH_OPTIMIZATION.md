-Goal-
    Decide if 2 entities with/without relationships are the same or not. 
        - If yes, create a new entity regrouping the information of both with the right relationships.
        - If no, return "Nothing to merge.".

-Merging Criterias-
    The criterias for merging depend on the label of the entities:
        - LivingBeing: (entity|livingbeing|<operation_type>||<name>|<species>|<date_of_birth>|<additional_infos>)
            When: They represent the same livingbeing but with different informations. 
            How: Take the most detailled name, species and date_of_birth and merge the two additional_infos to keep the informations of both.
        - Location: (entity|location|<operation_type>||<name>|<city>|<country>|<continent>|<additional_infos>)
            When: You can merge location entities only if they share a similar name, city, country and continent. 
            How: Take the correct information for the city, country and continent and merge the two names and additional_infos to keep the informations of both.
        - Event: (entity|event|<operation_type>||<name>|<date>|<additional_infos>)
            When: You can merge event entities only if they share a similar name, and date. 
            How: Merge the information of all the arguments.
        - Object: (entity|object|<operation_type>||<name>|<type>|<additional_infos>)
            When: You can merge object entities only if they share a similar name, and type. 
            How: Keep the most precise name and type, and merge the information of both additional_infos.
    Merging two entities of different labels is possible, since a wrong label could have been given at some point.
    Additionally, you will also receive the relationships of the entities you are comparing. When merging the entities, you need to specify the relationship with the newly created entity. 
    Relationships are formatted as such: (relationship|<operation_type>||<relation_type>|<from>|<to>|<description>) e.g. (relationship|||BORN_IN|A|Istanbul|A was born in Istanbul.)

-Important notice-
    - You must output the list of entities and relationships to CREATE or return "Nothing to merge." if the two entities are different.
    - Don't return any code.
    - If there is no merging to do, return "Nothing to merge."! Not following this would lead to crash and/or catastrophic forgetting of graph entities.

-Example Session 1-
    User:
    (entity|event|||Romantic Trip to Europe|Winter 2024|Noé and Sophie's romantic trip across Europe during winter 2024.)

    (relationship|||TOOK_PLACE_IN|Romantic Trip to Europe|Strasbourg|Noé and Sophie visited Strasbourg during their romantic trip.)
    (relationship|||TOOK_PLACE_IN|Romantic Trip to Europe|Europa Park|Noé and Sophie visited Europa Park during their romantic trip.)
    (relationship|||TOOK_PLACE_IN|Romantic Trip to Europe|Colmar|Noé and Sophie visited Colmar during their romantic trip.)
    (relationship|||PARTICIPATED_IN|Sophie|Romantic Trip to Europe|Sophie participated in a romantic trip to Europe with Noé during winter 2024.)
    (relationship|||PARTICIPATED_IN|Noé|Romantic Trip to Europe|Noé participated in a romantic trip to Europe with Sophie during winter 2024.)
    --------------------------------------------------
    (entity|event|||Winter Trip to Strasbourg|2024-12-XX|Noé and Sophie's winter trip to Strasbourg.)

    (relationship|||TOOK_PLACE_IN|Winter trip to Strasbourg|Strasbourg|The winter trip took place in Strasbourg.)
    (relationship|||PARTICIPATED_IN|Sophie|Winter trip to Strasbourg|Sophie participated in the winter trip to Strasbourg.)
    (relationship|||PARTICIPATED_IN|Noé|Winter trip to Strasbourg|Noé participated in the winter trip to Strasbourg.)
    (relationship|||REPRESENT|Strasbourg Christmas Tree with Noé and Sophie|Winter trip to Strasbourg|The image represents the winter trip to Strasbourg.)

    Model: (All those events took place during the same period, are geographically close and have the same participants, hence they can be grouped as one.)
    (entity|event|Created||Noé and Sophie's Winter 2024 trip in Europe|Winter 2024|During this trip Noé and Sophie explored a lot of places like Strasbourg and Vatican City.)

    (relationship|Created||TOOK_PLACE_IN|Noé and Sophie's Winter 2024 trip in Europe|Strasbourg|Noé and Sophie visited Strasbourg during their romantic trip.)
    (relationship|Created||TOOK_PLACE_IN|Noé and Sophie's Winter 2024 trip in Europe|Europa Park|Noé and Sophie visited Europa Park during their romantic trip.)
    (relationship|Created||TOOK_PLACE_IN|Noé and Sophie's Winter 2024 trip in Europe|Colmar|Noé and Sophie visited Colmar during their romantic trip.)
    (relationship|Created||TOOK_PLACE_IN|Noé and Sophie's Winter 2024 trip in Europe|Strasbourg|The winter trip took place in Strasbourg.)
    (relationship|Created||PARTICIPATED_IN|Sophie|Noé and Sophie's Winter 2024 trip in Europe|Sophie participated in the winter 2024 trip to Europe with Noé.)
    (relationship|Created||PARTICIPATED_IN|Noé|Noé and Sophie's Winter 2024 trip in Europe|Noé participated in the winter 2024 trip to Europe with Sophie.)
    (relationship|Created||REPRESENT|Strasbourg Christmas Tree with Noé and Sophie|Noé and Sophie's Winter 2024 trip in Europe|The image represents the winter trip in Strasbourg.)

-Example Session 2-
    User:
    (entity|livingbeing|||Sophie|Human|16-10-2001|Sophie is dating Noé. She lives in Montreal with Noé and her dog Rookie.  Two of her greatest joys are traveling and eating churros.)

    (relationship|||COUPLE|Sophie|Noé|)
    (relationship|||CUSTOM|Sophie|Sarah|Sophie and Sarah met during a trip to Europa Park.)
    (relationship|||CUSTOM|Sophie|Sarah|Sophie and Sarah met during a trip to Europa Park.)
    (relationship|||WENT_TO|Sophie|Saint Peter's Square|Sophie visited St Peter's Square.)
    (relationship|||BELONG_TO|Rookie|Sophie|Rookie belongs to Sophie.)
    --------------------------------------------------
    (entity|livingbeing|||Sarah|Human|None|Girlfriend of Elliot)

    Model: Nothing to merge. (They are two different livingbeing)

-Inference-
    User: {input}
    Model: