import os
import asyncio
import shutil
from typing import Any, Tuple
from gitlab import Gitlab
from gitlab.v4.objects import Project, Group
from unidecode import unidecode
from pydantic_yaml import to_yaml_str
from ctutor_backend.api.system import CourseReleaseUpdate
from ctutor_backend.api.utils import directory_path_to_db_path_and_parent_path, directory_path_to_position
from ctutor_backend.client.crud_client import CrudClient, CustomClient
from ctutor_backend.client.api_client import get_course_content_from_path_api, get_course_content_type_from_slug_api, get_execution_backend_from_slug_api, validate_course_content_api, validate_course_member_api
from ctutor_backend.client.api_client import validate_course_api, validate_course_execution_backend_api, validate_course_family_api
from ctutor_backend.client.api_client import validate_organization_api, validate_execution_backend_api
from ctutor_backend.interface.deployments import CodeabilityReleaseBuilder
from ctutor_backend.generator.git_helper import git_clone, git_version_identifier, git_repo_exist, git_repo_create, git_repo_pull, git_repo_commit
from ctutor_backend.generator.release import release_assignment_reference, release_course, release_unit, release_assignment, check_realease_course_content_type
from ctutor_backend.gitlab_utils import gitlab_unprotect_branches, gitlab_fork_project
from ctutor_backend.interface.accounts import AccountInterface, AccountList, AccountQuery
from ctutor_backend.interface.course_content_types import CourseContentTypeCreate
from ctutor_backend.interface.course_families import CourseFamilyProperties
from ctutor_backend.interface.deployments import ApiConfig, ComputorDeploymentConfig, CourseProjectsConfig, GitLabConfig, GitlabGroupProjectConfig
from ctutor_backend.interface.deployments import CodeAbilityCourseMeta
from ctutor_backend.interface.course_execution_backends import CourseExecutionBackendGet
from ctutor_backend.interface.execution_backends import ExecutionBackendGet
from ctutor_backend.interface.courses import CourseProperties, CourseUpdate
from ctutor_backend.interface.organizations import OrganizationProperties
from ctutor_backend.interface.tokens import encrypt_api_key
from ctutor_backend.interface.course_contents import CourseContentCreate, CourseContentProperties
from ctutor_backend.interface.users import UserGet
from ctutor_backend.interface.course_members import CourseMemberGet, CourseMemberGitLabConfig, CourseMemberProperties
from ctutor_backend.settings import settings
from ctutor_backend.helpers import read_file

GITLAB_CI_FILENAME = ".gitlab-ci.yml"
DOCKER_FILENAME = "Dockerfile"

# TODO: REFACTORING: change to constants or smth else. Defaults has to be defined for each builder type
GITLAB_COURSE_PROJECTS = CourseProjectsConfig(
  tests=GitlabGroupProjectConfig(path="assignments"),
  student_template=GitlabGroupProjectConfig(path="student-template"),
  reference=GitlabGroupProjectConfig(path="reference"),
  images=GitlabGroupProjectConfig(path="oci-registry"),
  documents=GitlabGroupProjectConfig(path="documents",name="Documents")
)

_repo_init_file_mapper = [
  ("README.md","README.md"),
  ("gitignore", ".gitignore")
] 

def _copy_files(source: str, destination: str, mapper: list[tuple[str,str]]):
    for file_name_from, file_name_to in mapper:

      file1 = os.path.join(source,file_name_from)
      file2 = os.path.join(destination,file_name_to)

      if not os.path.exists(file1):
        continue

      shutil.copy(file1,file2)

