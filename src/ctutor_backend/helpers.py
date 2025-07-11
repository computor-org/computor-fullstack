from prefect.client.orchestration import PrefectClient
from ctutor_backend.settings import settings

def read_file(filepath) -> str:
    with open(filepath) as file:
        return file.read()

def get_prefect_client():
  if settings.DEBUG_MODE  == "production":
    return PrefectClient("http://prefect:4200/api")
  else:
    return PrefectClient("http://localhost:4200/api")