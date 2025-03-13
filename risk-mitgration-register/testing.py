import logging
import json
import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import azure.functions as func
from sharepoint import SharepointConnector

# Load environment variables
load_dotenv()

# Retrieve environment variables
BLOB_CONNECTION_STRING = os.getenv("connectionstring")
BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")
client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")
tenant_id = os.getenv("tenant_id")
site_url = os.getenv('site_url') 
list_urls = json.loads(os.getenv("list_urls"))


delta = False
delta_value = '1'
delta_type = 'days'


sharepoint_site_details = SharepointConnector(client_id, client_secret, tenant_id, site_url, list_urls, delta, delta_value, delta_type)


site_id = sharepoint_site_details.get_sharepoint_id()


desired_field_names = [
    "Status", "Level1", "Level2", "ContentType", "ResponseDate", "ResponsePlan", 
    "Title", "Level3", "Likelihood", "ResponseOwner", "RiskId", "RiskIssueStrategy", 
    "RiskIssueRaisedBy", "ProgramRisk", "IsEsclated", "TargetDate", "Modified", "Impact", "FinancialImpact",
    "RiskIssueDescription", "Created", "RevisedResponseDate", "RiskIssueID"
]

def clean_data(item):
    """
    Function to clean data by keeping only the desired fields and replacing null or empty values with an empty string.
    """
    cleaned_item = {}
    for field in desired_field_names:
        value = item.get("fields", {}).get(field)
        if value is None or value == "":
            cleaned_item[field] = ""
        else:
            cleaned_item[field] = value
    return cleaned_item

if site_id:
    logging.info(f"Site ID: {site_id}")

    combined_data = [] 
    
    
    for list_url in list_urls:
        list_id = sharepoint_site_details.get_list_id_from_list_url(list_url, site_id)
        
        if list_id:
            logging.info(f"Processing List ID: {list_id} for List URL: {list_url}")
            list_data, field_names = sharepoint_site_details.get_sharepoint_list_data(list_id, site_id)

            # Clean each list's data
            cleaned_list_data = [clean_data(item) for item in list_data]

           
            combined_data.extend(cleaned_list_data)  
        else:
            logging.error(f"List not found for URL: {list_url}")

  
    if combined_data:
        
        blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)

        
        combined_data_json = json.dumps(combined_data)

       
        blob_name = "register-mitagations.json"

      
        blob_client = container_client.get_blob_client(blob_name)
        
        try:
            
            blob_client.upload_blob(combined_data_json, overwrite=True)
            logging.info(f"Combined SharePoint data successfully uploaded to Azure Blob Storage: {blob_name}")
            print(f"Azure blob storage successfully done: {blob_name}")
        except Exception as e:
            logging.error(f"Failed to upload to Azure Blob Storage: {e}")
            print(f"Error: {e}")
    else:
        logging.warning("No SharePoint data found to upload.")
        print("No SharePoint data found to upload.")
else:
    logging.error("No SharePoint site found.")
    print("No SharePoint site found.")
