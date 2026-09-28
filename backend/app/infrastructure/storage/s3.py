import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.infrastructure.storage.interface import StorageBackend


class S3Storage(StorageBackend):
    def __init__(self):
        settings = get_settings()
        self.bucket = settings.AWS_S3_BUCKET
        self.region = settings.AWS_REGION
        self.client = boto3.client(
            "s3",
            region_name=self.region,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    def upload(self, file_object, object_key: str, content_type: str | None = None) -> None:
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        try:
            self.client.upload_fileobj(file_object, self.bucket, object_key, ExtraArgs=extra_args)
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 upload failed: {str(e)}",
            )

    def download(self, object_key: str):
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=object_key)
            return response["Body"]
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"S3 object not found: {str(e)}",
            )

    def delete(self, object_key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=object_key)
        except ClientError:
            pass

    def exists(self, object_key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError:
            return False
