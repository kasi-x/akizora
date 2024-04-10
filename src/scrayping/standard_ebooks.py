import base64
import json
from datetime import datetime
from pathlib import Path

import structlog
from structlog.stdlib import BoundLogger

from scrayping.github_api import ContentData
from scrayping.github_api import FileInfo
from scrayping.github_api import GithubAPI
from scrayping.github_api import RepositoryInfo
from utils.logger_config import configure_logger


def save_chunk(
    data: list[FileInfo] | ContentData | list[RepositoryInfo], path: Path, logger: BoundLogger
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fp:
        json.dump(data, fp)
    if logger:
        logger.info("Saved data.", path=path)


def save_xhtml(data: str, path: Path, logger: BoundLogger) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fp:
        fp.write(data)
    if logger:
        logger.info("Saved data.", path=path)


def read_dict(path, logger=None) -> list[FileInfo]:
    if logger:
        logger.info("Reading data.", path=path)
    with open(path) as fp:
        return json.load(fp)


def get_text_file_tree_url_from_title(title: str) -> str:
    TEXT_FILE_DIR = "src/epub/text"
    return f"https://api.github.com/repos/standardebooks/{title}/git/trees/master:{TEXT_FILE_DIR}"


def data_info_path(title: str) -> Path:
    return Path(f"books/{title}/info.json")


def scrape_files(title: str, logger: BoundLogger = structlog.get_logger(__name__)) -> None:
    github_api = GithubAPI()
    if data_info_path(title).exists():
        tree_info_chunk: list[FileInfo] = read_dict(data_info_path(title))
    else:
        text_file_tree_url = get_text_file_tree_url_from_title(title)
        tree_info_chunk = github_api.get_file_tree_info(text_file_tree_url)

        save_chunk(tree_info_chunk, data_info_path(title), logger)
    for file_info in tree_info_chunk:
        try:
            target_path = Path(f"books/{title}/{file_info['path']}")
            # books/john-maynard-keynes_the-economic-consequences-of-the-peace/chapter-1.xhtml
            if target_path.exists():
                continue
            content_data = github_api.get_single_file_content_data(file_info["url"])
            content_data["content"] = base64.b64decode(content_data["content"]).decode("utf-8")
            content_data["encoding"] = "utf-8"

            save_xhtml(content_data["content"], target_path, logger)
        except Exception as e:
            logger.exception(
                "Failed to process file.",
                at="scrape_files",
                file_path=file_info["path"],
                error=str(e),
            )


def get_raw_toc_file(title: str, logger: BoundLogger = structlog.get_logger(__name__)) -> None:
    github_api = GithubAPI()
    toc_file_url = (
        f"https://api.github.com/repos/standardebooks/{title}/contents/src/epub/toc.xhtml"
    )
    toc_file_info = github_api.get_single_file_content_data(toc_file_url)
    save_xhtml(
        base64.b64decode(toc_file_info["content"]).decode("utf-8"),
        Path(f"books/{title}/toc.xhtml"),
        logger,
    )


def get_all_repositories(logger: BoundLogger = structlog.get_logger(__name__)) -> None:
    github_api = GithubAPI()
    repositories = github_api.get_all_user_repositories("standardebooks")
    today = datetime.now().strftime("%Y-%m-%d")
    save_chunk(repositories, Path(f"books/{today}_standardebooks_repositories.json"), logger)


def main():
    title = "john-maynard-keynes_the-economic-consequences-of-the-peace"
    configure_logger()

    logger = structlog.get_logger(__name__)

    get_raw_toc_file(title, logger)
    scrape_files(title, logger)
    # get_all_repositories(logger)


if __name__ == "__main__":
    main()
