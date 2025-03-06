from datetime import datetime, timedelta, timezone
import requests
import os
import re
from dotenv import load_dotenv
load_dotenv()
class SharepointConnector:
    
    def __init__(self, client_id, client_secret, tenant_id, site_url, list_url,delta=False,delta_value=None,delta_type=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.site_url = site_url
        self.list_url = list_url
        self.access_token = self.authenticate()
        self.delta=delta
        self.delta_value=delta_value
        self.delta_type=delta_type

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
        hostname = parts[2]  
        site_path = '/'.join(parts[4:])  

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

   

    def get_sharepoint_list_data(self, list_id, site_id):
        try:
            schema_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/columns"
            headers = self.get_headers()

            response = requests.get(schema_url, headers=headers)
            if response.status_code == 200:
                schema_data = response.json()
                fields_to_expand_and_index = [column["name"] for column in schema_data["value"]]

                select_fields = ','.join(fields_to_expand_and_index)
                delta_value = self.delta_value.strip()
                try:
                    delta_value = float(self.delta_value)  # Now it's safe to handle decimal values
                except ValueError:
                    raise ValueError(f"Invalid DELTA value: {delta_value}. Must be a valid number.")
                if self.delta_type == 'weeks':
                    delta_time = timedelta(weeks=delta_value)
                elif self.delta_type == 'days':
                    delta_time = timedelta(days=delta_value)
                elif self.delta_type == 'hours':
                    delta_time = timedelta(hours=delta_value)
                elif self.delta_type == 'minutes':
                    delta_time = timedelta(minutes=delta_value)
                else:
                    raise ValueError("Invalid DELTA_TYPE. Must be 'weeks', 'days', 'hours', or 'minutes'.")

                now = datetime.now(timezone.utc)
                delta_time = now - delta_time
                formatted_time = delta_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                if self.delta == True:
                     filter_query = f'{formatted_time}'
                     url= f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items/delta?token='{filter_query}'&$expand=fields($select={select_fields})"
                else:
                    
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
