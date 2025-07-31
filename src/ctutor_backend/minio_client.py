import os
from typing import Optional
from minio import Minio
from minio.error import S3Error
import logging

logger = logging.getLogger(__name__)


def transform_localhost_url(url: str) -> str:
    """
    Transform localhost URLs to Docker service name for container-to-container communication.
    
    Args:
        url: URL that may contain localhost
        
    Returns:
        URL with localhost replaced by minio service name
    """
    # In Docker environment, replace localhost with the MinIO service name
    if url and "localhost" in url:
        # Check if we're running in Docker by looking for common Docker environment variables
        if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER'):
            return url.replace("localhost", "minio")
    return url


# Environment configuration
MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'localhost:9000')
MINIO_ENDPOINT = transform_localhost_url(MINIO_ENDPOINT)  # Transform for Docker
MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')
MINIO_SECURE = os.environ.get('MINIO_SECURE', 'false').lower() == 'true'
MINIO_REGION = os.environ.get('MINIO_REGION', 'us-east-1')
MINIO_DEFAULT_BUCKET = os.environ.get('MINIO_DEFAULT_BUCKET', 'computor-storage')

_minio_client: Optional[Minio] = None


def get_minio_client() -> Minio:
    """Get the singleton MinIO client instance"""
    global _minio_client
    if _minio_client is None:
        logger.info(f"Initializing MinIO client for endpoint: {MINIO_ENDPOINT}")
        _minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE,
            region=MINIO_REGION
        )
        
        # Ensure default bucket exists
        try:
            if not _minio_client.bucket_exists(MINIO_DEFAULT_BUCKET):
                logger.info(f"Creating default bucket: {MINIO_DEFAULT_BUCKET}")
                _minio_client.make_bucket(MINIO_DEFAULT_BUCKET, location=MINIO_REGION)
        except S3Error as e:
            logger.warning(f"Error checking/creating default bucket: {e}")
            
    return _minio_client


def reset_minio_client():
    """Reset the MinIO client (useful for testing)"""
    global _minio_client
    _minio_client = None