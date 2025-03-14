import azure.functions as func
import datetime
import json
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
import logging
import os
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from azure_index import AzureIndex
from embeddings import GetEmbeddings

from azure.storage.blob import BlobServiceClient
from sharepoint import SharepointConnector
app = func.FunctionApp()
client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")
tenant_id = os.getenv("tenant_id")
site_url = os.getenv('site_url') 
list_urls = json.loads(os.getenv("list_urls"))
BLOB_CONNECTION_STRING=os.getenv("connectionstring")
BLOB_CONTAINER_NAME=os.getenv("BLOB_CONTAINER_NAME")
list_url=os.getenv("list_url")
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_ADMIN_KEY = os.getenv("SEARCH_ADMIN_KEY")
SEARCH_INDEX_NAME = os.getenv("SEARCH_INDEX_NAME")
credential = AzureKeyCredential(str(SEARCH_ADMIN_KEY))
azure_endpoint=os.getenv("azure_oepnai_endpoint")
azure_openai_key=os.getenv("azure_openai_key")
api_verison=os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION")
BLOB_CONNECTION_STRING = os.getenv("connectionstring")
BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")
blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
client = AzureOpenAI(
    api_version=api_verison,
    azure_endpoint=azure_endpoint,
    api_key=azure_openai_key,
)
search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=SEARCH_INDEX_NAME, credential=credential)

# In-memory cache to store past questions
cache = {
    "past_questions": []
}
 
def truncate_text(text, max_length):
    """Truncate text to ensure it doesn't exceed the max_length."""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text
 
# @app.function_name(name="mytimer")
# @app.timer_trigger(schedule="0 */5 * * * *", 
#               arg_name="mytimer",
#               run_on_startup=True) 
# def test_function(mytimer: func.TimerRequest) -> None:
#     utc_timestamp = datetime.datetime.utcnow().replace(
#         tzinfo=datetime.timezone.utc).isoformat()
#     if mytimer.past_due:
#         logging.info('The timer is past due!')
#         print("Past due date",utc_timestamp)
#     logging.info('Python timer trigger function ran at %s', utc_timestamp)
#     logging.info(f"Function triggered at {datetime.datetime.now()}")
    
    
def index_data_in_search(combined_data_json):
    """Function to index combined data into Azure Cognitive Search."""
    try:
        
        all_combined_data = json.loads(combined_data_json)
        
        
        search_client = SearchClient(endpoint=SEARCH_ENDPOINT,
                                     index_name=SEARCH_INDEX_NAME,
                                     credential=AzureKeyCredential(SEARCH_ADMIN_KEY))
        
        
        documents = []
        for list_data, embeddings, field_names in all_combined_data:
            for item in list_data:
                document = {
                    "id": item.get("Id"),  
                    "Title": item.get("fields", {}).get("Title"),
                    "Status": item.get("fields", {}).get("Status"),
                   
                }
                documents.append(document)
        
        
        if documents:
            result = search_client.upload_documents(documents=documents)
            logging.info(f"Successfully uploaded {len(documents)} documents to Azure Search.")
        else:
            logging.warning("No documents to upload to Azure Search.")
    except Exception as e:
        logging.error(f"Error indexing data in Azure Cognitive Search: {str(e)}")

# @app.route(route="create-index", auth_level=func.AuthLevel.FUNCTION)
# def create_index_func(req: func.HttpRequest) -> func.HttpResponse:
#     logging.info("Upload data triggered")
#     delta = req.params.get('delta', 'false').lower() == 'true'  
#     delta_value = req.params.get('delta_value', '1')  
#     delta_type = req.params.get('delta_type', 'days') 
#     sharepoint_site_details = SharepointConnector(client_id, client_secret, tenant_id, site_url, list_url, delta, delta_value, delta_type)
#     site_id = sharepoint_site_details.get_sharepoint_id()
    
