import base64
import os

import requests
import structlog

from logger_config import configure_logger

configure_logger()
logger = structlog.get_logger(__name__).bind(module="github_api")

API_URL = "https://api.github.com"


class GithubAPI:
    def __init__(self) -> None:
        access_token = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]
        self.headers = {"Authorization": f"token {access_token}"}

    def _log_api_request(self, url: str, method="GET") -> None:
        logger.info("API Request", url=url, method=method)

    def _log_api_response(self, url: str, status_code: int, response_text: str = "") -> None:
        if status_code >= 400:
            logger.error(
                "API Request Failed", url=url, status_code=status_code, response_text=response_text
            )
        else:
            logger.debug("API Request Successful", url=url, status_code=status_code)

    @staticmethod
    def get_file_tree_url_from_title(title: str) -> str:
        return f"{API_URL}/repos/standardebooks/{title}/git/trees/master:"

    def get_tree_info(self, title: str):
        file_tree_url = self.get_file_tree_url_from_title(title)
        self._log_api_request(file_tree_url)
        response = requests.get(file_tree_url, headers=self.headers)
        self._log_api_response(file_tree_url, response.status_code, response.text)

        if response.status_code == 200:
            return response.json()["tree"]
        else:
            msg = "Failed to get tree info."
            raise Exception(msg)

    def process_file_info(self, file_info):
        if file_info["type"] != "blob":
            logger.error("File type is not blob.", file_path=file_info["path"])
            msg = "File type is not blob."
            raise Exception(msg)
        return self.get_file_content(file_info["url"])

    def get_file_content(self, content_url):
        self._log_api_request(content_url)  # ログ追加
        response = requests.get(content_url, headers=self.headers)
        self._log_api_response(content_url, response.status_code, response.text)

        if response.status_code == 200:
            return base64.b64decode(response.json()["content"]).decode("utf-8")
        else:
            msg = "Failed to get file content."
            raise Exception(msg)


# test_case
def main():
    title = "john-maynard-keynes_the-economic-consequences-of-the-peace"
    github_api = GithubAPI()
    tree_info = github_api.get_tree_info(title)
    for file_info in tree_info:
        try:
            github_api.process_file_info(file_info)
            print(f"--- {file_info['path']} ---")
        except Exception as e:
            logger.exception("Failed to process file.", file_path=file_info["path"], error=str(e))
