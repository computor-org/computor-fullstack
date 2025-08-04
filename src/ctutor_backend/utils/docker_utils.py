"""
Docker-related utility functions.

This module provides utilities for detecting Docker environments and
transforming URLs for container-to-host communication.
"""

import os
from pathlib import Path
from typing import Optional


def is_running_in_docker() -> bool:
    """
    Detect if the current process is running inside a Docker container.
    
    Uses multiple detection methods:
    1. Check for RUNNING_IN_DOCKER environment variable (explicit)
    2. Check for /.dockerenv file (Docker standard)
    3. Check for Docker in /proc/1/cgroup (Linux containers)
    
    Returns:
        bool: True if running in Docker, False otherwise
    """
    # Method 1: Explicit environment variable
    if os.environ.get("RUNNING_IN_DOCKER", "").lower() in ("true", "1", "yes"):
        return True
    
    # Method 2: Check for .dockerenv file
    if Path("/.dockerenv").exists():
        return True
    
    # Method 3: Check cgroup for docker references (Linux only)
    try:
        with open("/proc/1/cgroup", "r") as f:
            for line in f:
                if "docker" in line or "containerd" in line:
                    return True
    except (FileNotFoundError, PermissionError):
        # File doesn't exist or can't be read (non-Linux or no permissions)
        pass
    
    # Method 4: Check for Kubernetes environment (often Docker-based)
    if os.environ.get("KUBERNETES_SERVICE_HOST"):
        return True
    
    return False


def get_docker_host_ip() -> str:
    """
    Get the Docker host IP address for container-to-host communication.
    
    Returns:
        str: The Docker host IP address (default: "172.17.0.1")
    """
    # Allow override via environment variable
    return os.environ.get("DOCKER_HOST_IP", "172.17.0.1")


def transform_localhost_url(url: Optional[str], force: bool = False) -> Optional[str]:
    """
    Transform localhost URLs to Docker host IP for container-to-host communication.
    
    This function replaces "localhost" and "127.0.0.1" with the Docker host IP
    when running inside a Docker container, enabling containers to communicate
    with services running on the host machine.
    
    Args:
        url: URL that may contain localhost references
        force: Force transformation even if not detected as running in Docker
        
    Returns:
        URL with localhost replaced by Docker host IP if in Docker, 
        original URL otherwise
        
    Examples:
        >>> # Running in Docker
        >>> transform_localhost_url("http://localhost:8080")
        "http://172.17.0.1:8080"
        
        >>> # Not in Docker (returns unchanged)
        >>> transform_localhost_url("http://localhost:8080")
        "http://localhost:8080"
        
        >>> # Force transformation
        >>> transform_localhost_url("http://localhost:8080", force=True)
        "http://172.17.0.1:8080"
    """
    if not url:
        return url
    
    # Only transform if we're in Docker or forced
    if not force and not is_running_in_docker():
        return url
    
    docker_host = get_docker_host_ip()
    
    # Replace various localhost references
    transformed = url
    localhost_variants = [
        "localhost",
        "127.0.0.1",
        "127.0.1.1",  # Sometimes used in Ubuntu
        "::1",  # IPv6 localhost
        "[::1]",  # IPv6 localhost in URL format
    ]
    
    for variant in localhost_variants:
        # Handle both http://localhost and localhost (without protocol)
        transformed = transformed.replace(f"://{variant}", f"://{docker_host}")
        transformed = transformed.replace(f"@{variant}", f"@{docker_host}")
        
        # Handle cases where localhost appears without protocol prefix
        if transformed.startswith(variant):
            transformed = transformed.replace(variant, docker_host, 1)
    
    return transformed


def transform_gitlab_url(url: Optional[str]) -> Optional[str]:
    """
    Transform GitLab URL for Docker environment if needed.
    
    This is a specialized version of transform_localhost_url specifically
    for GitLab URLs, with additional GitLab-specific handling if needed.
    
    Args:
        url: GitLab URL that may need transformation
        
    Returns:
        Transformed URL suitable for Docker environment
    """
    if not url:
        return url
    
    # First apply standard localhost transformation
    url = transform_localhost_url(url)
    
    # Add any GitLab-specific transformations here if needed
    # For example, handling special GitLab Docker registry URLs
    
    return url


def get_service_url(service_name: str, default_port: int) -> str:
    """
    Get the URL for a service, handling Docker networking automatically.
    
    Args:
        service_name: Name of the service (e.g., "gitlab", "temporal", "minio")
        default_port: Default port for the service
        
    Returns:
        str: URL for the service, adjusted for Docker if necessary
        
    Examples:
        >>> get_service_url("gitlab", 8084)
        "http://172.17.0.1:8084"  # If in Docker
        "http://localhost:8084"   # If not in Docker
    """
    # Check for service-specific environment variables first
    env_var = f"{service_name.upper()}_URL"
    if url := os.environ.get(env_var):
        return transform_localhost_url(url)
    
    # Build default URL
    host = "localhost"
    if is_running_in_docker():
        host = get_docker_host_ip()
    
    # Check for service-specific port override
    port_env_var = f"{service_name.upper()}_PORT"
    port = os.environ.get(port_env_var, str(default_port))
    
    return f"http://{host}:{port}"


# Service-specific convenience functions
def get_gitlab_url() -> str:
    """Get GitLab URL adjusted for Docker environment."""
    return get_service_url("gitlab", 8084)


def get_temporal_url() -> str:
    """Get Temporal URL adjusted for Docker environment."""
    return get_service_url("temporal", 7233)


def get_minio_url() -> str:
    """Get MinIO URL adjusted for Docker environment."""
    return get_service_url("minio", 9000)


def get_keycloak_url() -> str:
    """Get Keycloak URL adjusted for Docker environment."""
    return get_service_url("keycloak", 8080)


def get_postgres_host() -> str:
    """Get PostgreSQL host adjusted for Docker environment."""
    if is_running_in_docker():
        # In Docker, use the service name or Docker host IP
        return os.environ.get("DB_HOST", get_docker_host_ip())
    return os.environ.get("DB_HOST", "localhost")