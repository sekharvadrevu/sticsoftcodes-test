import logging
import requests
import azure.functions as func
from datetime import datetime
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
import json
from azure.storage.blob import BlobServiceClient
 

sharepoint_site_url = "https://yoursharepointsite"
sharepoint_list_names = ["List1", "List2", "List3"] 
api_base_url = f"{sharepoint_site_url}/_api/web/lists/getbytitle"
 

search_service_name = "your-search-service-name"
search_api_key = "YOUR_SEARCH_API_KEY"
search_endpoint = f"https://{search_service_name}.search.windows.net"
search_index_name = "combined-index-name"  
 

blob_connection_string = "YOUR_BLOB_STORAGE_CONNECTION_STRING"
container_name = "your-container-name"
blob_name = "last-sync-times.json"  

def get_last_sync_times():
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)
    
    try:
        blob_data = blob_client.download_blob()
        last_sync_times = json.loads(blob_data.content_as_text())
        return last_sync_times
    except Exception as e:
        logging.error(f"Error retrieving last sync times: {e}")
        return {}
 

def update_last_sync_times(last_sync_times):
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)
    
    try:
        blob_client.upload_blob(json.dumps(last_sync_times), overwrite=True)
        logging.info(f"Last sync times updated.")
    except Exception as e:
        logging.error(f"Error updating last sync times: {e}")
 

def fetch_sharepoint_data(list_name, last_sync_time):
    api_url = f"{api_base_url}('{list_name}')/items?$filter=Modified ge {last_sync_time}"
    headers = {
        'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
        'Accept': 'application/json'
    }
 
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            return response.json().get('value', [])
        else:
            logging.error(f"Failed to fetch data for {list_name}. Status code: {response.status_code}")
            return []
    except Exception as e:
        logging.error(f"Error fetching data for {list_name}: {e}")
        return []
 

def upload_to_search_index(documents):
    search_client = SearchClient(endpoint=search_endpoint,
                                 index_name=search_index_name,
                                 credential=AzureKeyCredential(search_api_key))
    
    try:
        result = search_client.upload_documents(documents=documents)
        logging.info(f"Indexed {len(result)} documents to {search_index_name}.")
    except Exception as e:
        logging.error(f"Error uploading documents to {search_index_name}: {e}")
 
def main(mytimer: func.TimerRequest) -> None:
    
    logging.info(f"Function triggered at {datetime.now()}.")
 
    
    last_sync_times = get_last_sync_times()
 
   
    all_documents = []
    latest_sync_time = "2000-01-01T00:00:00Z"  
 
   
    for list_name in sharepoint_list_names:
        logging.info(f"Processing SharePoint list: {list_name}")
 
        
        list_last_sync_time = last_sync_times.get(list_name, "2000-01-01T00:00:00Z")
        logging.info(f"Last sync time for {list_name}: {list_last_sync_time}")
 
        
        items = fetch_sharepoint_data(list_name, list_last_sync_time)
 
        if items:
           
            for item in items:
                doc = {
                    'id': str(item['ID']),
                    'title': item.get('Title', ''),
                    'description': item.get('Description', ''),
                    'createdDate': item.get('Created', ''),
                    'modifiedDate': item.get('Modified', ''),
                    'listName': list_name 
                }
 
                
                item_modified_time = item.get('Modified', '')
                if item_modified_time > latest_sync_time:
                    latest_sync_time = item_modified_time
 
                
                all_documents.append(doc)
 
   
    if all_documents:
        upload_to_search_index(all_documents)
 
   
    for list_name in sharepoint_list_names:
        last_sync_times[list_name] = latest_sync_time
 
    
    update_last_sync_times(last_sync_times)
 
   
    if mytimer.past_due:
     logging.info(f"Timer is past due! Last run was at {datetime.now()}")
    else:
        logging.info(f"Function ran at {datetime.now()}")