class CodeabilityGitlabBuilder(CodeabilityReleaseBuilder):
    def __init__(
        self,
        api_config: ApiConfig,
        deployment: ComputorDeploymentConfig,
        work_dir: str
    ):
        
        self.api_config = api_config

        self.execution_backends: list[ExecutionBackendGet] = []
        self.course_execution_backends: list[CourseExecutionBackendGet] = []
        
        self.work_dir = work_dir

        self.deployment = deployment
        self.gitlab_token = deployment.organization.gitlab.token

        self.gitlab = Gitlab(
            url=self.deployment.organization.gitlab.url,
            private_token=self.gitlab_token
        )

        self.create_all_groups()

    def create_all_groups(self):

        parent_group_full_path = None

        if self.deployment.organization.gitlab.parent != None:
            parent_group = self.gitlab.groups.get(self.deployment.organization.gitlab.parent)
            parent_group_full_path = parent_group.full_path

        self.organization_group, r = self.create_or_get_group(
            self.deployment.organization.name,
            parent_group_full_path,
            self.deployment.organization.path,
            self.deployment.organization.gitlab.parent
        )

        orgnization_properties = OrganizationProperties(gitlab=GitLabConfig(
            url=self.deployment.organization.gitlab.url,
            full_path=self.organization_group.full_path,
            token=encrypt_api_key(self.deployment.organization.gitlab.token),
            parent=self.deployment.organization.gitlab.parent,
            settings=self.deployment.organization.gitlab.settings
        ))

        self.organization = validate_organization_api(self.deployment, self.api_config, orgnization_properties)

        self.family_group, r = self.create_or_get_group(
            self.deployment.courseFamily.name,
            self.organization_group.full_path,
            self.deployment.courseFamily.path,
            self.organization_group.get_id()
        )

        properties = CourseFamilyProperties(gitlab=GitLabConfig(
            url=self.deployment.organization.gitlab.url,
            full_path=self.family_group.full_path,
            settings=self.deployment.organization.gitlab.settings
        ))
        
        self.course_family = validate_course_family_api(self.deployment, self.api_config, self.organization, properties)

        self.create_project_documents(self.family_group,f"{self.organization.path}/{self.course_family.path}",self.course_family.id)

        self.course_group, r = self.create_or_get_group(
            self.deployment.course.name,
            self.family_group.full_path,
            self.deployment.course.path,
            self.family_group.get_id()
        )

        properties = CourseProperties(gitlab=GitLabConfig(
            url=self.deployment.organization.gitlab.url,
            full_path=self.course_group.full_path,
            settings=self.deployment.organization.gitlab.settings
        ))

        self.course = validate_course_api(self.deployment, self.api_config, self.course_family, properties)

        for execution_backend_deployment in self.deployment.course.executionBackends or []:

            execution_backend = validate_execution_backend_api(self.api_config, execution_backend_deployment)
            course_execution_backend = validate_course_execution_backend_api(self.api_config, execution_backend, self.course)

            self.execution_backends.append(execution_backend)
            self.course_execution_backends.append(course_execution_backend)

        self.students_group, r = self.create_or_get_group(
            "students",
            self.course_group.full_path,
            "students",
            self.course_group.get_id(),
            os.path.join(settings.API_LOCAL_STORAGE_DIR,"defaults/deployments/students_group_description.md"))

        self.submissions_group, r = self.create_or_get_group(
            "submissions",
            self.course_group.full_path,
            "submissions",
            self.course_group.get_id(),
            os.path.join(settings.API_LOCAL_STORAGE_DIR,"defaults/deployments/submissions_group_description.md"))
        
        self.create_project_testing()
        self.create_student_template()
        self.create_reference()

    def create_or_get_project(self, project_deployment: GitlabGroupProjectConfig, group: Group) -> Tuple[Project,bool]:

        projects = group.projects.list(search=project_deployment.path)

        if len(projects) == 1:
            project = self.gitlab.projects.get(projects[0].get_id())
            project.name = project_deployment.display_name
            project.save()
            return project, False

        else:
            project = self.gitlab.projects.create({
                "name": project_deployment.display_name,
                "path": project_deployment.path,
                "namespace_id": group.get_id()
            })

        return project, True  

    def create_or_get_group(self, name: str | None, parent_path: str | None, path: str, parent_id: str | int, description_file_path: str | None = None) -> Tuple[Group,bool]:

        if parent_path != None:
          groups = list(filter(lambda g  : g.full_path == f"{parent_path}/{path}",
                      self.gitlab.groups.list(search=f"{parent_path}/{path}")))
        else:
          groups = list(filter(lambda g  : g.full_path == path,
                      self.gitlab.groups.list(search=path)))

        description = ""
        if description_file_path != None:
          try:
            description = read_file(os.path.join(settings.API_LOCAL_STORAGE_DIR,description_file_path))
          except:
            pass
            
        created = False
        if len(groups) == 1:
          group = self.gitlab.groups.get(groups[0].get_id())
          try:
            group.description = description
            group.save()
          except Exception as e:
            print(f"Could not save description to group: {e.args}")
        else:
          payload = {
              "path": path,
              "name": name,
              "description": description
          }

          if parent_id != None:
            payload["parent_id"] = parent_id

          group = self.gitlab.groups.create(payload)
          created = True

        return group, created
    
    def create_gitlab_project_path(user: UserGet):
      
      first_name = unidecode(user.given_name).lower().replace("ö","oe").replace("ä","ae").replace("ü","ue").replace(" ", "_")
      family_name = unidecode(user.family_name).lower().replace("ö","oe").replace("ä","ae").replace("ü","ue").replace(" ", "_")

      return f"{family_name}_{first_name}"

    def get_gitlab_user_info(self, user: UserGet):
        
        account: AccountList = CrudClient(
           url_base=self.api_config.url,
           auth=(self.api_config.user,self.api_config.password),
           entity_interface=AccountInterface
        ).get_first_or_default(
          AccountQuery(
            user_id=str(user.id), 
            type="gitlab", 
            provider=self.deployment.organization.gitlab.url))
        
        if account == None:
          return None
        
        gitlab_user_id = self.gitlab.users.list(username=account.provider_account_id)[0].get_id()

        return gitlab_user_id

    async def create_submission_project(self, user: UserGet, gitlab_user_id, gitlab_user_path):

      dir_submission = os.path.join(self.work_dir,"submissions",gitlab_user_path)

      project_name = f"{user.given_name} {user.family_name}"

      submissions_project, created_submissions_project = self.create_repository(
        dir_submission, 
        GitlabGroupProjectConfig(
          path=gitlab_user_path,
          name=project_name
        ), 
        self.submissions_group, 
        "student-submission")

      if created_submissions_project:
        if gitlab_user_id != None:
          try:
            submissions_project.members.create({
              "user_id": gitlab_user_id,
              "access_level": 30
            })
          except Exception as e:
            print(f"give access level: {str(e)} | {user.id}")
        else:
          print(f"Created gitlab repository without setting access level due to misisng gitlab_user_id")

      return submissions_project.path_with_namespace if submissions_project != None else None

    async def create_student_working_project(self, user: UserGet, gitlab_user_id, gitlab_user_path):

        project_name = f"{user.given_name} {user.family_name}"

        if len(self.students_group.projects.list(search=gitlab_user_path)) == 0:
          gitlab_fork_project(
            self.gitlab,
            self.student_template_project.get_id(),
            gitlab_user_path,
            project_name,
            self.students_group.get_id()
          )

          await asyncio.sleep(2)

        else:
          print("Project already exists (no fork)")

        student_project = None
        for i in range(0,20):
          try:
            query = self.students_group.projects.list(search=gitlab_user_path)
            if len(query) == 1:
              student_project = self.gitlab.projects.get(query[0].get_id())
              break
          except:
            print("Waiting for student working project [a fork process takes time]")
          print(f"Waited {i+1} iterations for fork process to succeed")

          await asyncio.sleep(5)

        if student_project != None:
          if gitlab_user_id != None:
            try:
              student_project.members.create({
                "user_id": gitlab_user_id,
                "access_level": 40
              })
            except Exception as e:
              print(f"give access level: {str(e)} | {user.id}")

            try:
              access_level = 20
              self.set_permission(self.student_template_project, gitlab_user_id, access_level)

            except Exception as e:
              print(f"Setting access level {access_level} for student template failed | {str(e)}")
          else:
            print(f"Created gitlab repository without setting access level due to misisng gitlab_user_id")

          try:
            gitlab_unprotect_branches(self.gitlab, student_project.get_id(), "main")

          except Exception as e:
            print(f"unprotect branch: {str(e)} | {user.id}")

          misc_dir = os.path.join(settings.API_LOCAL_STORAGE_DIR,"defaults/deployments/student-working")

          try:
            description = read_file(os.path.join(misc_dir,"description.md"))
            pr_resp = self.gitlab.projects.update(student_project.get_id(),{"description": description})
          except Exception as e:
            print(f"{student_project.path} | creating or editing description failed | {str(e)}")

        else:
          raise Exception(f"Could not retreive forked project for student {user.given_name} {user.family_name}")

        return student_project.path_with_namespace

    async def create_student_project(self, user: UserGet, course_group_id: str | None, role: str) -> CourseMemberGet:

      gitlab_user_path = CodeabilityGitlabBuilder.create_gitlab_project_path(user)
      gitlab_user_id = self.get_gitlab_user_info(user)

      full_path_working = await self.create_student_working_project(user,gitlab_user_id,gitlab_user_path)
      full_path_submission = await self.create_submission_project(user,gitlab_user_id,gitlab_user_path)

      try:
        if role == "_study_assistant":
          self.set_permission(self.reference_project,gitlab_user_id,20)
          self.set_permission(self.students_group,gitlab_user_id,20)
          self.set_permission(self.submissions_group,gitlab_user_id,40)

        elif role == "_maintainer":
          self.set_permission(self.family_group,gitlab_user_id,40)

        elif role == "_owner":
          self.set_permission(self.family_group,gitlab_user_id,40)
          self.set_permission(self.course_group,gitlab_user_id,50)

      except:
        pass

      properties = CourseMemberProperties(
        gitlab=CourseMemberGitLabConfig(
          url=self.course.properties.gitlab.url,
          full_path=full_path_working,
          full_path_submission=full_path_submission
        )
      )

      return validate_course_member_api(self.api_config, user.id, self.course.id, role, course_group_id, properties)

    def get_directory_testing(self):
      return os.path.join(self.work_dir,GITLAB_COURSE_PROJECTS.tests.path)

    def create_project_testing(self):

      dir_testing = self.get_directory_testing()

      settings = self.deployment.course.settings

      if settings != None and settings.source != None:

        def init_repo_files():
          import tempfile
          with tempfile.TemporaryDirectory() as tmp:
            git_clone(tmp,settings.source.url,settings.source.token)
            shutil.rmtree(os.path.join(tmp,".git"))
            shutil.copytree(tmp,dir_testing,dirs_exist_ok=True)
      else:
        def init_repo_files():
          course_meta = CodeAbilityCourseMeta(
            description="",
            title=self.deployment.course.name,
            version="0.1",
            contentTypes=self.deployment.course.contentTypes,
            executionBackends=self.deployment.course.executionBackends
          )
          with open(os.path.join(dir_testing,"meta.yaml"), "w") as file:
            file.write(to_yaml_str(course_meta,exclude_none=True))

      self.assignment_project, created_assignment_project = self.create_repository(
        dir_testing, 
        GITLAB_COURSE_PROJECTS.tests, 
        self.course_group, 
        "assignments",
        init_repo_files
      )

    def get_directory_student_template(self):
      return os.path.join(self.work_dir,GITLAB_COURSE_PROJECTS.student_template.path)

    def create_student_template(self):
      self.student_template_project, created_student_template_project = self.create_repository(
        self.get_directory_student_template(), 
        GITLAB_COURSE_PROJECTS.student_template, 
        self.course_group, 
        "student-template")

    def set_permission(self, project_or_group: Project | Group, user_id: str | int, access_level: int):
      try:
        project_or_group.members.create({
          "user_id": user_id,
          "access_level": access_level
        })
        print(f"Access {access_level} to {project_or_group.path} granted")
      except:
        try:
          member = project_or_group.members.get(user_id)
          member.access_level = access_level
          member.save()
          print(f"Access {access_level} to {project_or_group.path} granted")
        except Exception as e:
          print(f"Access {access_level} to {project_or_group.path} NOT granted {str(e)}")

    def create_course_release(self) -> list[str]:
      dir_testing = self.get_directory_testing()
      dir_reference = self.get_directory_reference()
      dir_student_template = self.get_directory_student_template()

      error_log = []

      if not os.path.exists(dir_student_template):
        error_dir_student_template = f"The directory [{dir_student_template}] does not exist."
        print(error_dir_student_template)
        error_log.append(error_dir_student_template)

      if not os.path.exists(dir_reference):
        error_dir_reference = f"The directory [{dir_reference}] does not exist."
        print(error_dir_reference)
        error_log.append(error_dir_reference)

      if not os.path.exists(dir_testing):
        error_dir_testing = f"The directory [{dir_testing}] does not exist."
        print(error_dir_testing)
        error_log.append(error_dir_testing)

      if len(error_log) > 0:
        return error_log
      
      version_identifier = git_version_identifier(dir_testing)

      try:
        release_info = release_course(dir_testing, dir_student_template)
        release_info2 = release_course(dir_testing, dir_reference)

        error_log = release_info.error_log + release_info2.error_log
        if len(error_log) > 0:
          print(f"Release [FAILED]")
          print(error_log)
        else:
          print(f"Release [SUCCEEDED]")

          try:
            cc_get: list[CourseContentTypeCreate] = []

            for it in release_info.course_meta.contentTypes or []:
              cc_get.append(
                CourseContentTypeCreate(
                  course_content_kind_id=it.kind,
                  slug=it.slug,
                  title=it.title,
                  description=it.description,
                  properties=it.properties,
                  course_id=str(self.course.id),
                  color=it.color))

            course_update = CourseUpdate(
                title=release_info.course_meta.title,
                description=release_info.course_meta.description,
                version_identifier=version_identifier
              )

            course_released = CustomClient(url_base=self.api_config.url,auth=(self.api_config.user,self.api_config.password)) \
              .update(f"system/release/courses/{self.course.id}/callback",
                      CourseReleaseUpdate(course=course_update,course_content_types=cc_get).model_dump(exclude_unset=True))

            print(f"course_released = {course_released}")

            if course_released == None or course_released == False:
              raise Exception("Course update @ database failed")

            git_repo_commit(dir_student_template, f"system release: course")
            git_repo_commit(dir_reference, f"system release: course")
          except Exception as e:
            print(e)
            error_log.append(e.args)

        return error_log

      except Exception as e:
        print(f"Release [FAILED] | {str(e)}")
        error_log.append(str(e))
        return error_log

    def create_release(self, release_dir: str) -> list[str]:

      dir_testing = self.get_directory_testing()
      dir_reference = self.get_directory_reference()
      dir_student_template = self.get_directory_student_template()

      error_log = []

      if not os.path.exists(dir_student_template):
        error_dir_student_template = f"The directory [{dir_student_template}] does not exist."
        print(error_dir_student_template)
        error_log.append(error_dir_student_template)

      if not os.path.exists(dir_reference):
        error_dir_reference = f"The directory [{dir_reference}] does not exist."
        print(error_dir_reference)
        error_log.append(error_dir_reference)

      if not os.path.exists(dir_testing):
        error_dir_testing = f"The directory [{dir_testing}] does not exist."
        print(error_dir_testing)
        error_log.append(error_dir_student_template)

      version_identifier = git_version_identifier(dir_testing)

      path, parent_path = directory_path_to_db_path_and_parent_path(release_dir)
      position = directory_path_to_position(release_dir)
      
      if parent_path != None:
        parent_course_content = get_course_content_from_path_api(self.api_config, str(self.course.id), parent_path)

        if parent_course_content == None:
          error_release_dir_parts = f"The parent directory is not released yet."
          print(error_release_dir_parts)
          error_log.append(error_release_dir_parts)
          return error_log
        elif parent_course_content.course_content_type.course_content_kind_id == "assignment":
          error_release_dir_parts = f"The parent directory is an assignment. Assignments could not have underlying CourseContents"
          print(error_release_dir_parts)
          error_log.append(error_release_dir_parts)
          return error_log

        print(f"parent_course_content = {parent_course_content}")
      
      element = get_course_content_from_path_api(self.api_config, str(self.course.id), path)

      if element != None and element.version_identifier == version_identifier:
        error_same_commit = f"The CourseContent is already released. Commit hash [{version_identifier}]"
        print(error_same_commit)
        error_log.append(error_same_commit)
        return error_log
      
      course_content_kind = check_realease_course_content_type(dir_testing,release_dir)

      try:
        if course_content_kind == "assignment":
          print("course_content_kind == assignment")
          release_info = release_assignment(dir_testing, dir_student_template, release_dir)
          release_info2 = release_assignment_reference(dir_testing, dir_reference, release_dir)

          execution_backend = get_execution_backend_from_slug_api(self.api_config, release_info.execution_backend_slug)

          if execution_backend == None:
            execution_backend_slug_error = f"Execution backend with slug {release_info.execution_backend_slug} does not exist"
            error_log.append(execution_backend_slug_error)
            print(execution_backend_slug_error)

          print(f"execution_backend = {execution_backend}")

          properties = CourseContentProperties(
            gitlab=GitLabConfig(directory=release_dir)
          )

          execution_backend_id = str(execution_backend.id)

        elif course_content_kind == "unit":
          print("course_content_kind == unit")
          release_info = release_unit(dir_testing, dir_student_template, release_dir)
          release_info2 = release_unit(dir_testing, dir_reference, release_dir)

          properties = CourseContentProperties(gitlab=GitLabConfig(
            directory=release_dir
          ))

          execution_backend_id = None
        else:
          print("NotImplementedError")
          raise NotImplementedError()
        
        error_log = release_info.error_log + release_info2.error_log
        if len(error_log) > 0:
          print(f"Release {release_dir} [FAILED]")
          print(error_log)
        else:
          print(f"Release {release_dir} [SUCCEEDED]")

          course_content_type = get_course_content_type_from_slug_api(self.api_config, release_info.course_content_type_slug, course_content_kind, self.course.id)
          print(f"course_content_type = {course_content_type}")

          if course_content_type == None:
            course_content_type_slug_error = f"CourseContentType with slug {release_info.course_content_type_slug} does not exist"
            error_log.append(course_content_type_slug_error)
            print(course_content_type_slug_error)
            return error_log
          
          if course_content_type.course_content_kind_id != release_info.course_content_kind_id:
            course_content_type_missmatch_error = "CourseContentType type and CourseContent type does not match"
            error_log.append(course_content_type_missmatch_error)
            print(course_content_type_missmatch_error)
            return error_log

          try:

            course_content_create = CourseContentCreate(
                path=path,
                position=position,
                title=release_info.title,
                description=release_info.description,
                course_id=str(self.course.id),
                course_content_type_id=str(course_content_type.id),
                version_identifier=release_info.version_identifier,
                properties=properties,
                max_group_size=release_info.max_group_size,
                max_submissions=release_info.max_submissions,
                max_test_runs=release_info.max_test_runs,
                execution_backend_id=execution_backend_id
              )

            course_content_released = validate_course_content_api(self.api_config, course_content_create)
            print(f"course_content_released = {course_content_released}")

            if course_content_released == None:
              raise Exception(f"{path} create @ database failed")

            git_repo_commit(dir_student_template, f"system release: {release_dir}")
            git_repo_commit(dir_reference, f"system release: {release_dir}")
          except Exception as e:
            print(e)
            error_log.append(e.args)

        return error_log

      except Exception as e:
        print(f"Release {release_dir} [FAILED] | {str(e)}")
        error_log.append(str(e))
        return error_log

    def get_directory_reference(self):
      return os.path.join(self.work_dir,GITLAB_COURSE_PROJECTS.reference.path)

    def create_reference(self):
      self.reference_project, created_reference_project = self.create_repository(
        self.get_directory_reference(), 
        GITLAB_COURSE_PROJECTS.reference, 
        self.course_group, 
        "reference")

    def create_project_documents(self,parent_group,path_prefix,id):

      dir_docs = os.path.join(self.work_dir,"documents",path_prefix,str(id))

      self.create_repository(
        dir_docs, 
        GITLAB_COURSE_PROJECTS.documents, 
        parent_group, 
        "documents")

      destination = os.path.join(settings.API_LOCAL_STORAGE_DIR,"documents",path_prefix)

      if os.path.exists(destination):
        shutil.rmtree(destination)

      ignore_dirs = [".git"]
      ignore_files = [".gitignore","README.md"]
      ignore_file_exts = [".key"]

      for root, dirs, files in os.walk(dir_docs):
        relative_path = os.path.relpath(root, dir_docs)
        dest_path = os.path.join(destination, relative_path)

        if relative_path in ignore_dirs:
          continue
        
        if relative_path.endswith(tuple(ignore_file_exts)):
          continue

        os.makedirs(dest_path, exist_ok=True)

        for file in files:
          if file not in ignore_files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_path, file)
            shutil.copy2(src_file, dest_file)

    def create_repository(self, directory: str, project_config: GitlabGroupProjectConfig, parent_group: Group, init_files_directory: str, create_repo_contents: Any = None):

      gitlab_project, created_gitlab_project = self.create_or_get_project(
        project_config,
        parent_group
      )

      misc_dir = os.path.join(settings.API_LOCAL_STORAGE_DIR,"defaults/deployments",init_files_directory)

      try:
        description = read_file(os.path.join(misc_dir,"description.md"))
        gitlab_project.description = description
        gitlab_project.save()
      except Exception as e:
        print(f"{gitlab_project.path} | creating or editing description failed | {str(e)}")

      if not git_repo_exist(directory):

        if not os.path.exists(directory):
          os.makedirs(directory)
        
        if created_gitlab_project:
          _copy_files(misc_dir,directory,_repo_init_file_mapper)
          create_repo_contents() if create_repo_contents != None else None

        git_repo_create(directory, gitlab_project.http_url_to_repo, self.gitlab_token)
        
      else:
        git_repo_pull(directory)

      return gitlab_project, created_gitlab_project