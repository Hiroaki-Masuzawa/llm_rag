import os
import subprocess
from extract_docstrings import extract_from_directory

def clone_repos(repo_file='repo.txt', clone_dir='repos'):
    os.makedirs(clone_dir, exist_ok=True)

    with open(repo_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue

            url = parts[0]
            branch = parts[1] if len(parts) > 1 else "main"
            repo_name = url.rstrip('/').split('/')[-1].replace('.git', '')
            dest_path = os.path.join(clone_dir, repo_name)

            if os.path.exists(dest_path):
                print(f"🔄 Updating {repo_name} (branch: {branch})...")
                try:
                    subprocess.run(["git", "fetch"], cwd=dest_path, check=True)
                    subprocess.run(["git", "checkout", branch], cwd=dest_path, check=True)
                    subprocess.run(["git", "pull", "origin", branch], cwd=dest_path, check=True)
                except subprocess.CalledProcessError as e:
                    print(f"⚠️  Failed to update {repo_name}: {e}")
                    continue
            else:
                print(f"⬇️  Cloning {url} (branch: {branch}) into {dest_path}")
                try:
                    subprocess.run(["git", "clone", "--branch", branch, url, dest_path], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to clone {url}: {e}")
                    continue

def extract_all_docstrings():
    CLONE_DIR = "repos"
    all_docs = []
    for repo in os.listdir(CLONE_DIR):
        repo_path = os.path.join(CLONE_DIR, repo)
        if os.path.isdir(repo_path):
            docs = extract_from_directory(repo_path)
            all_docs.extend(docs)
    return all_docs
