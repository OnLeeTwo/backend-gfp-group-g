import boto3

class UploadService:
    def __init__(self, access_key_id, secret_access_key, endpoint_url, bucket_name):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )
        self.bucket_name = bucket_name

    
    def upload_file(self, file, filename):
        try:
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                filename
            )
            file_url = f"{self.s3_client.meta.endpoint_url}/{self.bucket_name}/{filename}"
            return file_url
        except Exception as e:
            print(e)
            return False