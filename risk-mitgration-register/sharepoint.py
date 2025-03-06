import requests
import os
import re
from dotenv import load_dotenv
load_dotenv()
class SharepointConnector:
    
    def __init__(self, client_id, client_secret, tenant_id, site_url, list_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.site_url = site_url
        self.list_url = list_url
        self.access_token = self.authenticate()  # Now we authenticate in the constructor

    def authenticate(self):
        token_url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token'
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()  # This will throw an error if the response isn't successful
        return response.json()['access_token']

    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def get_sharepoint_id(self):
        """Fetches SharePoint site ID from the provided site URL using Microsoft Graph API."""
        parts = self.site_url.split('/')
        hostname = parts[2]  # Hostname is typically at index 2 (e.g., 'contoso.sharepoint.com')
        site_path = '/'.join(parts[4:])  # Site path (e.g., 'sites/ExampleSite')

        graph_url = f'https://graph.microsoft.com/v1.0/sites/{hostname}:/sites/{site_path}'

        headers = self.get_headers()

        response = requests.get(graph_url, headers=headers)

        if response.status_code == 200:
            site_info = response.json()
            return site_info['id']
        else:
            print("Failed to retrieve site information:", response.text)
            return None
    
    def get_list_id_from_list_url(self, list_url, site_id):
        list_endpoint = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists"
        headers = self.get_headers()

        list_response = requests.get(list_endpoint, headers=headers)

        if list_response.status_code == 200:
            lists_data = list_response.json().get("value", [])
            for sp_list in lists_data:
                if sp_list.get("webUrl") == list_url:
                    return sp_list.get("id")
            return None
        else:
            raise Exception(
                status_code=list_response.status_code, 
                detail=f"Failed to retrieve lists information: {list_response.text}"
            )

    def sanitize_field_name(self, field_name):
        sanitized_name = re.sub(r'^[^a-zA-Z]+', '', field_name)  # Remove leading non-alphabetical characters
        sanitized_name = re.sub(r'[^a-zA-Z0-9_]', '_', sanitized_name)  # Replace invalid characters with underscores
        return sanitized_name

    def get_sharepoint_list_data(self, list_id, site_id):
        try:
            schema_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/columns"
            headers = self.get_headers()

            response = requests.get(schema_url, headers=headers)
            if response.status_code == 200:
                schema_data = response.json()
                fields_to_expand_and_index = [column["name"] for column in schema_data["value"]]

                select_fields = ','.join(fields_to_expand_and_index)
                url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items?expand=fields(select={select_fields})"
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if 'value' in data:
                        return data['value'], fields_to_expand_and_index
                    else:
                        print("No items found in the SharePoint list.")
                        return [], []
                else:
                    print(f"Failed to retrieve data from SharePoint list. Status code: {response.status_code}")
                    return [], []
            else:
                print(f"Failed to retrieve schema from SharePoint list. Status code: {response.status_code}")
                return [], []
        except Exception as e:
            print(f"Error fetching data from SharePoint list: {str(e)}")
            return [], []

if __name__ == "__main__":
    client_id = os.getenv("client_id")
    client_secret = os.getenv("client_secret")
    tenant_id = os.getenv("tenant_id")
    site_url = os.getenv("site_url")  
    list_url = os.getenv("list_urls")

    if not all([client_id, client_secret, tenant_id, site_url, list_url]):
        raise ValueError("Some environment variables are missing.")

    # Initialize SharePointConnector with required parameters
    sp_graph = SharepointConnector(client_id, client_secret, tenant_id, site_url, list_url)

    # Get site ID
    site_id = sp_graph.get_sharepoint_id()
    if site_id:
        print(f"Site ID: {site_id}")
        
        # Get list ID from list URL
        list_id = sp_graph.get_list_id_from_list_url(list_url, site_id)
        if list_id:
            print(f"List ID: {list_id}")
            
            # Fetch the data (fields and values)
            list_data, field_names = sp_graph.get_sharepoint_list_data(list_id, site_id)
            
            # If data is retrieved
            if list_data:
                print("Fields retrieved: ", field_names)
                for item in list_data:
                    print("Item Data:")
                    for field in field_names:
                        print(f"  {field}: {item['fields'].get(field, 'N/A')}")
            else:
                print("No data found in the list.")
        else:
            print("List not found.")
    else:
        print("Failed to retrieve Site ID.")