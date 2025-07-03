import os
import subprocess

def git_repo_exist(directory):
  try:
    return_code = subprocess.run(f"git status",cwd=os.path.abspath(directory),shell=True)

    if return_code.returncode == 0:
        return True
    return False
  except:
      return False
  
def git_http_url_to_ssh_url(http_url_to_repo: str, token: str):

  http_type = ""
  if http_url_to_repo.startswith("http://"):
    repo_url = http_url_to_repo.replace("http://","")
    http_type = "http://"
  elif http_url_to_repo.startswith("https://"):
    repo_url = http_url_to_repo.replace("https://","")
    http_type = "https://"

  return f"{http_type}x-token-auth:{token}@{repo_url}"

def git_clone(directory: str, http_url_to_repo: str, token: str):
    ssh_url = git_http_url_to_ssh_url(http_url_to_repo, token)
    return subprocess.check_call(f"git clone {ssh_url} {directory}", cwd=os.path.abspath(directory), shell=True)

def git_checkout(directory: str, commit: str):
    return subprocess.check_call(f"git checkout {commit}", cwd=os.path.abspath(directory), shell=True)

def git_pull(directory: str):
    return subprocess.check_call(f"git pull", cwd=os.path.abspath(directory), shell=True)

def git_fetch_all(directory: str):
    return subprocess.check_call(f"git fetch --all", cwd=os.path.abspath(directory), shell=True)

def clone_or_pull_and_checkout(directory, repo_url, token, commit):
    
  try:
      if not os.path.exists(directory):
        print(f"Cloning {repo_url} into {directory}...")

        if not os.path.exists(directory):
          os.makedirs(directory,exist_ok=True)

        git_clone(directory, repo_url, token)

      elif os.path.exists(directory) and not os.path.exists(os.path.join(directory,".git")):

        os.removedirs(directory)

        print(f"Cloning {repo_url} into {directory}...")

        if not os.path.exists(directory):
          os.makedirs(directory,exist_ok=True)

        git_clone(directory, repo_url, token)
      else:
        git_checkout(directory,"main")
        git_fetch_all(directory)
         
      return git_checkout(directory,commit)

  except subprocess.CalledProcessError as e:
      print(f"An error occurred while cloning: {e}")
      return

def git_repo_create(directory: str, http_url_to_repo: str, token: str):

  # https://docs.gitlab.com/ee/api/projects.html
  # http_url_to_repo mit token vermischen

  # apiProject.http_url_to_repo

  repo_url = git_http_url_to_ssh_url(http_url_to_repo, token)

  subprocess.check_call(f"git init --initial-branch=main", cwd=os.path.abspath(directory), shell=True)
  subprocess.check_call(f"git remote add origin {repo_url}", cwd=os.path.abspath(directory), shell=True)
  subprocess.run(f"git pull --set-upstream origin main", cwd=os.path.abspath(directory), shell=True)

  subprocess.check_call(f"git add .", cwd=os.path.abspath(directory), shell=True)
      
  exec = subprocess.run(f'git commit -m "system release: from template"', cwd=os.path.abspath(directory), shell=True)
  if exec.returncode != 0:
      return

  subprocess.run(f"git push --set-upstream origin main", cwd=os.path.abspath(directory), shell=True)

def git_repo_pull(directory):
  subprocess.run(f"git pull", cwd=os.path.abspath(directory), shell=True)

def git_repo_commit(directory: str, commit_message: str, branch: str = "main"):
  subprocess.run(f"git add .", cwd=os.path.abspath(directory),shell=True)
  exec = subprocess.run(f'git commit -m "{commit_message}"', cwd=os.path.abspath(directory), shell=True)
  if exec.returncode != 0:
      return
  subprocess.check_output(f"git push --set-upstream origin {branch}", cwd=os.path.abspath(directory), shell=True)

def git_version_identifier(directory: str) -> str:
  return subprocess.check_output(f"git rev-parse --verify HEAD", cwd=os.path.abspath(directory), shell=True).decode().strip()

def git_push_set_upstream(directory, branch):
  exec = subprocess.run(f"git push --set-upstream origin {branch}", cwd=os.path.abspath(directory), shell=True, stdout=subprocess.PIPE)

  return True if exec.returncode == 0 else False

def check_branch_is_available(directory, branch):
  exec = subprocess.run(f"git ls-remote --exit-code origin {branch}", cwd=os.path.abspath(directory), shell=True, stdout=subprocess.PIPE)

  return True if exec.returncode == 0 else False

def checkout_branch(directory, branch):

  if not check_branch_is_available(directory,branch):
    exec = subprocess.run(f"git checkout -b {branch}", cwd=os.path.abspath(directory), shell=True, stdout=subprocess.PIPE)

    if exec.returncode == 0:
      return True
    else:
      exec = subprocess.run(f"git checkout {branch}", cwd=os.path.abspath(directory), shell=True, stdout=subprocess.PIPE)

      return True if exec.returncode == 0 else False

  else:
    exec = subprocess.run(f"git checkout {branch}", cwd=os.path.abspath(directory), shell=True, stdout=subprocess.PIPE)

    return True if exec.returncode == 0 else False