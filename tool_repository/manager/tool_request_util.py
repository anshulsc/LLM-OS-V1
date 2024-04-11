import requests
import os
from dotenv import load_dotenv

load_dotenv(override=True)
API_BASE_URL = os.getenv("API_BASE_URL")

class ToolRequestUtil:


    def __init__(self) -> None:

        self.session = requests.session()
        self.headers ={
            
        }