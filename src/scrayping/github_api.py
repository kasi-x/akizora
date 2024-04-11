import base64
import os
from typing import Annotated
from typing import Literal
from typing import TypedDict

import requests
import structlog
from pydantic import AnyUrl
from pydantic import BaseModel
from pydantic import UrlConstraints
from structlog.stdlib import BoundLogger

from utils.logger_config import configure_logger

GithubApiUrlDomain = "https://api.github.com"

GithubApiUrl = Annotated[AnyUrl, UrlConstraints(allowed_schemes=[GithubApiUrlDomain])]


def build_github_api_url(subdirectory: str) -> GithubApiUrl:
    return GithubApiUrlDomain + subdirectory


class FileInfo(TypedDict):
    """{'path': 'chapter-1.xhtml',
    'mode': '100644',
    'type': 'blob',
    'sha': '5a6be444aff865b840702deeec4ef6c2cdeacf87',
    'size': 8003,
    'url': 'https://api.github.com/repos/standardebooks/john-maynard-keynes_the-economic-consequences-of-the-peace/git/blobs/5a6be444aff865b840702deeec4ef6c2cdeacf87'}.
    """

    path: str
    mode: str
    type: Literal["blob", "tree"]
    size: str
    url: str


class ContentData(TypedDict):
    r"""{
      "sha": "31395a749154bf5fc9a234da87c5977b14e4ea50",
      "node_id": "B_kwDOLjmri9oAKDMxMzk1YTc0OTE1NGJmNWZjOWEyMzRkYTg3YzU5NzdiMTRlNGVhNTA",
      "size": 795,
      "url": "https://api.github.com/repos/standardebooks/john-maynard-keynes_the-economic-consequences-of-the-peace/git/blobs/31395a749154bf5fc9a234da87c5977b14e4ea50",
      "content": "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz4KPGh0bWwg\neG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkveGh0bWwiIHhtbG5zOmVw\ndWI9Imh0dHA6Ly93d3cuaWRwZi5vcmcvMjAwNy9vcHMiIGVwdWI6cHJlZml4\nPSJ6Mzk5ODogaHR0cDovL3d3dy5kYWlzeS5vcmcvejM5OTgvMjAxMi92b2Nh\nYi9zdHJ1Y3R1cmUvLCBzZTogaHR0cHM6Ly9zdGFuZGFyZGVib29rcy5vcmcv\ndm9jYWIvMS4wIiB4bWw6bGFuZz0iZW4tVVMiPgoJPGhlYWQ+CgkJPHRpdGxl\nPlRpdGxlcGFnZTwvdGl0bGU+CgkJPGxpbmsgaHJlZj0iLi4vY3NzL2NvcmUu\nY3NzIiByZWw9InN0eWxlc2hlZXQiIHR5cGU9InRleHQvY3NzIi8+CgkJPGxp\nbmsgaHJlZj0iLi4vY3NzL3NlLmNzcyIgcmVsPSJzdHlsZXNoZWV0IiB0eXBl\nPSJ0ZXh0L2NzcyIvPgoJPC9oZWFkPgoJPGJvZHkgZXB1Yjp0eXBlPSJmcm9u\ndG1hdHRlciI+CgkJPHNlY3Rpb24gaWQ9InRpdGxlcGFnZSIgZXB1Yjp0eXBl\nPSJ0aXRsZXBhZ2UiPgoJCQk8aDEgZXB1Yjp0eXBlPSJ0aXRsZSI+VGhlIEVj\nb25vbWljIENvbnNlcXVlbmNlcyBvZiB0aGUgUGVhY2U8L2gxPgoJCQk8cD5C\neSA8YiBlcHViOnR5cGU9InozOTk4OmF1dGhvciB6Mzk5ODpwZXJzb25hbC1u\nYW1lIj5Kb2huIE1heW5hcmQgS2V5bmVzPC9iPi48L3A+CgkJCTxpbWcgYWx0\nPSIiIHNyYz0iLi4vaW1hZ2VzL3RpdGxlcGFnZS5zdmciIGVwdWI6dHlwZT0i\nc2U6aW1hZ2UuY29sb3ItZGVwdGguYmxhY2stb24tdHJhbnNwYXJlbnQiLz4K\nCQk8L3NlY3Rpb24+Cgk8L2JvZHk+CjwvaHRtbD4K\n",
      "encoding": "base64"
    }.
    """

    sha: str
    node_id: str
    size: int
    url: str
    content: str
    encoding: str


class RepositoryInfo(TypedDict):
    """{'name': 'a-a-milne_the-red-house-mystery',
    'url': 'https://github.com/standardebooks/a-a-milne_the-red-house-mystery',
    'owner': 'standardebooks',
    'description': 'Epub source for the Standard Ebooks edition of The Red House Mystery, by A. A. Milne'}.
    """

    name: str
    url: str
    owner: str
    description: str


