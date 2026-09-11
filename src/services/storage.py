import os
import logging
from io import BytesIO
import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)

class MinioStorage:
    def __init__(
        self,
        endpoint_url: str = None,
        access_key: str = None,
        secret_key: str = None,
    ):
        """
        Khởi tạo kết nối S3 Client làm việc với MinIO.
        Cấu hình ưu tiên tham số truyền vào, nếu không có sẽ lấy từ biến môi trường.
        """
        self.endpoint_url = endpoint_url or os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        self.access_key = access_key or os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = secret_key or os.getenv("MINIO_SECRET_KEY", "minioadmin")

        try:
            self.client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name="us-east-1", # MinIO không bắt buộc nhưng boto3 yêu cầu region
            )
            logger.info(f"Khởi tạo MinIO S3 client thành công tới {self.endpoint_url}")
        except Exception as e:
            logger.error(f"Lỗi khởi tạo MinIO client: {e}")
            raise e

    def upload_file(self, bucket_name: str, file_path: str, object_name: str = None) -> bool:
        """
        Upload một file từ máy local lên MinIO bucket.
        """
        if not os.path.exists(file_path):
            logger.error(f"File không tồn tại tại đường dẫn: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        if object_name is None:
            object_name = os.path.basename(file_path)

        try:
            # Đảm bảo bucket tồn tại trước khi upload
            self._ensure_bucket_exists(bucket_name)

            self.client.upload_file(file_path, bucket_name, object_name)
            logger.info(f"Upload thành công '{file_path}' lên bucket '{bucket_name}' với tên key '{object_name}'")
            return True
        except ClientError as e:
            logger.error(f"Lỗi S3 Client khi upload file '{object_name}': {e}")
            return False
        except BotoCoreError as e:
            logger.error(f"Lỗi BotoCore SDK khi upload file '{object_name}': {e}")
            return False
        except Exception as e:
            logger.error(f"Lỗi không xác định khi upload: {e}")
            return False

    def get_file_stream(self, bucket_name: str, object_name: str) -> BytesIO:
        """
        Tải file từ MinIO về dưới dạng luồng dữ liệu BytesIO (Memory Stream).
        Giúp đọc file trực tiếp trong bộ nhớ mà không cần lưu xuống đĩa cứng.
        """
        try:
            response = self.client.get_object(Bucket=bucket_name, Key=object_name)
            file_stream = BytesIO(response["Body"].read())
            file_stream.seek(0)
            logger.info(f"Lấy stream thành công cho object '{object_name}' từ bucket '{bucket_name}'")
            return file_stream
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                logger.error(f"Object '{object_name}' không tồn tại trong bucket '{bucket_name}'")
            else:
                logger.error(f"Lỗi S3 Client khi đọc file '{object_name}': {e}")
            raise e
        except Exception as e:
            logger.error(f"Lỗi khi đọc file stream: {e}")
            raise e

    def _ensure_bucket_exists(self, bucket_name: str):
        """
        Hàm phụ trợ: Kiểm tra nếu Bucket chưa có thì tự động tạo mới.
        """
        try:
            self.client.head_bucket(Bucket=bucket_name)
        except ClientError:
            logger.info(f"Bucket '{bucket_name}' chưa tồn tại. Đang tiến hành tạo mới...")
            self.client.create_bucket(Bucket=bucket_name)
