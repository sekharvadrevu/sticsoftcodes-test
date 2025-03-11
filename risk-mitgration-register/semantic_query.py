
from azure.search.documents import SearchClient
from dotenv import load_dotenv
import os
from azure.core.credentials import AzureKeyCredential
load_dotenv()
search_endpoint=os.getenv("SEARCH_ENDPOINT")
index_name=os.getenv("SEARCH_INDEX_NAME")
admin_key=os.getenv("SEARCH_ADMIN_KEY")
credential = AzureKeyCredential(str(admin_key))
search_client = SearchClient(endpoint=search_endpoint,
                      index_name=index_name,
                      credential=credential)
results =  search_client.search(query_type='semantic', semantic_configuration_name='my-semantic-config',
    search_text="what is the TestIMO 123", 
    select='Title,Likelihood', query_caption='extractive')

for result in results:
    print(result["@search.reranker_score"])
    print(result["Title"])
    print(f"Likelihood: {result['Likelihood']}")

    captions = result["@search.captions"]
    if captions:
        caption = captions[0]
        if caption.highlights:
            print(f"Caption: {caption.highlights}\n")
        else:
            print(f"Caption: {caption.text}\n")