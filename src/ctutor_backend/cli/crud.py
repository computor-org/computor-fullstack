import click
from fastapi import HTTPException
from httpx import ConnectError
from ctutor_backend.cli.auth import authenticate, get_crud_client
from ctutor_backend.cli.config import CLIAuthConfig
from ctutor_backend.interface.results import ResultInterface
from ctutor_backend.interface.users import UserInterface
from ctutor_backend.interface.courses import CourseInterface
from ctutor_backend.interface.organizations import OrganizationInterface
from ctutor_backend.interface.course_families import CourseFamilyInterface
from ctutor_backend.interface.course_groups import CourseGroupInterface
from ctutor_backend.interface.course_members import CourseMemberInterface
from ctutor_backend.interface.course_roles import CourseRoleInterface
from ctutor_backend.interface.course_content_types import CourseContentTypeInterface
from ctutor_backend.interface.course_contents import CourseContentInterface


AVAILABLE_DTO_DEFINITIONS = [
    OrganizationInterface.endpoint,
    CourseFamilyInterface.endpoint,
    CourseInterface.endpoint,
    CourseContentInterface.endpoint,
    CourseContentTypeInterface.endpoint,
    CourseGroupInterface.endpoint,
    CourseMemberInterface.endpoint,
    CourseRoleInterface.endpoint,
    UserInterface.endpoint,
    ResultInterface.endpoint
]

def DTO_DEFINITIONS(table: str):

    if OrganizationInterface.endpoint == table:
        return OrganizationInterface
    elif CourseFamilyInterface.endpoint == table:
        return CourseFamilyInterface
    elif CourseInterface.endpoint == table:
        return CourseInterface
    elif CourseContentInterface.endpoint == table:
        return CourseContentInterface
    elif CourseContentTypeInterface.endpoint == table:
        return CourseContentTypeInterface
    elif CourseGroupInterface.endpoint == table:
        return CourseGroupInterface
    elif CourseMemberInterface.endpoint == table:
        return CourseMemberInterface
    elif CourseRoleInterface.endpoint == table:
        return CourseRoleInterface
    elif UserInterface.endpoint == table:
        return UserInterface
    elif ResultInterface.endpoint == table:
        return ResultInterface
    else:
        raise Exception("Not found")


def handle_api_exceptions(func):
  def wrapper(*args, **kwargs):
    try:
      return func(*args, **kwargs)
    except ConnectError as e:
      click.echo(f"Connection to [{click.style(kwargs['auth'].api_url,fg='red')}] could not be established.")
    except HTTPException as e:
      message = e.detail.get("detail")
      message = message if message != None else e.detail
      click.echo(f"[{click.style(e.status_code,fg='red')}] {message}")
    except Exception as e:
      click.echo(f"[{click.style('500',fg='red')}] {e.args if e.args != () else 'Internal Server Error'}")

  return wrapper

@click.command()
@click.option("--table", "-t", type=click.Choice(AVAILABLE_DTO_DEFINITIONS), prompt="Type")
@click.option("--query", "-q", "query", type=(str, str), multiple=True)
@authenticate
@handle_api_exceptions
def list_entities(table, query, auth: CLIAuthConfig):

  params = None
  query = dict(query)
  if dict(query) != {}:
    params = DTO_DEFINITIONS(table).query(**query)

  resp = get_crud_client(auth,DTO_DEFINITIONS(table)).list(params)

  for entity in resp:
    click.echo(f"{entity.model_dump_json(indent=4)}")

@click.command()
@click.option("--table", "-t", type=click.Choice(AVAILABLE_DTO_DEFINITIONS), prompt="Type")
def show_entities_query(table):

  dto = DTO_DEFINITIONS(table)

  query_fields = dto.query.model_fields

  click.echo(f"Query parameters for endpoint [{click.style(dto.endpoint,fg='green')}]:\n")
  for field, info in query_fields.items():
    click.echo(f"{click.style(field,fg='green')} - {info.annotation}")

@click.command()
@click.option("--table", "-t", type=click.Choice(AVAILABLE_DTO_DEFINITIONS), prompt="Type")
@click.option("--id", "-i", prompt=True)
@authenticate
@handle_api_exceptions
def get_entity(table, id, auth: CLIAuthConfig):

  entity = get_crud_client(auth,DTO_DEFINITIONS(table)).get(id)

  click.echo(f"{entity.model_dump_json(indent=4)}")

@click.group()
def rest():
    pass

rest.add_command(list_entities,"list")
rest.add_command(show_entities_query,"query")
rest.add_command(get_entity,"get")