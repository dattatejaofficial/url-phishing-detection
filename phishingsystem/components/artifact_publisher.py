import os
import sys
from dotenv import load_dotenv
load_dotenv()

from phishingsystem.logging.logger import logging
from phishingsystem.exception.exception import PhishingSystemException

from phishingsystem.entity.config_entity import ArtifactPublisherConfig

from azure.storage.blob import BlobServiceClient

AZURE_BLOB_ARTIFACT_CONTAINER = os.getenv('AZURE_BLOB_ARTIFACT_CONTAINER')
AZURE_ARTIFACT_STORAGE_CONNECTION_STRING = os.getenv('AZURE_ARTIFACT_STORAGE_CONNECTION_STRING')

if not AZURE_BLOB_ARTIFACT_CONTAINER or not AZURE_ARTIFACT_STORAGE_CONNECTION_STRING:
    raise Exception("Azure Blob config is not set")

class ArtifactPublisher:
    def __init__(self, artifact_publisher_config : ArtifactPublisherConfig):
        self.artifact_publisher_config = artifact_publisher_config
        self.blob_service_client = BlobServiceClient.from_connection_string(conn_str=AZURE_ARTIFACT_STORAGE_CONNECTION_STRING)
        self.container_client = self.blob_service_client.get_container_client(AZURE_BLOB_ARTIFACT_CONTAINER)
        
        if not self.container_client.exists():
            self.container_client.create_container()

    def initiate_artifact_publisher(self):
        try:
            artifact_dir = self.artifact_publisher_config.artifact_dir
            base_folder_name = os.path.basename(artifact_dir)

            for root, dirs, files in os.walk(artifact_dir):

                for file in files:
                    local_file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_file_path, artifact_dir)

                    blob_path = f'{base_folder_name}/{relative_path}'
                    blob_client = self.container_client.get_blob_client(blob_path)

                    with open(local_file_path, 'rb') as data:
                        blob_client.upload_blob(data)
            
            logging.info('Uploaded Artifacts into Blob')

        except Exception as e:
            raise PhishingSystemException(e,sys)