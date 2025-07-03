from gitlab import Gitlab, GitlabHttpError

def gitlab_unprotect_branches(gitlab: Gitlab, id: str | int, branch_name):
  try:
    response = gitlab.http_delete(path=f"/projects/{id}/protected_branches/{branch_name}")
    print(f"deleted branch {branch_name} of project {id}")
  except GitlabHttpError as e:
    if e.response_code == 404:
      print(f"Already unprotected branch '{branch_name}' [projectId={id}]")
    else:
      raise e

def gitlab_fork_project(gitlab: Gitlab, fork_id: str | int, dest_path: str, dest_name: str, namespace_id: str | int):
  try:
    gitlab.http_post(path=f"/projects/{fork_id}/fork",
          post_data={
            "path": dest_path,
            "name": dest_name,
            "namespace_id": namespace_id
          })
  except Exception as e:
    print(f"[gitlab_fork_project]{str(e)}")
    raise e

def gitlab_current_user(gitlab: Gitlab):
    return gitlab.http_get(path=f"/user")