#     if site_id:
#         logging.info(f"Site ID: {site_id}")
#         list_id = sharepoint_site_details.get_list_id_from_list_url(list_url, site_id)
        
#         if list_id:
#             logging.info(f"List ID: {list_id}")
#             list_data, field_names = sharepoint_site_details.get_sharepoint_list_data(list_id, site_id)
#             field_names = ["Status", "Level1", "Level2", "ContentType", "Title", "Level3", "Likelihood", "RiskId", "RiskIssueStrategy", "RiskIssueRaisedBy", "ProgramRisk", "IsEsclated", "TargetDate", "Modified", "Impact", "FinancialImpact"]

#             embedding_generator = GetEmbeddings()
#             embeddings = []

#             for item in list_data:
#                 field_value = item.get("fields", {}).get("Status")
#                 print(field_value)
#                 if field_value:
#                     embedding = embedding_generator.generate_embeddings(field_value)
#                     embeddings.append(embedding)
#                 else:
#                     embeddings.append([])

#             if list_data:
#                 azure_search = AzureIndex(SEARCH_ENDPOINT, SEARCH_ADMIN_KEY, SEARCH_INDEX_NAME)
#                 azure_search.upload_data_to_azure_search(list_data, embeddings, field_names)
#                 return func.HttpResponse("Data indexed successfully!", status_code=200)
#             else:
#                 return func.HttpResponse("No new or modified data found in the SharePoint list.", status_code=404)
        
#         else:
#             return func.HttpResponse("List not found.", status_code=404)
#     else:
#         return func.HttpResponse("Site not found.", status_code=404) 
field_names = ["Status", "Level1", "Level2", "ContentType", "ResponseDate", "ResponsePlan", "Title", "Level3", "Likelihood", "ResponseOwner", "RiskId", "RiskIssueStrategy", "RiskIssueRaisedBy", "ProgramRisk", "IsEsclated", "TargetDate", "Modified", "Impact", "FinancialImpact","RiskIssueDescription", "Created", "RevisedResponseDate", "RiskIssueID"]
def clean_data(item):
    """
    Function to clean data by keeping only the desired fields and replacing null or empty values with an empty string.
    """
    cleaned_item = {}
    for field in field_names:
        value = item.get("fields", {}).get(field)
        if value is None or value == "":
            cleaned_item[field] = ""
        else:
            cleaned_item[field] = value
    return cleaned_item

