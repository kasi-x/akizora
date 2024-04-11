import base64
import json
import os
from datetime import datetime
from pathlib import Path

import structlog
from structlog.stdlib import BoundLogger

from scrayping.github_api import ContentData
from scrayping.github_api import FileInfo
from scrayping.github_api import GithubApiManager
from scrayping.github_api import GithubApiUrl
from scrayping.github_api import RepositoryInfo
from utils.logger_config import configure_logger

BOOK_DIR = os.environ.get("BOOK_DIR", "/books")


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


def build_text_file_tree_url(book_name: str) -> GithubApiUrl:
    TEXT_FILE_DIR = "src/epub/text"
    BASE_URL = f"https://api.github.com/repos/standardebooks/{book_name}/git/trees/master"
    return BASE_URL + ":" + TEXT_FILE_DIR


def build_toc_file_url(book_name: str) -> GithubApiUrl:
    TOC_FILE_DIR = "src/epub/toc.xhtml"
    BASE_URL = f"https://api.github.com/repos/standardebooks/{book_name}/git/trees/master"
    return BASE_URL + ":" + TOC_FILE_DIR


def tree_info_path(book_name: str) -> Path:
    return tarfetch_book_dir(book_name) / "info.json"


def tarfetch_book_dir(book_name: str) -> Path:
    return Path(f"{BOOK_DIR}/{book_name}")


def scrape_files(
    book_name: str, force=False, logger: BoundLogger = structlog.get_logger(__name__)
) -> None:
    tree_info_chunk = read_dict(tree_info_path(book_name), logger)

    for each_file_info in tree_info_chunk:
        github = GithubApiManager()
        try:
            # EXAMPLE: books/john-maynard-keynes_the-economic-consequences-of-the-peace/chapter-1.xhtml
            tarfetch_path = tarfetch_book_dir(book_name) / each_file_info["path"]
            if not force and tarfetch_path.exists():
                logger.info(
                    "File already exists.",
                    path=tarfetch_path,
                    book_name=book_name,
                    fiil_name=tarfetch_path.name,
                )
                continue
            url = github.valivade_url(each_file_info["url"], "standardebooks", book_name)
            content_data = github.fetch_single_file_content_data(url)
            save_xhtml(
                base64.b64decode(content_data["content"]).decode("utf-8"), tarfetch_path, logger
            )
        except Exception as e:
            logger.exception(
                "Failed to process file.",
                at="scrape_files",
                file_path=each_file_info["path"],
                error=str(e),
            )


def save_tree_info(
    book_name: str, force=False, logger: BoundLogger = structlog.get_logger(__name__)
) -> None:
    if not force and tree_info_path(book_name).exists():
        logger.info(
            "Tree_info already exists.", path=tree_info_path(book_name), book_name=book_name
        )
        return
    text_file_tree_url = build_text_file_tree_url(book_name)
    save_chunk(
        GithubApiManager().fetch_file_tree_info(text_file_tree_url),
        tree_info_path(book_name),
        logger,
    )
    return


def fetch_raw_toc_file(
    book_name: str, force: bool = False, logger: BoundLogger = structlog.fetch_logger(__name__)
) -> None:
    if not force and Path(f"{BOOK_DIR}/{book_name}/toc.xhtml").exists():
        logger.info("toc.xhtml already exists.", book_name=book_name)
        return
    toc_file_url = build_toc_file_url(book_name)
    toc_file_info = GithubApiManager().fetch_single_file_content_data(toc_file_url)
    toc_file_info["content"] = base64.b64decode(toc_file_info["content"]).decode("utf-8")

    save_chunk(toc_file_info, Path(f"{BOOK_DIR}/{book_name}/toc_file_info.json"), logger)
    save_xhtml(toc_file_info["content"], Path(f"{BOOK_DIR}/{book_name}/toc.xhtml"), logger)


def fetch_all_repositories(
    force=False, logger: BoundLogger = structlog.get_logger(__name__)
) -> None:
    if not force and Path("books/standardebooks_repositories.json").exists():
        return
    github_api = GithubApiManager()
    repositories = github_api.fetch_all_user_repositories("standardebooks")
    today = datetime.now().strftime("%Y-%m-%d")
    save_chunk(repositories, Path(f"{BOOK_DIR}/{today}_standardebooks_repositories.json"), logger)


def fetch_30_repositories(
    force=False, logger: BoundLogger = structlog.get_logger(__name__)
) -> None:
    if not force and Path("books/standardebooks_repositories.json").exists():
        return
    github_api = GithubApiManager()
    repositories = github_api.fetch_user_repositories("standardebooks")
    import pprint

    pprint.pprint(repositories)


def main():
    book_name = "john-maynard-keynes_the-economic-consequences-of-the-peace"
    configure_logger()

    logger = structlog.get_logger(__name__)

    fetch_raw_toc_file(book_name, False, logger)
    scrape_files(book_name, True, logger)
    fetch_30_repositories(False, logger)
    # fetch_all_repositories(False, logger)


if __name__ == "__main__":
    main()
