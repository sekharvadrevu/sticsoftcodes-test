from datetime import datetime
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes.models import (
    SimpleField, SearchableField, HnswAlgorithmConfiguration,
    VectorSearch, VectorSearchProfile, SearchField,
    SemanticConfiguration, SemanticPrioritizedFields,
    SemanticField, SemanticSearch
)
import logging
import re
class AzureIndex:
    def __init__(self, search_endpoint, search_admin_key, search_index_name):
        self.search_endpoint = search_endpoint
        self.search_admin_key = search_admin_key
        self.search_index_name = search_index_name
    def sanitize_field_name(self, field_name):
        sanitized_name = re.sub(r'^[^a-zA-Z]+', '', field_name)  
        sanitized_name = re.sub(r'[^a-zA-Z0-9_]', '_', sanitized_name)  
        return sanitized_name
    def get_field_type(self, field_value):
      
        if isinstance(field_value, str):
            return "Edm.String"
        elif isinstance(field_value, int):
            return "Edm.Int32"
        elif isinstance(field_value, float):
            return "Edm.Double"
        elif isinstance(field_value, bool):
            return "Edm.Boolean"
        elif isinstance(field_value, datetime):
            return "Edm.DateTimeOffset"
        else:
            return "Edm.String"
    # def create_azure_search_index(self, field_names):
    #         index_client = SearchIndexClient(endpoint=self.search_endpoint, credential=AzureKeyCredential(self.search_admin_key))

    #         fields = [
    #             SimpleField(name="id", type="Edm.String", key=True),
    #             SearchableField(name="Title",type="Edm.String",searchable=True),
    #             SearchableField(name="ContentType",type="Edm.String",searchable=True),
    #             SearchableField(name="Impact",type="Edm.String",searchable=True),
    #             SimpleField(name="FinancialImpact",type="Edm.Double"),
    #             SearchField(name="contentVector", type="Collection(Edm.Single)", searchable=True, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
    #             SearchableField(name="Likelihood",type="Edm.String",searchable=True),
    #             SearchableField(name="IsEsclated",type="Edm.String",searchable=True),
    #             SearchableField(name="TargetDate",type="Edm.DateTimeOffset"),
    #             SearchableField(name="Modified",type="Edm.DateTimeOffset"),
    #             SearchableField(name="RiskIssueStrategy",type="Edm.String",searchable=True),
    #             SearchableField(name="RiskIssueRaisedBy",type="Edm.String",searchable=True),
    #             SearchableField(name="Level1", type="Edm.String",searchable=True),
    #             SearchableField(name="Level2",type="Edm.String",searchable=True),
    #             SearchableField(name="Level3", type="Edm.String",searchable=True),
    #             SearchableField(name="status",type="Edm.String",searchable=True),
    #             SearchableField(name="RiskId",type="Edm.String",searchable=True),
    #             SearchableField(name="ProgramRisk",type="Edm.String",searchable=True)
    #             ] 
    #         vector_search = VectorSearch(
    #         algorithms=[HnswAlgorithmConfiguration(name="myHnsw")],
    #         profiles=[VectorSearchProfile(name="myHnswProfile", algorithm_configuration_name="myHnsw")])

    #         semantic_config = SemanticConfiguration(
    #         name="my-semantic-config",
    #         prioritized_fields=SemanticPrioritizedFields(content_fields=[SemanticField(field_name="Title")])
    #     )

    #         semantic_search = SemanticSearch(configurations=[semantic_config])
    #         for field in field_names:
    #             sanitized_field = self.sanitize_field_name(field)
                 
    #             field_type = "Edm.String" 
                
                
    #             if isinstance(field, (int, float)):
    #                 field_type = "Edm.Double"  
    #             elif isinstance(field, int):
    #                 field_type = "Edm.Int32"  

    #             # fields.append(SearchableField(name=sanitized_field, type=field_type,searchable=True))
                
    #         index = SearchIndex(
    #             name=self.search_index_name,
    #             fields=fields,
    #             vector_search=vector_search,
    #             semantic_search=semantic_search
                
    #         )

    #         try:
                
    #             existing_index = index_client.get_index(self.search_index_name)
    #             print(f"Index '{self.search_index_name}' already exists. Deleting the existing index...")
    #             index_client.delete_index(self.search_index_name)
    #             print(f"Index '{self.search_index_name}' has been deleted.")
    #         except Exception as e:
    #             print(f"Index '{self.search_index_name}' not found.")

    #         try:
    #             print(f"Creating index '{self.search_index_name}'...")
    #             index_client.create_index(index)
    #             print(f"Index '{self.search_index_name}' has been created successfully.")
    #         except Exception as e:
    #             print(f"Error creating index '{self.search_index_name}': {e}")
                
   
    
    # def upload_data_to_azure_search(self, data, embeddings, field_names):
    #     try:
           
    #         search_client = SearchClient(
    #             endpoint=self.search_endpoint,
    #             index_name=self.search_index_name,
    #             credential=AzureKeyCredential(self.search_admin_key)
    #         )
            
    #         documents = []
    #         for idx, item in enumerate(data):
               
    #             doc = {"id": str(item["id"])}  
                
                
    #             for field in field_names:
    #                 sanitized_field = self.sanitize_field_name(field)
    #                 field_value = item["fields"].get(field, "")
    #                 if field_value is None:
    #                  field_value = ""
                   
    #                 if isinstance(field_value, str):
    #                     doc[sanitized_field] = str(field_value)
    #                 elif isinstance(field_value, (int, float)):
    #                     doc[sanitized_field] = str(field_value)
    #                 else:
    #                     doc[sanitized_field] = str(field_value)
    #             financial_impact = item.get("FinancialImpact", 0.0)
    #             doc['FinancialImpact']=float(financial_impact)
    #             # target_date=item.get("TargetDate")
    #             # Modified=item.get("Modified")
    #             # if target_date:
    #             #     try:
    #             #         target_date = datetime.strptime(target_date, "%Y-%m-%dT%H:%M:%S.%fZ")  
    #             #         target_date = target_date.isoformat()  
    #             #         print("target_date",target_date)
    #             #     except ValueError:
    #             #         target_date = None  
    #             # if Modified:
    #             #     try:
    #             #         Modified = datetime.strptime(Modified, "%Y-%m-%dT%H:%M:%S.%fZ")  
    #             #         Modified = Modified.isoformat()  
    #             #     except ValueError:
    #             #         target_date = None  
    #             # doc['TargetDate'] = target_date
    #             # doc["Modified"]= Modified
    #             doc['contentVector'] = embeddings[idx]  

    #             documents.append(doc)

            
    #         if documents:
    #             result = search_client.upload_documents[documents]
    #             print(f"Uploaded {len(result)} documents to the index.")
    #         else:
    #            print("No documents to upload.")
                
    #     except Exception as e:
    #        print(f"Error uploading data to Azure Search: {str(e)}")
    
    def upload_data_to_azure_search(self, data, embeddings, field_names):
        try:
            # Create a SearchClient for uploading documents to the existing index
            search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=self.search_index_name,
                credential=AzureKeyCredential(self.search_admin_key)
            )

            documents = []
            for idx, item in enumerate(data):
                doc = {"id": str(item["id"])}  # Assuming "id" is unique for each document

                # Process the fields from the input data and sanitize field names
                for field in field_names:
                    sanitized_field = self.sanitize_field_name(field)
                    field_value = item["fields"].get(field, None)  # Get value or None if missing
                    
                    # Handle Edm.DateTimeOffset fields
                    if field_value is None or (isinstance(field_value, str) and field_value.strip() == ''):
                        # If the value is None or empty string, set it to None (which is handled as null in Azure Search)
                        if 'Date' in sanitized_field:  # Assumption: field names that contain 'Date' are of type Edm.DateTimeOffset
                            field_value = None

                    # Check for null values and replace with default values if necessary
                    if field_value is None:
                        # You can decide a default value based on field type
                        if isinstance(field_value, str):
                            field_value = ""  # Default for strings
                        elif isinstance(field_value, (int, float)):
                            field_value = 0.0  # Default for numeric fields (float)
                        elif isinstance(field_value, bool):
                            field_value = False  # Default for boolean fields
                        else:
                            field_value = ""  # Fallback for other types

                    # Ensure correct field type assignment
                    if isinstance(field_value, str):
                        doc[sanitized_field] = str(field_value)  # Assign string value
                    elif isinstance(field_value, bool):
                        # Convert boolean values to "True" or "False" if the field is Edm.String
                        doc[sanitized_field] = "True" if field_value else "False"
                    elif isinstance(field_value, (int, float)):
                        # Ensure numeric fields are floats (Edm.Double)
                        doc[sanitized_field] = float(field_value)  # Ensuring the value is treated as a float (Edm.Double)
                    elif isinstance(field_value, datetime):
                        # Convert datetime objects to ISO format (Edm.DateTimeOffset)
                        doc[sanitized_field] = field_value.isoformat()
                    elif field_value is None:
                        # Explicitly set None for fields that expect Edm.DateTimeOffset or other null-acceptable types
                        doc[sanitized_field] = None
                    else:
                        doc[sanitized_field] = str(field_value)  # Default to string if unsure

                # Handle embedding (assuming it's a valid vector)
                doc['contentVector'] = embeddings[idx] if embeddings else []

                documents.append(doc)

            # Upload documents if there are any
            if documents:
                result = search_client.upload_documents(documents)
                logging.info(f"Uploaded {len(result)} documents to the index.")
            else:
                logging.info("No documents to upload.")
                
        except Exception as e:
            logging.error(f"Error uploading data to Azure Search: {str(e)}")