@app.route(route="create-index", auth_level=func.AuthLevel.FUNCTION)
def create_index_func(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Upload data triggered")
    
    delta = req.params.get('delta', 'false').lower() == 'true'
    delta_value = req.params.get('delta_value', '1')
    delta_type = req.params.get('delta_type', 'days')
    
    
    sharepoint_site_details = SharepointConnector(client_id, client_secret, tenant_id, site_url, list_urls, delta, delta_value, delta_type)
    site_id = sharepoint_site_details.get_sharepoint_id()
    
    if site_id:
        logging.info(f"Site ID: {site_id}")

       
       
        all_embeddings = []

        for list_url in list_urls:
            list_id = sharepoint_site_details.get_list_id_from_list_url(list_url, site_id)
            
            if list_id:
                logging.info(f"Processing List ID: {list_id} for List URL: {list_url}")
                list_data, field_names = sharepoint_site_details.get_sharepoint_list_data(list_id, site_id)
                field_names = ["Status", "Level1", "Level2", "ContentType", "ResponseDate", "ResponsePlan", "Title", "Level3", "Likelihood", "ResponseOwner", "RiskId", "RiskIssueStrategy", "RiskIssueRaisedBy", "ProgramRisk", "IsEsclated", "TargetDate", "Modified", "Impact", "FinancialImpact","RiskIssueDescription", "Created", "RevisedResponseDate", "RiskIssueID"]
                

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

               
                all_embeddings.append((list_data, embeddings, field_names))
            else:
                logging.error(f"List not found for URL: {list_url}")
        
      
        if all_embeddings:
            azure_search = AzureIndex(SEARCH_ENDPOINT, SEARCH_ADMIN_KEY, SEARCH_INDEX_NAME)
            for list_data, embeddings, field_names in all_embeddings:
                azure_search.upload_data_to_azure_search(list_data, embeddings, field_names)
            
            return func.HttpResponse("All lists indexed successfully!", status_code=200)
        else:
            return func.HttpResponse("No new or modified data found in the SharePoint lists.", status_code=404)
    else:
        return func.HttpResponse("Site not found.", status_code=404)
 
@app.route(route="create-index-function", auth_level=func.AuthLevel.FUNCTION)
def create_index_function(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Upload data triggered")
    
    delta = req.params.get('delta', 'false').lower() == 'true'
    delta_value = req.params.get('delta_value', '1')
    delta_type = req.params.get('delta_type', 'days')

    sharepoint_site_details = SharepointConnector(client_id, client_secret, tenant_id, site_url, list_urls, delta, delta_value, delta_type)
    site_id = sharepoint_site_details.get_sharepoint_id()
    
    if not site_id:
        return func.HttpResponse("Site not found.", status_code=404)
    
    logging.info(f"Site ID: {site_id}")

    embedding_generator = GetEmbeddings()
    
    all_embeddings = []

    for list_url in list_urls:
        list_id = sharepoint_site_details.get_list_id_from_list_url(list_url, site_id)
        
        if not list_id:
            logging.error(f"List not found for URL: {list_url}")
            continue
        
        logging.info(f"Processing List ID: {list_id} for List URL: {list_url}")
        list_data, field_names = sharepoint_site_details.get_sharepoint_list_data(list_id, site_id)
        
        cleaned_list_data = [clean_data(item) for item in list_data]
        combined_data = json.dumps(cleaned_list_data)
        
        blob_name = "register-mitagations.json" 
        blob_client = container_client.get_blob_client(blob_name)
        
        try:
            blob_client.upload_blob(combined_data, overwrite=True)
            logging.info(f"Data uploaded to Azure Blob Storage: {blob_name}")
        except Exception as e:
            logging.error(f"Failed to upload to Azure Blob Storage: {e}")
            return func.HttpResponse(f"Failed to upload to Azure Blob Storage: {e}", status_code=500)
        embedding_generator = GetEmbeddings()
        embeddings = []
        for item in cleaned_list_data:
                    field_value = item.get("fields", {}).get("Status")
                    print(field_value)
                    if field_value:
                        embedding = embedding_generator.generate_embeddings(field_value)
                        embeddings.append(embedding)
                    else:
                        embeddings.append([])

               
        all_embeddings.append((list_data, embeddings, field_names))
          
        
      
        # for item in cleaned_list_data:
        #     search_document = {"id": str(item.get("id", ""))}
        #     field_value = item.get("Status", "")
        #     content_embedding = embedding_generator.generate_embeddings(field_value) if field_value else []

            
        #     if content_embedding:
        #         search_document["contentVector"] = content_embedding  d
        #     else:
        #         search_document["contentVector"] = []  

        #     for field, value in item.items():
        #         if field != "Status":  # Exclude the embedding field itself
        #             # If the value is boolean, convert it to string
        #             if isinstance(value, bool):
        #                 search_document[field] = "True" if value else "False"
        #             else:
        #                 search_document[field] = value

        #     all_embeddings.append(search_document)
    
    if not all_embeddings:
        return func.HttpResponse("No new or modified data found in the SharePoint lists.", status_code=404)
    if all_embeddings:
            azure_search = AzureIndex(SEARCH_ENDPOINT, SEARCH_ADMIN_KEY, SEARCH_INDEX_NAME)
            for list_data, embeddings, field_names in all_embeddings:
                azure_search.upload_data_to_azure_search(list_data, embeddings, field_names)
            
            return func.HttpResponse("All lists indexed successfully!", status_code=200)
    else:
            return func.HttpResponse("No new or modified data found in the SharePoint lists.", status_code=404)
    
    
    # try:
    #     result = search_client.upload_documents(documents=all_embeddings)
    #     logging.info(f"Uploaded {len(all_embeddings)} documents to the index.")
    #     return func.HttpResponse("All lists indexed successfully!", status_code=200)

    # except Exception as e:
    #     logging.error(f"Error uploading to Azure Search: {e}")
    #     return func.HttpResponse(f"Failed to upload data to Azure Search: {e}", status_code=500)



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



# @app.route(route="ragchatbot", auth_level=func.AuthLevel.FUNCTION)
# def ragchabot(req: func.HttpRequest) -> func.HttpResponse:
#     try:
       
#         req_body = req.get_json()
#         user_query=req_body["query"] 
       
#         global cache
#         past_questions = cache["past_questions"]
#         if user_query not in past_questions:
#             past_questions.append(user_query)
#         if len(past_questions) > 5:
#             past_questions.pop(0)
 
#         if not isinstance(user_query, str):
#             raise ValueError("Query must be a string")
 
    
#         try:
#             embedding = client.embeddings.create(input=user_query, model="text-embedding-ada-002").data[0].embedding
#         except Exception as e:
#             raise func.HttpResponse(f"Error in embedding creation: {e}", status_code=500)
 
#         vector_query = VectorizedQuery(vector=embedding, k_nearest_neighbors=3, fields="contentVector", exhaustive=True)
#         results = search_client.search(
#             search_text=user_query,
#             vector_queries=[vector_query],
#             select=["id", "status"],
#             top=3
#         )
 
        
#         result_output = []
#         for result in results:
#             result_output.append({
#                 "Id": result["id"],
#                 "status": result["status"]
#             })
 
#         # Convert result to string to display
#         result_display = "\n".join([f"Id: {r['Id']}, status: {r['status']}" for r in result_output])
 
#         last_five_questions = "\n".join(past_questions)
        
#         try:
#             azure_client=client.chat.completions.create(
#               model="gpt-4o",
#               messages=[{"role":"system" ,"content":"Fetching the information from the sharepoint list based on keywords and giving relevant data"},
#                        {"role":"user","content":user_query}], max_tokens=600,temperature=1)
#             user_update=azure_client.choices[0].message.content.strip() 
                          
          
#         except Exception as e:
#             return func.HttpResponse(f"Error generating response: {e}", status_code=500)
        
#         try:
#             results = search_client.search(search_text=user_update, top=5)
#             responselist=[]
#             select_fields=["Title","Likelihood","Level1","status"]
#             for result in results:
#                     responseutils=[]
#                     for field in select_fields:
#                      if field in result and isinstance(result[field], str) and result[field].strip():
#                         responseutils.append(f"{field.capitalize()}: {result[field].strip()}")
#                     if responseutils:
#                         responselist.append("\n".join(responseutils))
#             responselist = " ".join(responselist)
#         except Exception as e:
#             logging.error(f"Error get the revelant information search results: {str(e)}")
            
    
#         try:
#             azure_client = client.chat.completions.create(
#                 model="gpt-4o",
#                 messages=[
#                     {"role": "system", "content": responselist},
#                     {"role": "user", "content": user_query}
#                 ],
#                 max_tokens=800,
#                 temperature=1
#             )
#             response = azure_client.choices[0].message.content
#         except Exception as e:
#             print("Error response",str(e))
#             response = "we are not able not generate response from api"

        
       

#         return func.HttpResponse(
#             json.dumps(response),
#             mimetype="application/json",
#             status_code=200
#         )

#     except Exception as e:
#         logging.error(f"Error occurred: {str(e)}")
#         return func.HttpResponse("An error occurred while processing your request.", status_code=500)
    
        
@app.route(route="ragchatbot", auth_level=func.AuthLevel.FUNCTION)
def rag_chat_bot_session(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing request in Azure Function.')

    
    req_body = req.get_json()
    user_query=req_body["query"] 
    if not user_query:
        return func.HttpResponse("Please pass a query on the query string", status_code=400)

    
    Prompt = """
    You are an AI assistant that helps users learn from the information found in the source material.
    Fetching the information from the SharePoint list based on keywords and giving relevant data.

    Query: {query}
    Sources:\n{sources}
    """
    
    try:
        
        embedding = client.embeddings.create(input=[user_query], model="text-embedding-ada-002").data[0].embedding
    except Exception as e:
        logging.error(f"Error in embedding creation: {e}")
        return func.HttpResponse("Error in embedding creation", status_code=500)
    
    
    vector_query = VectorizedQuery(vector=embedding, k_nearest_neighbors=3, fields="contentVector", exhaustive=True)

    
    try:
        search_results = search_client.search(
            search_text=user_query,
            vector_queries=[vector_query],
            select=["Title", "id", "Status"],
            top=5,
        )
    except Exception as e:
        logging.error(f"Error during search query execution: {e}")
        return func.HttpResponse("Error during search query execution", status_code=500)

    
    sources_formatted = "=================\n".join(
        [f'TITLE: {document["Title"]}, id: {document["id"]}, status: {document["Status"]}' for document in search_results]
    )

    
    try:
        response = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": Prompt.format(query=user_query, sources=sources_formatted)
            }],
            model="gpt-4o",
            temperature=1,
            
        )
        response=response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error generating response from the model: {e}")
        return func.HttpResponse("Error generating response", status_code=500)

    
    return func.HttpResponse(
        json.dumps({"response": response}),  
        mimetype="application/json",
        status_code=200
    )
    

 
            
    
    
