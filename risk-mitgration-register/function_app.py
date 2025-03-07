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
credential = AzureKeyCredential(str(SEARCH_ADMIN_KEY))

client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION"),
    azure_endpoint=os.getenv("azure_oepnai_endpoint"),
    api_key=os.getenv("azure_openai_key"),
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
              field_names=["Status","Level1","Level2","ContentType","Title","Level3","Likelihood","RiskId","RiskIssueStrategy","ProgramRisk","IsEsclated","TargetDate","Modified","Impact","FinancialImpact"]

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
    try:
        
        req_body = req.get_json()
        query = req_body.get("query")
 
        
        global cache
        past_questions = cache["past_questions"]
 
        if query not in past_questions:
            past_questions.append(query)
 
        if len(past_questions) > 5:
            past_questions.pop(0)
 
        if not isinstance(query, str):
            raise ValueError("Query must be a string")
 
       
        try:
            embedding = client.embeddings.create(input=query, model="text-embedding-ada-002").data[0].embedding
        except Exception as e:
            raise func.HttpResponse(f"Error in embedding creation: {e}", status_code=500)
 
       
        vector_query = VectorizedQuery(vector=embedding, k_nearest_neighbors=3, fields="contentVector", exhaustive=True)
        results = search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            select=["id", "status", "Level1"],
            top=3
        )
 
        result_data = []
        for result in results:
            result_data.append({
                "id": result["id"],
                "status": result["status"],
                "Level1": result["Level1"]
            })
 
        
        result_display = "\n".join([f"Id: {r['id']}, status: {r['status']}" for r in result_data])
 
        last_five_questions = "\n".join(past_questions)
 
        prompt = f'''
        You are a helpful assistant that responds to queries based on the context provided.
        
        CURRENT QUERY: {query}
        PAST QUESTIONS: {last_five_questions}
        QUERY TYPE: Hybrid Search
        CONTEXTUAL GUIDANCE:
        - This query is part of a hybrid search that combines both keyword-based and vector-based search methods.
        - You should consider the context of both the current query and past questions.
        - Provide a response that is not only accurate but also coherent with previous inquiries, ensuring consistency.
        - Offer suggestions or further elaboration where applicable, depending on the nature of the question.
        Based on the information above, craft a thoughtful response to the current query.
        '''
 

        
        max_prompt_length = 2048
        prompt = truncate_text(prompt, max_prompt_length)
 
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": prompt}]
            )
            output = response.choices[0].message.content
        except Exception as e:
            return func.HttpResponse(f"Error generating response: {e}", status_code=500)
 
        
        return func.HttpResponse(
            json.dumps({
               
                "search_results": result_display
            }),
            mimetype="application/json",
            status_code=200
        )

 
    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
