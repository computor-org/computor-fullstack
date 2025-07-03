import click
from ctutor_backend.api.exceptions import BadRequestException
from ctutor_backend.api.system import ReleaseStudentsCreate
from ctutor_backend.cli.auth import authenticate
from ctutor_backend.cli.config import CLIAuthConfig
from ctutor_backend.cli.crud import handle_api_exceptions
from ctutor_backend.cli.release import handle_flow_runs
from ctutor_backend.client.crud_client import CustomClient
from ctutor_backend.generator.export_user import ExportUser
from ctutor_backend.interface.accounts import AccountCreate, AccountInterface, AccountQuery
from ctutor_backend.interface.users import UserCreate, UserGet, UserInterface, UserQuery
from ctutor_backend.cli.auth import authenticate, get_crud_client

def create_user_from_export(auth: CLIAuthConfig, export_user: ExportUser, type: str, provider: str) -> UserGet | None:

    user_client = get_crud_client(auth,UserInterface)
    account_client = get_crud_client(auth,AccountInterface)

    # try:

    users = user_client.list(UserQuery(email=export_user.email))

    if len(users) == 0:

        user = user_client.create(UserCreate(
            given_name=export_user.first_name,
            family_name=export_user.family_name,
            email=export_user.email))

        click.echo(f"Created user [{click.style(f'{user.given_name} {user.family_name}',fg='green')}]")
    
    else:
        user = users[0]

    accounts = account_client.list(AccountQuery(provider_account_id=export_user.username))

    if len(accounts) == 0:

        account = account_client.create(AccountCreate(
                type=type,
                provider=provider,
                user_id=str(user.id),
                provider_account_id=export_user.username
            ))
        
        click.echo(f"Created account [{click.style(f'{account.type} | {account.provider}',fg='green')}] for user [{click.style(f'{user.given_name} {user.family_name}',fg='green')}]")
    
    else:
        account = accounts[0]

    return user

@click.command()
@click.option("--file", "-f", prompt="Directory")
@click.option("--type", "-t", type=click.Choice(["gitlab"]), default="gitlab")
@click.option("--provider", "-p", prompt="Provider", default="https://gitlab.com")
@click.option("--course-id", "-c", prompt="Course Id", prompt_required=False)
@click.option("--course-group-title", "-g", prompt="Course group Title", prompt_required=False)
@authenticate
@handle_api_exceptions
def import_users(file, type, provider, course_id, course_group_title, auth: CLIAuthConfig):
    from ctutor_backend.api.system import StudentCreate

    export_users = ExportUser.read_excel(file)
    releaseStudentList: list[StudentCreate] = []

    for export_user in export_users:
        user = create_user_from_export(auth,export_user,type,provider)

        if user != None and course_id != None:
            releaseStudentList.append(StudentCreate(user_id=str(user.id),course_group_title=course_group_title,role=export_user.role).model_dump())

    custom_client = CustomClient(url_base=auth.api_url,auth=(auth.basic.username,auth.basic.password))

    if len(releaseStudentList) == 0:
        raise BadRequestException()

    try:
        resp = custom_client.create(
            "/system/release/students",
            ReleaseStudentsCreate(
                course_id=str(course_id),
                students=releaseStudentList
            ).model_dump()
        )

        handle_flow_runs(resp['flow_run_id'], custom_client)

    except Exception as e:
        click.echo(e)
        return

@click.group()
def import_group():
    pass

import_group.add_command(import_users,"users")
