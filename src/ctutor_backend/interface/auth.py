from abc import ABC
from ctutor_backend.interface.deployments import BaseDeployment

class AuthConfig(ABC,BaseDeployment):
    pass

class GLPAuthConfig(AuthConfig):
    url: str
    token: str

class BasicAuthConfig(AuthConfig):
    username: str
    password: str