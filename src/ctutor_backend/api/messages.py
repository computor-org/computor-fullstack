import os
import json
from gitlab import Gitlab
from gitlab.v4.objects import ProjectMergeRequest
from ctutor_backend.api.exceptions import BadRequestException, InternalServerException, NotFoundException
from aiocache import Cache
from ctutor_backend.interface.auth import GLPAuthConfig
from ctutor_backend.redis import get_redis_client

def list_submission_mergerequests(gitlab: Gitlab, project_path: str):

  if project_path == None:
    raise NotFoundException()
  
  projects = gitlab.projects.list(search=project_path,search_namespaces=True)

  if len(projects) == 0:
    raise BadRequestException(detail="[list_submission_mergerequests] No submission project available.")
  elif len(projects) > 1:
    raise InternalServerException(detail="[list_submission_mergerequests] More than one submission project available.")

  project = projects[0]

  return project.mergerequests.list(get_all=True)

async def get_submission_mergerequest(glp_auth: GLPAuthConfig, user_id: str, project_path: str, assignment_id: str, assignment_path: str) -> ProjectMergeRequest:

  gitlab = Gitlab(url=glp_auth.url, private_token=glp_auth.token)

  cache = await get_redis_client()

  cache_key = f"{user_id}:merge_request:{assignment_id}"
  cached_merge_request = await cache.get(cache_key)

  if cached_merge_request:
    merge_request = ProjectMergeRequest(gitlab.projects,json.loads(cached_merge_request))

  else:
    mergerequests = list_submission_mergerequests(gitlab,project_path)
    source_branch=f"submission/{assignment_path}"
    merge_request = next((x for x in mergerequests if x.source_branch == source_branch and x.title.lower() == f"submission: {assignment_path.lower()}"), None)

    if merge_request != None:
      await cache.set(cache_key, json.dumps(merge_request.asdict()), ttl=1800)

  return merge_request