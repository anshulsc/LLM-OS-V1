import openai
import logging
import os 
from dotenv import load_dotenv

load_dotenv(override=True)
MODEL_NAME = os.getenv("MODEL_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORGANIZATION = os.getenv("OPENAI_ORGANIZATION")
BASE_URL = os.getenv("BASE_URL")

class OpenAI:

    def __init__(self):
        self.model_name = MODEL_NAME


    def chat(self, messages, temperature= 0):

        response = openai.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature
        )
        logging.info(f"Response : {response.choices[0].message.content}")

        return response.choices[0].message.content
    

def main():
    message = [{'role':'user', 'content': 'hello'},]

    llm = OpenAI()
    print(llm.chat(message))

if __name__ == "__main__":
    main()