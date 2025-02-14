
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from langchain_core.prompts import PromptTemplate
from tools import update_neo4j_graph, search_neo4j_graph, load_image, encode_image, replace_emotes, find_image
from PIL import Image
import time
import ast

import os
from dotenv import load_dotenv
load_dotenv()

class ReActAgent:
    """
    A class to represent a ReActAgent that interacts with a gemini model and tools to generate responses based on user input.
    Attributes:
    -----------
    model : object
        The model used for generating responses.
    tools : list
        A list of tools that the agent can use to fetch additional information.
    messages : list(dict(str, str))
        A list to store the conversation history.
    Methods:
    --------
    __init__(model, tools, system="")
        Initializes the ReActAgent with a model, tools, and an optional system message.
    __call__(message)
        Processes the user message, interacts with the model and tools, and returns the final response.
    execute()
        Sends the latest user message to the model and returns the model's response.
    """
    def __init__(self, model, tools, system=""):
        self.tools = tools
        self.messages = []
        if system is not None:
            self.messages.append({"role": "model", "parts": system})
        self.model = model.start_chat(history = self.messages)
            
    def __call__(self, message, verbose=False):
        """
        Handles the incoming message, processes it through the Thought/Action/Observation ReAct loop using the available tools, and returns the response.
        Args:
            message (str): The message to be processed.
            verbose (bool, optional): If True, enables verbose output. Defaults to False.
        Returns:
            str: The final response after processing the message.
        """
        self.messages.append({"role": "user", "parts": message})
        while True:
            response = self.execute(verbose)
            self.messages.append({"role": "model", "parts": response})
            if not response.strip().endswith("PAUSE") or response.strip().endswith("End"):
                break
            response = response.split("Action:")[1].split("PAUSE")[0]
            for tool in self.tools:
                if tool.name in response:
                    entity_name = response.split(tool.name)[1].split("PAUSE")[0]
                    try:
                        self.messages.append({"role": "user", "parts": tool.invoke(entity_name)})
                    except Exception as e:
                        self.messages.append({"role": "user", "parts": f"Error ({e}): {entity_name}"})
                        if not verbose:
                            print(f"Error ({e}):",entity_name)
                    break
                
        return response
    
    def execute(self, verbose):
        """
        Executes the model by sending the last message in the messages list.

        Args:
            verbose (bool): If True, prints the user message and model's response for each loop.

        Returns:
            str: The text response from the model.
        """
        if verbose:
            print("User:", self.messages[-1]["parts"])
        while True:
            try:
                completion = self.model.send_message(self.messages[-1]["parts"])
                break
            except ResourceExhausted:
                time.sleep(5)
            except Exception as e:
                return f"An error occurred: {e}"
        if verbose:
            print("Model:" + completion.text)
        return completion.text
    
class UpdateAgent(ReActAgent):
    def __init__(self, max_output_tokens: int=30000, temperature: float=0.5):
        system="You are a smart and curious database management agent. From a given text, you test the knowledge of a graph database and update it."
        
        tools = [update_neo4j_graph, search_neo4j_graph, load_image]
        
        instruction_template = PromptTemplate.from_template(open("./prompt_template/ENTITIES_RELATIONS_GENERATION/ENTITIES_RELATIONS_GENERATION.md", "r").read())
        instructions = instruction_template.invoke({"tools": tools}).to_string()
        
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel(
            model_name = os.environ.get("DEFAULT_AI_GEMINI_MODEL"),
            system_instruction= instructions,
            generation_config = genai.GenerationConfig(
                max_output_tokens=max_output_tokens,
                temperature=temperature,
            )
        )
        
        return super().__init__(model, tools, system)
    
    def __call__(self, message: str, image_path: str = "", verbose=False):
        message = "Images and knowledges are stored in a graph database. Use tools to update the following knowledge: \n" + message
        
        if image_path != "":
            image = Image.open(image_path)
        else:
            image = ""
        
        return super().__call__(message=[image_path, image, message], verbose=verbose)
        
class AnswerAgent(ReActAgent):
    def __init__(self, max_output_tokens: int=30000, temperature: float=0.5):
        system="You are a caring, harmless and helpful assistant answering questions about a graph database, helping people remember pasts events and make decisions accordingly."
        
        tools = [search_neo4j_graph, find_image, load_image]
        
        instruction_template = PromptTemplate.from_template(open("./prompt_template/USER_ANSWER/USER_ANSWER.md", "r").read())
        instructions = instruction_template.invoke({"tools": tools}).to_string()
        
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel(
            model_name = os.environ.get("DEFAULT_AI_GEMINI_MODEL"),
            system_instruction= instructions,
            generation_config = genai.GenerationConfig(
                max_output_tokens=max_output_tokens,
                temperature=temperature,
            )
        )
        
        super().__init__(model, tools, system)
        
    def __call__(self, message:str, image_path:str = "", verbose=False):
        if image_path != "":
            image = Image.open(image_path)
        else:
            image = ""
        
        message = "Images and knowledges are stored in a graph database. Access the information you don't have using the available tools: \n" + message
        
        completion = super().__call__(message=[image, message], verbose=verbose)
        print(completion)
        try:
            completion = completion.split("Answer:")[1].strip()
        except IndexError:
            pass
        try:
            response_dict = ast.literal_eval(completion)
            response_dict["message"] = replace_emotes(response_dict["message"]).strip()
        except (SyntaxError, ValueError) as e:
            raise Exception(f"Error when parsing completion: {e};\n", completion)

        return response_dict