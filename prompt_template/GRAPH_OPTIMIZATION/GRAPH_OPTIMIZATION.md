-Goal-
    After receiving 2 or more graph entities, merge similar embedded entities of the graph as one as well as their relation ships if they meet the criteria of their label, or return them untouched.

-Merge Criterias-
    The criterias for merging depend on the label of the entities:
        - LivingBeing: (entity|livingbeing|<operation_type>|<name>|<species>|<date_of_birth>|<additional_infos>)
            When: You can merge livingbeing entities only if they share a similar name, species and date_of_birth. 
            How: Take the most detailled name, species and date_of_birth and merge the two additional_infos to keep the informations of both.
            Examples:
                1. Merge situation example (same entity with information spread across classes.)
                    Prompt:
                        (entity|livingbeing||John|Human|??-11-1980|He is the owner of a house in Birmington.)
                        (entity|livingbeing||John Smith|Human|19-11-1980|He works at a bank.)
                    Completion:
                        (entity|livingbeing|Updated|John Smith|Human|19-11-1980|He works at a bank and owns a house in Birmington.)
                2. Preserve situation example (different entities)
                    Prompt:
                        (entity|livingbeing||John|Human|??-11-1980|He is the owner of a house in Birmington.)
                        (entity|livingbeing||Clara Smith|Human|19-11-1985|She leaves in London.)
                    Completion:
                        (entity|livingbeing|Preserved|John|Human|??-11-1980|He is the owner of a house in Birmington.)
                        (entity|livingbeing|Preserved|Clara Taylor|Human|19-11-1985|She leaves in London.)
        - Location: (entity|location|<operation_type>|<name>|<city>|<country>|<continent>|<additional_infos>)
            When: You can merge location entities only if they share a similar name, city, country and continent. 
            How: Take the correct information for the city, country and continent and merge the two names and additional_infos to keep the informations of both.
            Example:
                1. Merge situation example (same entity with information spread across classes.)
                    Prompt:
                        (entity|location||Wuhan|Wuhan|China|Asia|A city in China)
                        (entity|location||City of Wuhan|Wuhan|China|Asia|A chinese city where John comes from.)
                    Completion:
                        (entity|location|Updated|Wuhan|Wuhan|China|Asia|A chinese city where John comes from.)
                2. Preserve situation example (different entities)
                    Prompt:
                        (entity|location||Wuhan|Wuhan|China|Asia|A city in China)
                        (entity|location||Beijing|Beijing|China|Asia|)
                    Completion:
                        (entity|location|Preserved|Wuhan|Wuhan|China|Asia|A city in China)
                        (entity|location|Preserved|Beijing|Beijing|China|Asia|)
        - Event: (entity|event|<operation_type>|<name>|<date>|<additional_infos>)
            When: You can merge event entities only if they share a similar name, and date. 
            How: Merge the information of all the arguments.
            Example:
                1. Merge situation example (same entity with information spread across classes.)
                    Prompt:
                        (entity|event||Noé and Sophie's Visit to St. Peter's Square|2024-03-15|Noé and Sophie visited St. Peter's Square in Vatican City.)
                        (entity|event||Europe Trip|2024-12-XX|Noé and Sophie's trip to Europe, including a visit to Vatican City.)
                        (entity|event||Romantic Trip to Europe|Winter 2024|Noé and Sophie's romantic trip across Europe during winter 2024.)
                        (entity|event||Winter Trip to Strasbourg|2024-12-XX|Noé and Sophie's winter trip to Strasbourg.)
                    Completion:
                        (entity|event|Created|Noé and Sophie's Winter 2024 trip in Europe|Winter 2024|During this trip Noé and Sophie explored a lot of places like Strasbourg and Vatican City.)
                2. Preserve situation example (different entities)
                    Prompt:
                        (entity|event||John Birthday Party|19-11-2024|The birthday party of John.)
                        (entity|event||John Wedding with Clara|14-05-2015|The wedding of John and Clara in Spain.)
                    Completion:
                        (entity|event|Preserved|John Birthday Party|19-11-2024|The birthday party of John.)
                        (entity|event|Preserved|John Wedding with Clara|14-05-2015|The wedding of John and Clara in Spain.)
        - Object: (entity|object|<operation_type>|<name>|<type>|<additional_infos>)
            When: You can merge object entities only if they share a similar name, and type. 
            How: Keep the most precise name and type, and merge the information of both additional_infos.
            Example:
                1. Merge situation example (same entity with information spread across classes.)
                    Prompt:
                        (entity|object||Noé's Computer|Laptop|The computer of Noé.)
                        (entity|object||The computer of Noé|Electronics|Bought in 2022.)
                    Completion:
                        (entity|object|Updated|Noé's Computer|Laptop|The computer of Noé he bought in 2022.)
                2. Preserve situation example (different entities)
                    Prompt:
                        (entity|object||Churros|Food|The favorite snack of Sophie.)
                        (entity|object||The toy of John's dog|Dog toy|The favorite toy of Dagobert.)
                    Completion:
                        (entity|object|Preserved|Churros|Food|The favorite snack of Sophie.)
                        (entity|object|Preserved|The toy of John's dog|Dog toy|The favorite toy of Dagobert.)
    Additionally, you will also receive the relationships of the entities you are comparing, in the case, you merge two entities you must also update and merge the relationships. Relationships are formatted as such: (relationship|<relation_type>|<operation_type>|<from>|<to>|<description>) e.g. (relationship|BORN_IN|A|Istanbul|A was born in Istanbul.)

-Example Session-
    1. Merge situation example (same entity with information spread across classes.)
        User:
        (entity|event||Noé and Sophie's Visit to St. Peter's Square|2024-03-15|Noé and Sophie visited St. Peter's Square in Vatican City.)
        (entity|event||Europe Trip|2024-12-XX|Noé and Sophie's trip to Europe, including a visit to Vatican City.)
        (entity|event||Romantic Trip to Europe|Winter 2024|Noé and Sophie's romantic trip across Europe during winter 2024.)
        (entity|event||Winter Trip to Strasbourg|2024-12-XX|Noé and Sophie's winter trip to Strasbourg.)

        (relationship|TOOK_PLACE_IN|Noé and Sophie's Visit to St. Peter's Square|St. Peter's Square|The visit took place in St. Peter's Square on December 19th, 2024.)
        (relationship|CUSTOM|Noé and Sophie's Visit to St. Peter's Square|Europe Trip|This visit to St. Peter's Square was part of a larger trip to Europe. The Europe trip encompassed multiple locations and activities.)
        (relationship|TOOK_PLACE_IN|Romantic Trip to Europe|Strasbourg|Noé and Sophie visited Strasbourg during their romantic trip.)
        (relationship|TOOK_PLACE_IN|Romantic Trip to Europe|Europa Park|Noé and Sophie visited Europa Park during their romantic trip.)
        (relationship|TOOK_PLACE_IN|Romantic Trip to Europe|Colmar|Noé and Sophie visited Colmar during their romantic trip.)
        (relationship|TOOK_PLACE_IN|Winter trip to Strasbourg|Strasbourg|The winter trip took place in Strasbourg.)
        (relationship|PARTICIPATED_IN|Sophie|Winter trip to Strasbourg|Sophie participated in the winter trip to Strasbourg.)
        (relationship|PARTICIPATED_IN|Noé|Winter trip to Strasbourg|Noé participated in the winter trip to Strasbourg.)
        (relationship|PARTICIPATED_IN|Sophie|Noé and Sophie's Visit to St. Peter's Square|Sophie participated in the visit to St. Peter's Square.)
        (relationship|PARTICIPATED_IN|Noé|Noé and Sophie's Visit to St. Peter's Square|Noé participated in the visit to St. Peter's Square.)
        (relationship|PARTICIPATED_IN|Sophie|Romantic Trip to Europe|Sophie participated in a romantic trip to Europe with Noé during winter 2024.)
        (relationship|PARTICIPATED_IN|Noé|Romantic Trip to Europe|Noé participated in a romantic trip to Europe with Sophie during winter 2024.)
        (relationship|REPRESENT|Strasbourg Christmas Tree with Noé and Sophie|Winter trip to Strasbourg|The image represents the winter trip to Strasbourg.)

        Model:
        (entity|event|Created|Noé and Sophie's Winter 2024 trip in Europe|Winter 2024|During this trip Noé and Sophie explored a lot of places like Strasbourg and Vatican City.)

        (relationship|TOOK_PLACE_IN|Noé and Sophie's Winter 2024 trip in Europe|St. Peter's Square|The visit took place in St. Peter's Square on December 19th, 2024.)
        (relationship|TOOK_PLACE_IN|Noé and Sophie's Winter 2024 trip in Europe|Strasbourg|Noé and Sophie visited Strasbourg during their romantic trip.)
        (relationship|TOOK_PLACE_IN|Noé and Sophie's Winter 2024 trip in Europe|Europa Park|Noé and Sophie visited Europa Park during their romantic trip.)
        (relationship|TOOK_PLACE_IN|Noé and Sophie's Winter 2024 trip in Europe|Colmar|Noé and Sophie visited Colmar during their romantic trip.)
        (relationship|TOOK_PLACE_IN|Noé and Sophie's Winter 2024 trip in Europe|Strasbourg|The winter trip took place in Strasbourg.)
        (relationship|PARTICIPATED_IN|Sophie|Noé and Sophie's Winter 2024 trip in Europe|Sophie participated in the winter 2024 trip to Europe with Noé.)
        (relationship|PARTICIPATED_IN|Noé|Noé and Sophie's Winter 2024 trip in Europe|Noé participated in the winter 2024 trip to Europe with Sophie.)
        (relationship|REPRESENT|Strasbourg Christmas Tree with Noé and Sophie|Noé and Sophie's Winter 2024 trip in Europe|The image represents the winter trip in Strasbourg.)


    2. Preserve situation example (different entities)
        User:
        (entity|livingbeing||Sophie|Human|16-10-2001|Sophie is dating Noé. She lives in Montreal with Noé and her dog Rookie.  Two of her greatest joys are traveling and eating churros.)
        (entity|livingbeing||Rookie|Dog|20-10-2022|Medium Shiba Inu; Can be cute, selfish, and dominant)
        (entity|livingbeing||Sarah|Human|None|Girlfriend of Elliot)

        (relationship|COUPLE||Sophie|Noé|)
        (relationship|CUSTOM||Sophie|Sarah|Sophie and Sarah met during a trip to Europa Park.)
        (relationship|CUSTOM||Sophie|Sarah|Sophie and Sarah met during a trip to Europa Park.)
        (relationship|WENT_TO||Sophie|Saint Peter's Square|Sophie visited St Peter's Square.)
        (relationship|BELONG_TO||Rookie|Sophie|Rookie belongs to Sophie.)

        Model: Nothing to merge.