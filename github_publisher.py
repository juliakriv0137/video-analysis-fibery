import os
import requests
import base64
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class GitHubPublisher:
    def __init__(self, token):
        self.token = token
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def create_repo(self, name, description="Video Analysis System"):
        """Create a new GitHub repository"""
        try:
            url = f"{self.api_base}/user/repos"
            data = {
                "name": name,
                "description": description,
                "private": False,
                "auto_init": True,
                "has_issues": True,
                "has_projects": True,
                "has_wiki": True
            }
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error creating repository: {str(e)}")
            raise

    def upload_file(self, repo_name, file_path, commit_message="Add file via API"):
        """Upload a file to the repository"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return None

            with open(file_path, 'rb') as file:
                content = file.read()
                content_b64 = base64.b64encode(content).decode('utf-8')

            # Try to get existing file
            url = f"{self.api_base}/repos/{self.get_user()['login']}/{repo_name}/contents/{Path(file_path).name}"
            try:
                existing_file = requests.get(url, headers=self.headers)
                existing_file.raise_for_status()
                sha = existing_file.json().get('sha')
            except:
                sha = None

            data = {
                "message": commit_message,
                "content": content_b64
            }
            if sha:
                data["sha"] = sha

            response = requests.put(url, headers=self.headers, json=data)
            response.raise_for_status()
            logger.info(f"Successfully uploaded {file_path}")
            return response.json()
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {str(e)}")
            return None

    def get_user(self):
        """Get authenticated user information"""
        try:
            response = requests.get(f"{self.api_base}/user", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            raise

def publish_to_github(repo_name="video-analysis-fibery"):
    """Publish all project files to GitHub"""
    try:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise ValueError("GitHub token not found in environment variables")

        publisher = GitHubPublisher(token)

        # Create repository
        try:
            repo = publisher.create_repo(repo_name, 
                description="Video analysis system with Fibery integration for automated content processing")
            logger.info(f"Created repository: {repo['html_url']}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 422:  # Repository already exists
                logger.info(f"Repository {repo_name} already exists, continuing with file uploads")
            else:
                raise

        # Files to upload
        files = [
            "main.py",
            "video_processor.py",
            "ai_analyzer.py",
            "app.py",
            "github_publisher.py",
            "README.md",
            "FIBERY_SETUP.md",
            "CONTRIBUTING.md",
            "CONTRIBUTORS.md",
            ".gitignore",
            ".github/workflows/analyze-video.yml"
        ]

        # Upload each file
        success_count = 0
        for file in files:
            if publisher.upload_file(repo_name, file):
                success_count += 1
                logger.info(f"Uploaded {file}")

        logger.info(f"Successfully uploaded {success_count} out of {len(files)} files")

        if repo.get('html_url'):
            return repo['html_url']
        return f"https://github.com/{publisher.get_user()['login']}/{repo_name}"

    except Exception as e:
        logger.error(f"Error publishing to GitHub: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    url = publish_to_github()
    print(f"Repository published at: {url}")