import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from typing import TypedDict

import structlog

from scrayping.github_api import ContentData
from scrayping.github_api import FileInfo
from scrayping.github_api import GithubAPI
from scrayping.github_api import RepositoryInfo
from utils.logger_config import configure_logger

configure_logger()

logger = structlog.get_logger(__name__)


def save_chunk(data: list[FileInfo] | ContentData | list[RepositoryInfo], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fp:
        json.dump(data, fp)


def read_dict(path) -> list[FileInfo]:
    with open(path) as fp:
        return json.load(fp)


def get_text_file_tree_url_from_title(title: str) -> str:
    TEXT_FILE_DIR = "src/epub/text"
    return f"https://api.github.com/repos/standardebooks/{title}/git/trees/master:{TEXT_FILE_DIR}"


def data_info_path(title: str) -> Path:
    return Path(f"{title}/info.json")


def scrape_files(
    title: str = "john-maynard-keynes_the-economic-consequences-of-the-peace",
) -> None:
    github_api = GithubAPI()
    if data_info_path(title).exists():
        tree_info_chunk: list[FileInfo] = read_dict(data_info_path(title))
    else:
        text_file_tree_url = get_text_file_tree_url_from_title(title)
        tree_info_chunk = github_api.get_file_tree_info(text_file_tree_url)

        save_chunk(tree_info_chunk, data_info_path(title))
    for file_info in tree_info_chunk:
        try:
            target_path = Path(f"{title}/{file_info['path']}.json")
            if target_path.exists():
                continue
            content_data = github_api.get_single_file_content_data(file_info)
            content_data["content"] = base64.b64decode(content_data["content"]).decode("utf-8")
            content_data["encoding"] = "utf-8"

            save_chunk(content_data, target_path)
        except Exception as e:
            logger.exception("Failed to process file.", file_path=file_info["path"], error=str(e))


def get_all_repositories():
    github_api = GithubAPI()
    repositories = github_api.get_all_user_repositories("standardebooks")
    save_chunk(repositories, Path("standardebooks_repositories.json"))


def main():
    scrape_files()


if __name__ == "__main__":
    main()
