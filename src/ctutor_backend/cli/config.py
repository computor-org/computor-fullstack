from typing import Optional
from ctutor_backend.interface.deployments import BaseDeployment
from ctutor_backend.interface.auth import BasicAuthConfig, GLPAuthConfig

class CLIAuthConfig(BaseDeployment):
    api_url: str
    gitlab: Optional[GLPAuthConfig] = None
    basic: Optional[BasicAuthConfig] = None