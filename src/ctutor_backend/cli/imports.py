import click
import yaml
from pathlib import Path
from ctutor_backend.api.exceptions import BadRequestException
from ctutor_backend.api.system import ReleaseStudentsCreate
from ctutor_backend.cli.auth import authenticate
from ctutor_backend.cli.config import CLIAuthConfig
from ctutor_backend.cli.crud import handle_api_exceptions
from ctutor_backend.client.crud_client import CustomClient
from ctutor_backend.generator.export_user import ExportUser
from ctutor_backend.interface.accounts import AccountCreate, AccountInterface, AccountQuery
from ctutor_backend.interface.users import UserCreate, UserGet, UserInterface, UserQuery
from ctutor_backend.cli.auth import authenticate, get_crud_client
from ctutor_backend.interface.deployments_refactored import UsersDeploymentConfig

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

# @click.command()
# @click.option("--file", "-f", prompt="Directory")
# @click.option("--type", "-t", type=click.Choice(["gitlab"]), default="gitlab")
# @click.option("--provider", "-p", prompt="Provider", default="https://gitlab.com")
# @click.option("--course-id", "-c", prompt="Course Id", prompt_required=False)
# @click.option("--course-group-title", "-g", prompt="Course group Title", prompt_required=False)
# @authenticate
# @handle_api_exceptions
# def import_users(file, type, provider, course_id, course_group_title, auth: CLIAuthConfig):
#     from ctutor_backend.api.system import StudentCreate

#     export_users = ExportUser.read_excel(file)
#     releaseStudentList: list[StudentCreate] = []

#     for export_user in export_users:
#         user = create_user_from_export(auth,export_user,type,provider)

#         if user != None and course_id != None:
#             releaseStudentList.append(StudentCreate(user_id=str(user.id),course_group_title=course_group_title,role=export_user.role).model_dump())

#     custom_client = CustomClient(url_base=auth.api_url,auth=(auth.basic.username,auth.basic.password))

#     if len(releaseStudentList) == 0:
#         raise BadRequestException()

#     try:
#         resp = custom_client.create(
#             "/system/release/students",
#             ReleaseStudentsCreate(
#                 course_id=str(course_id),
#                 students=releaseStudentList
#             ).model_dump()
#         )

#         handle_flow_runs(resp['flow_run_id'], custom_client)

#     except Exception as e:
#         click.echo(e)
#         return


# def create_user_from_deployment(auth: CLIAuthConfig, user_deployment, account_deployment=None) -> UserGet | None:
#     """Create a user from UserDeployment configuration."""
    
#     user_client = get_crud_client(auth, UserInterface)
#     account_client = get_crud_client(auth, AccountInterface)
    
#     # Check if user already exists by email or username
#     existing_users = []
#     if user_deployment.email:
#         existing_users.extend(user_client.list(UserQuery(email=user_deployment.email)))
#     if user_deployment.username and not existing_users:
#         # Only check username if no user found by email
#         try:
#             # Username search might not be directly supported, so we'll handle it gracefully
#             pass
#         except:
#             pass
    
#     if existing_users:
#         user = existing_users[0]
#         click.echo(f"User already exists: [{click.style(user.display_name, fg='yellow')}] ({user.email})")
#     else:
#         # Create new user
#         user_create = UserCreate(
#             given_name=user_deployment.given_name,
#             family_name=user_deployment.family_name,
#             email=user_deployment.email,
#             number=user_deployment.number,
#             username=user_deployment.username,
#             user_type=user_deployment.user_type,
#             properties=user_deployment.properties
#         )
        
#         try:
#             user = user_client.create(user_create)
#             click.echo(f"Created user: [{click.style(user.display_name, fg='green')}] ({user.email})")
#         except Exception as e:
#             click.echo(f"Failed to create user {user_deployment.display_name}: {e}")
#             return None
    
#     # Create account if provided
#     if account_deployment:
#         # Check if account already exists
#         existing_accounts = account_client.list(AccountQuery(
#             provider_account_id=account_deployment.provider_account_id
#         ))
        
#         if existing_accounts:
#             click.echo(f"Account already exists: [{click.style(f'{account_deployment.provider}:{account_deployment.provider_account_id}', fg='yellow')}]")
#         else:
#             # Create new account
#             account_create = AccountCreate(
#                 provider=account_deployment.provider,
#                 type=account_deployment.type,
#                 provider_account_id=account_deployment.provider_account_id,
#                 user_id=str(user.id),
#                 properties=account_deployment.properties or {}
#             )
            
#             try:
#                 account = account_client.create(account_create)
#                 click.echo(f"Created account: [{click.style(account.display_name, fg='green')}] for user {user.display_name}")
#             except Exception as e:
#                 click.echo(f"Failed to create account for {user.display_name}: {e}")
    
#     return user


@click.command()
@click.option("--file", "-f", required=True, help="Path to users deployment YAML file")
@click.option("--dry-run", is_flag=True, help="Preview what would be imported without making changes")
@authenticate
@handle_api_exceptions
def import_users_yaml(file, dry_run, auth: CLIAuthConfig):
    """Import users from a YAML deployment file into the system."""
    
    # Check if file exists
    yaml_file = Path(file)
    if not yaml_file.exists():
        click.echo(f"Error: File {file} not found", err=True)
        return
    
    # Load and parse the YAML file
    try:
        with open(yaml_file, 'r') as f:
            config_data = yaml.safe_load(f)
        deployment = UsersDeploymentConfig(**config_data)
    except Exception as e:
        click.echo(f"Error loading deployment file: {e}", err=True)
        return
    
    click.echo(f"Loading users from: {yaml_file}")
    click.echo(f"Found {deployment.count_users()} users to import")
    
    if dry_run:
        click.echo(f"\n{click.style('DRY RUN MODE - No changes will be made', fg='yellow')}")
    
    click.echo("-" * 60)
    
    created_users = []
    failed_users = []
    
    for user_account_deployment in deployment.users:
        user_dep = user_account_deployment.user
        gitlab_account = user_account_deployment.get_primary_gitlab_account()
        
        click.echo(f"\nProcessing: {user_dep.display_name} ({user_dep.username})")
        
        if dry_run:
            click.echo(f"  Would create user: {user_dep.email}")
            if gitlab_account:
                click.echo(f"  Would create GitLab account: {gitlab_account.provider_account_id}")
            created_users.append(user_dep)
            continue
        
        # Create the user and account
        try:
            user = create_user_from_deployment(auth, user_dep, gitlab_account)
            if user:
                created_users.append(user_dep)
            else:
                failed_users.append(user_dep)
        except Exception as e:
            click.echo(f"  Error: {e}")
            failed_users.append(user_dep)
    
    # Summary
    click.echo(f"\n{'=' * 60}")
    click.echo("IMPORT SUMMARY")
    click.echo(f"{'=' * 60}")
    click.echo(f"Total users processed: {len(deployment.users)}")
    click.echo(f"Successful: {len(created_users)}")
    click.echo(f"Failed: {len(failed_users)}")
    
    if failed_users:
        click.echo(f"\nFailed users:")
        for user_dep in failed_users:
            click.echo(f"  - {user_dep.display_name} ({user_dep.email})")


@click.group()
def import_group():
    pass

# import_group.add_command(import_users,"users")
import_group.add_command(import_users_yaml,"users-yaml")
