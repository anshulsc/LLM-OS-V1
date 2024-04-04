
from langchain.vectorstores import chroma
from langchain.embeddings.openai import OpenAIEmbeddings

import argparse
import json
import sys
import os
import re
from dotenv import load_dotenv
load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORGANIZATION = os.getenv("OPENAI_ORGANIZATION")

class ToolManager:
    """
    Manages tools within a repository, including adding, deleting, and retrieving tool information.

    The `ToolManager` class provides a comprehensive interface for managing a collection
    of tools, where each tool is associated with its code, description, and other metadata.
    It supports operations such as adding new tools, checking for the existence of tools,
    retrieving tool names, descriptions, and codes, and deleting tools from the collection.
    It leverages a vector database for efficient retrieval of tools based on similarity searches.

    Attributes:
        generated_tools (dict): Stores the mapping relationship between tool names and their
                                information (code, description).
        generated_tool_repo_dir (str): The directory path where the tools' information is stored,
                                       including code files, description files, and a JSON file
                                       containing the tools' metadata.
        vectordb_path (str): The path to the vector database used for storing and retrieving
                             tool descriptions based on similarity.
        vectordb (Chroma): An instance of the Chroma class for managing the vector database.

    Note:
        The class uses OpenAI's `text-embedding-ada-002` model by default for generating embeddings
        via the `OpenAIEmbeddings` wrapper. Ensure that the `OPENAI_API_KEY` and `OPENAI_ORGANIZATION`
        are correctly set for OpenAI API access.

    This class is designed to facilitate the management of a dynamic collection of tools, providing
    functionalities for easy addition, retrieval, and deletion of tools. It ensures that the tools'
    information is synchronized across a local repository and a vector database for efficient
    retrieval based on content similarity.
    """

    def __init__(self, generated_tool_repo_dir=None) -> None:

        self.generated_tools = {}
        self.generated_tool_repo_dir = generated_tool_repo_dir

        with open(f"{self.generated_tool_repo_dir}/generated_tools.json") as f2:
            self.generated_tools = json.load(f2)

        self.vectordb_path = f"{self.generated_tool_repo_dir}/vectordb"

        if not os.path.exists(self.vectordb_path):
            os.makedirs(self.vectordb_path)
        
        os.makedirs(f"{generated_tool_repo_dir}/tool_code", exist_ok=True)
        os.makedirs(f"{generated_tool_repo_dir}/tool_description", exist_ok=True)


        self.vectordb = chroma.Chroma(
            collection_name="tool_vectordb",
            embedding_function=OpenAIEmbeddings(
                open_api_key = OPENAI_API_KEY,
                open_organization = OPENAI_ORGANIZATION
            ),
            persist_directory=self.vectordb_path
        )

        assert self.vectordb._collection.count() == len(self.generated_tools), (
            f"Tool Manager's vectodb is not synced with generated_tools,json.\n"
            f"There are {self.vectordb._collection.count()} tools in vectordb but {len(self.generated_tools)} tools in generated_tools.json.\n"
        )

    @property
    def program(self):

        program = ""
        for _, entry in self.generated_tools.items():
            program += f"{entry['code']}\n\n"
        return program
    

    @property
    def descriptions(self): 
        """
        Retrieve the descriptions of all tools in a dictionary.

        This property constructs a dictionary where each key is a tool name and its value
        is the description of that tool, extracted from the generated_tools dictionary.

        Returns:
            dict: A dictionary mapping each tool name to its description.
        """
        descriptions = {}
        for tool_name, entry in self.generated_tools.items():
            descriptions.update({tool_name: entry["description"]})
        return descriptions
    

    @property
    def tool_names(self):

        return self.generated_tools.keys()
    
    def get_tool_code(self, tool_name):
        code = self.generated_tools[tool_name]["code"]
        return code 

    def add_new_tool(self, info):
        """
        Adds a new tool to the tool manager, including updating the vector database
        and tool repository with the provided information.

        This method processes the given tool information, which includes the task name,
        code, and description. It prints out the task name and description, checks if
        the tool already exists (rewriting it if so), and updates both the vector
        database and the tool dictionary. Finally, it persists the new tool's code and
        description in the repository and ensures the vector database is synchronized
        with the generated tools.

        Args:
            info (dict): A dictionary containing the tool's information, which must
                         include 'task_name', 'code', and 'description'.

        Raises:
            AssertionError: If the vector database's count does not match the length
                            of the generated_tools dictionary after adding the new tool,
                            indicating a synchronization issue.
        """

        program_name = info["task_name"]
        program_code = info["code"]
        program_description = info["description"]   

        print(
            f"\033[33m {program_name}:\n{program_description}\033[0m")
        
        if program_name in self.generated_tools:
            print(f"\033[33mTool {program_name} already exists. Rewriting!\033[0m")
            self.vectordb._collection.delete(ids=[program_name])


        self.vectordb.add_texts(
            texts=[program_description],
            ids=[program_name],
            metadatas=[{"name": program_name}],
        )

        self.generated_tools[program_name] = {
            "code": program_code,
            "description": program_description,
        }

        assert self.vectordb._collection.count() == len(
            self.generated_tools
        ), "vectordb is not synced with generated_tools.json"

        with open(f"{self.generated_tool_repo_dir}/tool_code/{program_name}.py", "w") as fa:
            fa.write(program_code)
        
        with open(f"{self.generated_tool_repo_dir}/tool_description/{program_name}.txt", "w") as fb:
            fb.write(program_description)
        
        with open(f"{self.generated_tool_repo_dir}/generated_tools.json", "w") as fc:
            json.dump(self.generated_tools, fc, indent=4)
        self.vectordb.persist()


    def exist_tool(self, tool):

        if tool in self.tool_names:
            return True
        return False
    
    def retrieve_tool_name(self, query, k=10):
        """
        Retrieves related tool names based on a similarity search against a query.

        This method performs a similarity search in the vector database for the given
        query and retrieves the names of the top `k` most similar tools. It prints the
        number of tools being retrieved and their names.

        Args:
            query (str): The query string to search for similar tools.
            k (int, optional): The maximum number of similar tools to retrieve.
                               Defaults to 10.

        Returns:
            list[str]: A list of tool names that are most similar to the query,
                       up to `k` tools. Returns an empty list if no tools are found
                       or if `k` is 0.
        """

