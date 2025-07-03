import os
import yaml
import shutil
from pydantic import BaseModel
from ctutor_backend.generator.git_helper import git_version_identifier
from ctutor_backend.interface.deployments import DeploymentFactory, CodeAbilityCourseMeta, CodeAbilityMeta, CodeAbilityReleaseMeta, CodeAbilityUnitMeta

def convert_content_to_release_directory(source, destination):
    content_dir = os.path.join(source, "content")

    if os.path.exists(content_dir):

        readme_file_en = os.path.join(content_dir,"index.md")

        if os.path.exists(readme_file_en):
            shutil.copyfile(readme_file_en, os.path.join(destination, "README.md"))

        # TODO: generalize this for each language found in the directory
        readme_file_de = os.path.join(content_dir,"index_de.md")

        if os.path.exists(readme_file_de):
            shutil.copyfile(readme_file_de, os.path.join(destination, "README_de.md"))

        media_files_dir = os.path.join(content_dir,"mediaFiles")

        if os.path.exists(media_files_dir):

            media_files_dest_dir = os.path.join(destination, "mediaFiles")

            if os.path.exists(media_files_dest_dir):
                shutil.rmtree(media_files_dest_dir)

            shutil.copytree(media_files_dir,media_files_dest_dir,dirs_exist_ok=True)
    else:
        with open(os.path.join(destination, "README.md"), "w") as file:
            file.write("# readme")

def status_meta_file(path: str):
    return os.path.exists(os.path.join(path,"meta.yaml"))

def status_test_file(path: str):
    return os.path.exists(os.path.join(path,"test.yaml"))

def meta_file_read(path: str):
    with open(os.path.join(path,"meta.yaml")) as file:
        meta_obj = yaml.safe_load(file)
        properties = meta_obj["properties"]
        student_submission_files = properties["studentSubmissionFiles"]
        additional_files = properties["additionalFiles"]
        student_templates  = properties["studentTemplates"]

        # just a hack solution. Should be fixed in future releases
        to_create = student_submission_files
        to_copy = additional_files
        to_copy_from_templates = student_templates

        return to_create, to_copy, to_copy_from_templates

class CourseContentReleaseInfo(BaseModel):
    course_content_kind_id: str | None = None
    execution_backend_slug: str | None = None
    course_content_type_slug: str | None = None
    version_identifier: str = ""
    error_log: list[str] = []
    title: str | None = None
    description : str | None = None
    max_test_runs: int | None = None
    max_submissions: int | None = None
    max_group_size: int | None = None

def check_realease_course_content_type(source_dir, course_content_dir) -> str:
    error_log = []

    source_example = os.path.join(source_dir, course_content_dir)

    if status_meta_file(source_example) == False:
        error_meta_file = f"meta.yaml not found. Directory is not a valid example."
        print(error_meta_file)
        error_log.append(error_meta_file)
    
    # TODO: REFACTORING
    try:
        course_content_meta: CodeAbilityReleaseMeta = DeploymentFactory.read_deployment_from_file(CodeAbilityReleaseMeta, os.path.join(source_example,"meta.yaml"))
        
        if course_content_meta.kind.lower() != "assignment" and course_content_meta.kind.lower() != "unit":
            error_log.append(f"Wrong meta.yaml field [kind={course_content_meta.kind}]. Expected value 'assignment'")

        if course_content_meta.kind.lower() == "assignment":
            if status_test_file(source_example) == False:
                error_test_file = f"test.yaml not found. Directory is not a valid example."
                print(f"test.yaml not found. Directory is not a valid example.")
                error_log.append(error_test_file)
        
    except Exception as e:
        print(e.args)
        print(e)
        error_log.append(e.args)

    if len(error_log) > 0:
        return error_log
    
    return course_content_meta.kind.lower()

class CourseReleaseInfo(BaseModel):
    error_log: list[str] = []
    course_meta: CodeAbilityCourseMeta | None = None


def release_assignment_reference(source_dir, destination_dir, assignment_dir) -> CourseContentReleaseInfo:
    error_log = []

    source_example = os.path.join(source_dir, assignment_dir)
    destination_example = os.path.join(destination_dir, assignment_dir)

    os.makedirs(destination_example, exist_ok=True)

    to_create, to_copy, to_copy2 = meta_file_read(source_example)

    for tc in to_create + to_copy:
        if os.path.exists(os.path.join(source_example, tc)):
            shutil.copyfile(os.path.join(source_example, tc), os.path.join(destination_example, tc))
        else:
            print(f"File does not exist {os.path.join(source_example, tc)}")

    try:
        convert_content_to_release_directory(source_example,destination_example)

    except Exception as e:
        print(e.args)
        print(e)
        error_log.append(e.args)

    return CourseContentReleaseInfo(error_log=error_log)

