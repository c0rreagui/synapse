
import os
import boto3
from botocore.client import Config

class S3Storage:
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        if "http" not in self.endpoint:
             self.endpoint = f"http://{self.endpoint}"
             
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "synapse_admin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "synapse_secret_key")
        self.bucket = "synapse-data"
        
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1' # Ignored by MinIO but required by boto3
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except:
            try:
                self.client.create_bucket(Bucket=self.bucket)
            except Exception as e:
                print(f"Failed to create bucket: {e}")

    def upload_file(self, file_path: str, object_name: str = None):
        if object_name is None:
            object_name = os.path.basename(file_path)
        try:
            self.client.upload_file(file_path, self.bucket, object_name)
            return f"{self.bucket}/{object_name}"
        except Exception as e:
            print(f"S3 Upload failed: {e}")
            raise e

    def download_file(self, object_name: str, dest_path: str):
        try:
            self.client.download_file(self.bucket, object_name, dest_path)
            return dest_path
        except Exception as e:
            print(f"S3 Download failed: {e}")
            raise e

s3_storage = S3Storage()
