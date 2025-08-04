"""
Utilities package for ctutor_backend.
"""

from .color_validation import (
    is_valid_color, validate_color, is_valid_hex_color, 
    is_valid_rgb_color, is_valid_hsl_color, is_valid_css_named_color,
    get_color_examples
)

from .docker_utils import (
    is_running_in_docker, get_docker_host_ip, transform_localhost_url,
    transform_gitlab_url, get_service_url, get_gitlab_url, get_temporal_url,
    get_minio_url, get_keycloak_url, get_postgres_host
)

__all__ = [
    # Color validation
    'is_valid_color', 'validate_color', 'is_valid_hex_color', 
    'is_valid_rgb_color', 'is_valid_hsl_color', 'is_valid_css_named_color',
    'get_color_examples',
    # Docker utilities
    'is_running_in_docker', 'get_docker_host_ip', 'transform_localhost_url',
    'transform_gitlab_url', 'get_service_url', 'get_gitlab_url', 'get_temporal_url',
    'get_minio_url', 'get_keycloak_url', 'get_postgres_host'
]