def release_assignment(source_dir, destination_dir, assignment_dir) -> CourseContentReleaseInfo:

    error_log = []

    source_example = os.path.join(source_dir, assignment_dir)
    destination_example = os.path.join(destination_dir, assignment_dir)

    if status_meta_file(source_example) == False:
        error_meta_file = f"meta.yaml not found. Directory is not a valid example."
        print(error_meta_file)
        error_log.append(error_meta_file)

    if status_test_file(source_example) == False:
        error_test_file = f"test.yaml not found. Directory is not a valid example."
        print(f"test.yaml not found. Directory is not a valid example.")
        error_log.append(error_test_file)
    
    try:
        assignment_meta: CodeAbilityMeta = DeploymentFactory.read_deployment_from_file(CodeAbilityMeta, os.path.join(source_example,"meta.yaml"))
        
        if assignment_meta.kind.lower() != "assignment":
            error_log.append(f"Wrong meta.yaml field [kind={assignment_meta.kind}]. Expected value 'assignment'")
        if assignment_meta.type == None or assignment_meta.type == "":
            error_log.append(f"Wrong meta.yaml field [type={assignment_meta.type}]. Expected value should be an existing assignment_type slug")

    except Exception as e:
        print(e.args)
        print(e)
        error_log.append(e.args)

    if len(error_log) > 0:
        return CourseContentReleaseInfo(error_log=error_log)

    os.makedirs(destination_example, exist_ok=True)

    to_create, to_copy, to_copy2 = meta_file_read(source_example)
    print(f"[START] Files to copy from templates")
    for tc in to_copy2:
        tc_splitted = os.path.split(tc)
        tc_dest = os.path.join(*tc_splitted[1:])
        if os.path.exists(os.path.join(source_example, tc)):
            shutil.copyfile(os.path.join(source_example, tc), os.path.join(destination_example, tc_dest))
            print(f"{os.path.join(source_example, tc)} -> {os.path.join(destination_example, tc_dest)}")
        else:
            print(f"File does not exist {os.path.join(source_example, tc)}")
    print(f"[END] Files to copy from templates")

    for tc in to_create:
        if not os.path.exists(os.path.join(destination_example, tc)):
            with open(os.path.join(destination_example, tc), "w") as file:
                pass

    for tc in to_copy:
        if os.path.exists(os.path.join(source_example, tc)):
            shutil.copyfile(os.path.join(source_example, tc), os.path.join(destination_example, tc))
        else:
            print(f"File does not exist {os.path.join(source_example, tc)}")

    try:
        convert_content_to_release_directory(source_example,destination_example)

        return CourseContentReleaseInfo(
            course_content_type_slug=assignment_meta.type, 
            execution_backend_slug=assignment_meta.properties.executionBackend.slug, 
            version_identifier=git_version_identifier(source_dir),
            course_content_kind_id="assignment",
            title=assignment_meta.title,
            description=assignment_meta.description,
            max_test_runs=assignment_meta.properties.maxTestRuns,
            max_submissions=assignment_meta.properties.maxSubmissions,
            max_group_size=assignment_meta.properties.maxGroupSize if assignment_meta.properties.maxGroupSize != None else 1
        )
    
    except Exception as e:
        print(e.args)
        print(e)
        error_log.append(e.args)
    
    return CourseContentReleaseInfo(error_log=error_log)

def release_unit(source_dir, destination_dir, unit_dir) -> CourseContentReleaseInfo:

    error_log = []

    source_unit = os.path.join(source_dir, unit_dir)
    destination_unit = os.path.join(destination_dir, unit_dir)

    if status_meta_file(source_unit) == False:
        error_meta_file = f"meta.yaml not found. Directory is not a valid unit."
        print(error_meta_file)
        error_log.append(error_meta_file)

    try:
        unit_meta: CodeAbilityUnitMeta = DeploymentFactory.read_deployment_from_file(CodeAbilityUnitMeta, os.path.join(source_unit,"meta.yaml"))
        
        if unit_meta.kind.lower() != "unit":
            error_log.append(f"Wrong meta.yaml field [kind={unit_meta.kind}]. Expected value 'unit'")
        if unit_meta.type == None or unit_meta.type == "":
            error_log.append(f"Wrong meta.yaml field [type={unit_meta.kind}]. Expected value should be an existing unit_type slug")

        if len(error_log) > 0:
            return CourseContentReleaseInfo(error_log=error_log)

        if not os.path.exists(destination_unit):
            os.mkdir(destination_unit)

        convert_content_to_release_directory(source_unit,destination_unit)

        return CourseContentReleaseInfo(
            course_content_type_slug=unit_meta.type,
            version_identifier=git_version_identifier(source_dir),
            course_content_kind_id="unit",
            title=unit_meta.title,
            description=unit_meta.description,
            max_test_runs=None,
            max_submissions=None,
            max_group_size=None
        )
    except Exception as e:
        print(e.args)
        print(e)
        error_log.append(e.args)

    return CourseContentReleaseInfo(error_log=error_log)

def release_course(source_dir, destination_dir) -> CourseReleaseInfo:

    error_log = []

    source_course = source_dir
    destination_course = destination_dir

    if status_meta_file(source_course) == False:
        error_meta_file = f"meta.yaml not found. Directory is not a valid course."
        print(error_meta_file)
        error_log.append(error_meta_file)

    if len(error_log) > 0:
        return error_log

    try:
        course_meta: CodeAbilityCourseMeta = DeploymentFactory.read_deployment_from_file(CodeAbilityCourseMeta, os.path.join(source_course,"meta.yaml"))
        
        convert_content_to_release_directory(source_course,destination_course)

        if course_meta.kind.lower() == "course":
            error_log.append(f"Wrong meta.yaml field [kind={course_meta.kind}]. Expected value 'course'")

        return CourseReleaseInfo(course_meta=course_meta)

    except Exception as e:
        print(e.args)
        print(e)
        error_log.append(e.args)

    if len(error_log) > 0:
        return CourseReleaseInfo(error_log=error_log)