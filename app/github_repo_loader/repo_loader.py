import os
from urllib.parse import urlparse

from github import Github
from dotenv import load_dotenv
from app.parser.language import ALLOWED_EXTENSIONS, IGNORE_DIRS, EXTENSION_TO_LANGUAGE

load_dotenv()


class GitHubRepoLoader:

    def __init__(self):
        token = os.getenv("GITHUB_AUTH")

        if not token:
            raise ValueError("GITHUB_AUTH not found")

        self.github = Github(token)

    def get_repositories(self, repo_url):
        parsed = urlparse(repo_url.strip())

        if parsed.netloc.lower() != "github.com":
            raise ValueError("Please enter a valid GitHub repository URL.")

        parts = [part for part in parsed.path.strip("/").split("/") if part]

        if len(parts) < 2:
            raise ValueError("GitHub URL must include an owner and repository name.")

        owner = parts[0]
        repo_name = parts[1].removesuffix(".git")

        return self.github.get_repo(f"{owner}/{repo_name}")

    def get_files(self, repo):

        files = []

        def traverse(path):

            contents = repo.get_contents(path)

            for item in contents:

                if item.type == "dir":

                    if item.name in IGNORE_DIRS:
                        continue

                    traverse(item.path)

                elif item.type == "file":

                    extension = "." + item.name.split(".")[-1].lower()
                    file_name = item.path.split("/")[-1]

                    if extension in ALLOWED_EXTENSIONS:

                        language = EXTENSION_TO_LANGUAGE[extension]

                        code = item.decoded_content.decode("utf-8")

                        files.append({
                            "language": language,
                            "path": item.path,
                            "file_name": file_name,
                            "code": code
                        })

        # This must be outside traverse()
        traverse("")

        return files

    def load_repository(self, repo):
        return self.get_files(repo)