# semantic query 
         
# @app.route(route="ragchatbot2", auth_level=func.AuthLevel.FUNCTION)
# def rag_chat_bot_session1(req: func.HttpRequest) -> func.HttpResponse:
#     logging.info('Processing request in Azure Function.')

    
#     req_body = req.get_json()
#     user_query=req_body["query"] 
#     if not user_query:
#         return func.HttpResponse("Please pass a query on the query string", status_code=400)

    
#     GROUNDED_PROMPT = """
#     You are an AI assistant that helps users learn from the information found in the source material.
#     Fetching the information from the SharePoint list based on keywords and giving relevant data.

#     Query: {query}
#     Sources:\n{sources}
#     """
    
#     # try:
        
#     #     embedding = client.embeddings.create(input=[user_query], model="text-embedding-ada-002").data[0].embedding
#     # except Exception as e:
#     #     logging.error(f"Error in embedding creation: {e}")
#     #     return func.HttpResponse("Error in embedding creation", status_code=500)
    
    
#     # vector_query = VectorizedQuery(vector=embedding, k_nearest_neighbors=3, fields="contentVector", exhaustive=True)

    
#     try:
#         search_results = search_client.search(
#             search_text=user_query,
#             query_type="semantic",
#             select=["Title", "id", "status"],
#             top=5,
#         )
#     except Exception as e:
#         logging.error(f"Error during search query execution: {e}")
#         return func.HttpResponse("Error during search query execution", status_code=500)

    
#     sources_formatted = "=================\n".join(
#         [f'TITLE: {document["Title"]}, id: {document["id"]}, status: {document["status"]}' for document in search_results]
#     )

    
#     try:
#         response = client.chat.completions.create(
#             messages=[{
#                 "role": "user",
#                 "content": GROUNDED_PROMPT.format(query=user_query, sources=sources_formatted)
#             }],
#             model="gpt-4o",
#             temperature=1,
#             top_p=5
#         )
#         response=response.choices[0].message.content
#     except Exception as e:
#         logging.error(f"Error generating response from the model: {e}")
#         return func.HttpResponse("Error generating response", status_code=500)

    
#     return func.HttpResponse(
#                 json.dumps(response),
#                 mimetype="application/json",
#                 status_code=200
#             )
    

 
            
    
    

 