class GithubApiManager:
    def __init__(self) -> None:
        self.logger = structlog.get_logger(__name__).bind(module="github_api")
        access_token = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]
        self.headers = {"Authorization": f"token {access_token}"}

    def _log_api_request(self, url: str, method="GET") -> None:
        self.logger.info("API Request", url=url, method=method)

    def _log_api_response(self, url: str, status_code: int, response_text: str = "") -> None:
        if status_code >= 400:
            self.logger.error(
                "API Request Failed", url=url, status_code=status_code, response_text=response_text
            )
        else:
            self.logger.debug("API Request Successful", url=url, status_code=status_code)

    def fetch_file_tree_info(self, file_tree_url: GithubApiUrl) -> list[FileInfo]:
        self._log_api_request(file_tree_url)
        response = requests.get(file_tree_url, headers=self.headers)
        self._log_api_response(file_tree_url, response.status_code, response.text)

        if response.status_code == 200:
            return response.json()["tree"]
        else:
            msg = "Failed to get tree info."
            raise Exception(msg)

    def fetch_single_file_content_data(self, file_api_url: GithubApiUrl) -> ContentData:
        self._log_api_request(file_api_url)
        response = requests.get(file_api_url, headers=self.headers)
        self._log_api_response(file_api_url, response.status_code, response.text)
        return response.json()

    def fetch_user_repositories(self, username: str) -> list[RepositoryInfo]:
        api_url = build_github_api_url(f"/users/{username}/repos")
        self._log_api_request(api_url)
        response = requests.get(api_url, headers=self.headers)
        self._log_api_response(api_url, response.status_code, response.text)

        if response.status_code == 200:
            repositories = []
            for repo_data in response.json():
                repositories.append(
                    RepositoryInfo(
                        name=repo_data["name"],
                        url=repo_data["html_url"],
                        owner=repo_data["owner"]["login"],
                        description=repo_data["description"],
                    )
                )
            return repositories
        else:
            msg = "Failed to get repositories."
            raise Exception(msg)

    def fetch_all_user_repositories(self, username: str) -> list[RepositoryInfo]:
        repositories: list[RepositoryInfo] = []
        api_url = build_github_api_url(f"/users/{username}/repos")
        while api_url:
            response = requests.get(api_url, headers=self.headers)
            if response.status_code == 200:
                repositories.extend(list(response.json()))
                link_header = response.headers.get("Link")
                if link_header:
                    links = link_header.split(",")
                    for link in links:
                        if 'rel="next"' in link:
                            # MAYBE: I don't need to validate link.
                            api_url = link.strip().split(";")[0][1:-1]
                            break
                    else:
                        api_url = None
                else:
                    api_url = None

            else:
                msg = "Failed to get repositories."
                raise Exception(msg)

        return repositories

    def valivade_url(self, url: str, author: str, title: str) -> GithubApiUrl:
        # WARNING: This is a very naive implementation.
        # WARNING: If attecker pushes injection attack file at master branch, this implementation will be vulnerable.
        # WARNING: If author or title contains "/", this implementation will be vulnerable.
        # WARNING: If author or title is not ASCII, you need to encode it to ASCII.
        # EXAMPLE: https://api.github.com/repos/standardebooks/john-maynard-keynes_the-economic-consequences-of-the-peace/git/blobs/fdde73b43549194faeac89a38adee574ab378511
        if url.startswith(GithubApiUrlDomain + f"/repos/{author}/{title}"):
            return url
        else:
            expected = GithubApiUrlDomain + f"/repos/{author}/{title}"
            self.logger.error("Invalid URL.", url=url, expected=expected)
            msg = f"Invalid URL. Expected: {expected}, Actual: {url}"
            raise Exception(msg)


# test_case
def main():
    configure_logger()
    logger = structlog.get_logger(__name__).bind(module="github_api_tutorial")

    title = "john-maynard-keynes_the-economic-consequences-of-the-peace"
    github = GithubApiManager()
    text_file_tree_url = (
        f"https://api.github.com/repos/standardebooks/{title}/git/trees/master:src/epub/text"
    )
    tree_info = github.fetch_file_tree_info(text_file_tree_url)
    for file_info in tree_info:
        try:
            if file_info["type"] != "blob":
                logger.error("File type is not blob.", file_path=file_info["path"])
                msg = "File type is not blob."
                raise Exception(msg)
            url = github.valivade_url(file_info["url"], "standardebooks", title)
            content_data = github.fetch_single_file_content_data(url)
            content_data["content"] = base64.b64decode(content_data["content"]).decode("utf-8")
            content_data["encoding"] = "utf-8"
            print(f"--- {file_info['path']} ---")
            print(content_data["content"][:1000])
        except Exception as e:
            logger.exception(
                "Failed to process file.",
                file_path=file_info["path"],
                error=str(e),
                file_info=file_info,
            )

    username = "standardebooks"
    repositories = github.fetch_user_repositories(username)

    toc_url = f"https://api.github.com/repos/standardebooks/{title}/contents/src/epub/toc.xhtml?ref=master"
    toc_data = github.fetch_single_file_content_data(toc_url)
    print(toc_data["content"])

    for repo in repositories:
        print(f"Name: {repo['name']}")
        print(f"URL:  {repo['url']}")
        print(f"Owner: {repo['owner']}")
        print(f"Description: {repo['description']}")
        print("-" * 30)


if __name__ == "__main__":
    main()
