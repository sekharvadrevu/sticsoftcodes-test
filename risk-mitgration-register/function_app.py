import azure.functions as func
import datetime
import json
import logging
import os
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from azure_index import AzureIndex
from embeddings import GetEmbeddings
from sharepoint import SharepointConnector
app = func.FunctionApp()
client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")
tenant_id = os.getenv("tenant_id")
site_url = os.getenv('site_url') 
list_url = os.getenv('list_urls')  
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_ADMIN_KEY = os.getenv("SEARCH_ADMIN_KEY")
SEARCH_INDEX_NAME = os.getenv("SEARCH_INDEX_NAME")

@app.route(route="create-index", auth_level=func.AuthLevel.FUNCTION)
def create_index_func(req:func.HttpRequest)->func.HttpResponse:
    logging.info("create index triggered has been started")
    delta = req.params.get('delta', 'false').lower() == 'true'  
    delta_value = req.params.get('delta_value', '1')  
    delta_type = req.params.get('delta_type', 'days') 
    sharepoint_site_details=SharepointConnector(client_id, client_secret, tenant_id, site_url, list_url,delta,delta_value,delta_type)
    site_id=sharepoint_site_details.get_sharepoint_id()
    if site_id:
          logging.info(f"Site ID: {site_id}")
          list_id = sharepoint_site_details.get_list_id_from_list_url(list_url, site_id)
          if list_id:
              logging.info(f"List ID: {list_id}")
              list_data,field_names = sharepoint_site_details.get_sharepoint_list_data(list_id, site_id)
              field_names=["Status","Level1","Level2","ContentType","Title","Level3","Likelihood","RiskIssueStrategy","ProgramRisk","IsEsclated","TargetDate","Modified"]

              embedding_generator = GetEmbeddings()

              embeddings = []
              for item in list_data:
                    field_value = item.get("fields", {}).get("Status")  
                    print(field_value)
                    if field_value:
                        embedding = embedding_generator.generate_embeddings(field_value)
                        embeddings.append(embedding)
                    else:
                        embeddings.append([])
              if list_data:
                   azure_search = AzureIndex(SEARCH_ENDPOINT,SEARCH_ADMIN_KEY,SEARCH_INDEX_NAME)
                   azure_search.create_azure_search_index(field_names)
                   azure_search.upload_data_to_azure_search(list_data, embeddings,field_names)
                   return func.HttpResponse("Data indexed successfully!", status_code=200)
              else:
                    return func.HttpResponse("No data found in the SharePoint list.", status_code=404)
                  
          else:
                return func.HttpResponse("List not found.", status_code=404)    
@app.route(route="MyHttpTrigger", auth_level=func.AuthLevel.FUNCTION)
def MyHttpTrigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
        
@app.route(route="ragchatbot", auth_level=func.AuthLevel.FUNCTION)
def rag_chatbot(req: func.HttpRequest)->func.HttpResponse:
    req_body = req.get_json()
    query = req_body.get('query')
    azure_search = AzureIndex(SEARCH_ENDPOINT,SEARCH_ADMIN_KEY,SEARCH_INDEX_NAME)
    vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=1, fields="contentVector", exhaustive=True)
    results = azure_search.search(search_text=None,vector_queries= [vector_query],top=1)  
