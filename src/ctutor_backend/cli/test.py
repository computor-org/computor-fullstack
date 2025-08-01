import json
import os
import click
from ctutor_backend.api.exceptions import BadRequestException
from ctutor_backend.cli.auth import authenticate, get_crud_client, get_custom_client
from ctutor_backend.cli.config import CLIAuthConfig
from ctutor_backend.cli.crud import handle_api_exceptions
from ctutor_backend.cli.release import handle_flow_runs
from ctutor_backend.interface.results import ResultGet, ResultInterface
from ctutor_backend.interface.tests import TestCreate
from git import Repo, InvalidGitRepositoryError

def get_repo_info():
    script_dir = "."

    try:
        repo = Repo(script_dir, search_parent_directories=True)

        repo_url = repo.remotes.origin.url

        repo_root = repo.git.rev_parse("--show-toplevel")
        relative_path = os.path.relpath(script_dir, repo_root)

        return repo_url, relative_path

    except InvalidGitRepositoryError:
        raise BadRequestException(detail="Is not a git repository")

@click.command()
@authenticate
@handle_api_exceptions
def run_test(auth: CLIAuthConfig):

    repo_url, directory = get_repo_info()

    test_create = TestCreate(
        directory=directory
    )
    
    custom_client = get_custom_client(auth)

    result = ResultGet(**custom_client.create("tests",test_create.model_dump()))

    if handle_flow_runs(result.test_system_id, custom_client) == True:
        
        if click.confirm('Do you want to show test results?'):
            result = json.dumps(get_crud_client(auth,ResultInterface).get(result.id).result_json,indent=3)
            click.echo(result)
    
