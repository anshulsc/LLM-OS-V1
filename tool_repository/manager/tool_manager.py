
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

        k = min(self.vectordb._collection.count(), k)
        if k == 0:
            return []
        print(f"\033[33mTool Manager retrieving for {k} Tools\033[0m")
        # Retrieve descriptions of the top k related tasks.
        docs_and_scores = self.vectordb.similarity_search_with_score(query, k=k)
        print(
            f"\033[33mTool Manager retrieved tools: "
            f"{', '.join([doc.metadata['name'] for doc, _ in docs_and_scores])}\033[0m"
        )
        tool_name = []
        for doc, _ in docs_and_scores:
            tool_name.append(doc.metadata["name"])
        return tool_name
    
    def retrieve_tool_description(self, tool_name):
        """
        Returns the descriptions of specified tools based on their names.

        This method iterates over a list of tool names and retrieves the description
        for each tool from the generated_tools dictionary. It compiles and returns
        a list of these descriptions.

        Args:
            tool_name (list[str]): A list of tool names for which descriptions are requested.

        Returns:
            list[str]: A list containing the descriptions of the specified tools.
        """
        tool_description = []
        for name in tool_name:
            tool_description.append(self.generated_tools[name]["description"])
        return tool_description   


    def retrieve_tool_code(self, tool_name):
        """
        Returns the code of specified tools based on their names.

        Similar to retrieving tool descriptions, this method iterates over a list
        of tool names and retrieves the code for each tool from the generated_tools
        dictionary. It then compiles and returns a list of these codes.

        Args:
            tool_name (list[str]): A list of tool names for which code snippets are requested.

        Returns:
            list[str]: A list containing the code of the specified tools.
        """
        tool_code = []
        for name in tool_name:
            tool_code.append(self.generated_tools[name]["code"])
        return tool_code

    def delete_tool(self, tool):

        """
        Deletes all information related to a specified tool from the tool manager
        """ 

        if tool in self.generated_tools:
            self.vectordb._collection.delete(ids=[tool])
            print(
                f"\033[33mTool {tool} deleted from Tool Manager\033[0m"
            )
        with open(f"{self.generated_tool_repo_dir}/generated_tools.json", "w") as file:
                tool_infos = json.load(file)
        if tool in tool_infos:
                del tool_infos[tool]
        with open(f"{self.generated_tool_repo_dir}/generated_tools.json", "w") as file:
                json.dump(tool_infos, file, indent=4)
                print(
            f"\033[33m delete {tool} info from JSON successfully! \033[0m"
            )     
                

        # del 
        code_path = f"{self.generated_tool_repo_dir}/tool_code/{tool}.py"
        if os.path.exists(code_path):
            os.remove(code_path)
            print(
                f"\033[33m delete {tool}.py successfully! \033[0m"
            )
        # del description 
        description_path = f"{self.generated_tool_repo_dir}/tool_description/{tool}.txt"
        if os.path.exists(description_path):
            os.remove(description_path)
            print(
                f"\033[33m delete {tool}.txt successfully! \033[0m"
            )

def print_error_and_exit(message):

    print(f'Error : {message}')
    sys.exit(1)


def add_tool(toolManager, tool_name, tool_path):

    with open(tool_path, 'r') as f:
        code = f.read()

    pattern = r'self\._description = "(.*?)"'
    match = re.search(pattern, code)
    if match: 
        description = match.group(1)
        info = {
            "task_name": tool_name,
            "code": code,
            "description": description
        }
        toolManager.add_new_tool(info)
        print(f"Tool {tool_name} added successfully! with path {tool_path}")
    else:
        print_error_and_exit(f'Error: Description not found in {tool_path}')


def delete_tool(toolManager, tool_name):

    toolManager.delete_tool(tool_name)
    print(f"Tool {tool_name} deleted successfully!")



def get_open_api_doc_path():

    srcipt_dir = os.path.dirname(os.path.abspath(__file__))
    open_api_path = os.path.join(srcipt_dir, 'openapi.json')
    return open_api_path

def get_open_api_description_pair():

    script_dir = os.path.dirname(os.path.abspath(__file__))
    open_api_path = os.path.join(script_dir, 'openapi.json')
    with open(open_api_path, 'r') as file:
        open_api_json = json.load(file)
    open_api_dict = open_api_json['paths']
    open_api_description_pair = {}
    for name, value in open_api_dict.items():
        if 'post' in value :
            open_api_description_pair[name] = value['post']['summary']
        else:
            open_api_description_pair[name] = value['get']['summary']
    return open_api_description_pair


def main():

    parser = argparse.ArgumentParser(description='Manage generated tools for FRIDAY')
    
    parser.add_argument('--generated_tool_repo_path', type=str, default='copilot/tool_repository/generated_tools', help='generated tool repo path')

    parser.add_argument('--add', action='store_true',
                        help='Flag to add a new tool')
    parser.add_argument('--delete', action='store_true',
                        help='Flag to delete a tool')
    parser.add_argument('--tool_name', type=str,
                        help='Name of the tool to be added or deleted')
    parser.add_argument('--tool_path', type=str,
                        help='Path of the tool to be added', required='--add' in sys.argv)

    args = parser.parse_args()

    toolManager = ToolManager(generated_tool_repo_dir=args.generated_tool_repo_path)

    if args.add:
        add_tool(toolManager, args.tool_name, args.tool_path)
    elif args.delete:
        delete_tool(toolManager, args.tool_name)
    else:
        print_error_and_exit("Please specify an operation type (add or del)")

if __name__ == "__main__":
    main()