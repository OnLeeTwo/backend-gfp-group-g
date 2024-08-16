import boto3
import os
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_DOMAINS = os.getenv("R2_DOMAINS")

class UploadService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        )
 
    
    def upload_file(self, file, filename):
        try:
            self.s3_client.upload_fileobj(
                file,
                R2_BUCKET_NAME,
                filename
            )
            file_url = f"{self.s3_client.meta.endpoint_url}/{self.bucket_name}/{filename}"
            return file_url
        except Exception as e:
            print(e)
            return False