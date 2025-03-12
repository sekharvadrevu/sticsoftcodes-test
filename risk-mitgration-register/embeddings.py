import logging
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
load_dotenv()
# Load environment variables
AZURE_OPENAI_KEY = os.getenv("azure_openai_key")
AZURE_OPENAI_ENDPOINT = os.getenv("azure_oepnai_endpoint")
EMBEDDING_API_VERSION = os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION")

class GetEmbeddings:
    def __init__(self):
        
        self.client = AzureOpenAI(
            api_key=AZURE_OPENAI_KEY,
            api_version=EMBEDDING_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            azure_deployment="text-embedding-ada-002"  # This is your deployment name for the model
        )

    def generate_embeddings(self, field_value):
        try:
            response = self.client.embeddings.create(input=[field_value], model="text-embedding-ada-002")
            embedding = response.data[0].embedding
            logging.info(f"Embedding generated successfully for the value: {field_value}")
            return embedding
        except Exception as e:
            logging.error(f"Error generating embedding for field value {field_value}: {str(e)}")
            return []
    def sanitize_field_name(field_name):
     return field_name.replace(" ", "_").replace("-", "_").lower()