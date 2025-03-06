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
class AzureIndex:
    
    def create_azure_search_index(self, field_names):
            index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=AzureKeyCredential(SEARCH_ADMIN_KEY))

            # Create fields dynamically based on SharePoint list fields
            fields = [SimpleField(name="id", type="Edm.String", key=True)]  # Add a primary key field

            for field in field_names:
                sanitized_field = self.sanitize_field_name(field)
                
                # Here, we can add logic to determine the correct type (e.g., Edm.Double for numbers)
                field_type = "Edm.String"  # Default to Edm.String
                
                # Check if the field is numeric in nature
                if isinstance(field, (int, float)):
                    field_type = "Edm.Double"  # Change to Edm.Double for numeric fields
                elif isinstance(field, int):
                    field_type = "Edm.Int32"  # Change to Edm.Int32 if integer

                fields.append(SimpleField(name=sanitized_field, type=field_type))
                
            index = SearchIndex(
                name=SEARCH_INDEX_NAME,
                fields=fields
            )

            try:
                # Check if the index exists
                existing_index = index_client.get_index(SEARCH_INDEX_NAME)
                print(f"Index '{SEARCH_INDEX_NAME}' already exists. Deleting the existing index...")
                index_client.delete_index(SEARCH_INDEX_NAME)
                print(f"Index '{SEARCH_INDEX_NAME}' has been deleted.")
            except Exception as e:
                print(f"Index '{SEARCH_INDEX_NAME}' not found.")

            try:
                print(f"Creating index '{SEARCH_INDEX_NAME}'...")
                index_client.create_index(index)
                print(f"Index '{SEARCH_INDEX_NAME}' has been created successfully.")
            except Exception as e:
                print(f"Error creating index '{SEARCH_INDEX_NAME}': {e}")
    def upload_data_to_azure_search(self, data, field_names):
                try:
                    search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=SEARCH_INDEX_NAME, credential=AzureKeyCredential(SEARCH_ADMIN_KEY))
                    
                    # Prepare data to be uploaded
                    documents = []
                    for item in data:
                        doc = {"id": str(item["id"])}  # Ensure ID is a string
                        for field in field_names:
                            sanitized_field = self.sanitize_field_name(field)
                            # Get the field value
                            field_value = item["fields"].get(field, "N/A")
                            
                            # Handle data type conversions
                            if isinstance(field_value, str):
                                doc[sanitized_field] = str(field_value)
                            elif isinstance(field_value, (int, float)):
                                doc[sanitized_field] = str(field_value)
                            else:
                                doc[sanitized_field] = str(field_value)  # Convert other types to string

                        documents.append(doc)

                    # Upload data to the Azure Search index
                    if documents:
                        result = search_client.upload_documents(documents)
                        print(f"Uploaded {len(result)} documents to the index.")
                except Exception as e:
                    print(f"Error uploading data to Azure Search: {str(e)}")

