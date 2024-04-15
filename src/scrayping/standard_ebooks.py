import base64
import json
import os
from datetime import datetime
from pathlib import Path

import structlog
from structlog.stdlib import BoundLogger

from scrayping.github_api import FileInfo
from scrayping.github_api import GithubApiManager
from scrayping.github_api import GithubApiUrl
from scrayping.github_api import RepositoryInfo
from scrayping.github_api import build_github_file_api
from scrayping.github_api import build_github_tree_api
from utils.data_io import read_dict
from utils.data_io import save_chunk
from utils.data_io import save_xhtml
from utils.logger_config import configure_logger

BOOK_DIR = os.environ.get("BOOK_DIR", "/books")


def build_text_file_tree_url(book_name: str) -> GithubApiUrl:
    return build_github_tree_api("standardebooks", book_name, "src/epub/text")


def build_toc_file_url(book_name: str) -> GithubApiUrl:
    return build_github_file_api("standardebooks", book_name, "src/epub/toc.xhtml")


def tree_info_path(book_name: str) -> Path:
    return target_book_dir(book_name) / "info.json"


def target_book_dir(book_name: str) -> Path:
    return Path(f"{BOOK_DIR}/{book_name}")


def scrape_files(
    book_name: str, force=False, logger: BoundLogger = structlog.get_logger(__name__)
) -> None:
    tree_info_chunk: list[FileInfo] = read_dict(tree_info_path(book_name), logger)  # type: ignore

    for each_file_info in tree_info_chunk:
        github = GithubApiManager()
        try:
            # EXAMPLE: books/john-maynard-keynes_the-economic-consequences-of-the-peace/chapter-1.xhtml
            target_path = target_book_dir(book_name) / each_file_info["path"]
            if not force and target_path.exists():
                logger.info(
                    "File already exists.",
                    path=target_path,
                    book_name=book_name,
                    fiil_name=target_path.name,
                )
                continue
            url = github.valivade_url(each_file_info["url"], "standardebooks", book_name)
            content_data = github.fetch_single_file_content_data(url)
            save_xhtml(
                base64.b64decode(content_data["content"]).decode("utf-8"), target_path, logger
            )
        except Exception as e:
            logger.exception(
                "Failed to process file.",
                at="scrape_files",
                file_path=each_file_info["path"],
                error=str(e),
                content_data=content_data,
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
    book_name: str, force: bool = False, logger: BoundLogger = structlog.get_logger(__name__)
) -> None:
    if not force and Path(f"{BOOK_DIR}/{book_name}/toc.xhtml").exists():
        logger.info("toc.xhtml already exists.", book_name=book_name)
        return
    toc_file_url = build_toc_file_url(book_name)
    toc_file_info = GithubApiManager().fetch_single_file_content_data(toc_file_url)
    try:
        toc_file_info["content"] = base64.b64decode(toc_file_info["content"]).decode("utf-8")
    except Exception as e:
        logger.exception(
            "Failed to process file.", at="scrape_files", error=str(e), toc_file_info=toc_file_info
        )

    save_chunk(toc_file_info, Path(f"{BOOK_DIR}/{book_name}/toc_file_info.json"), logger)
    save_xhtml(toc_file_info["content"], Path(f"{BOOK_DIR}/{book_name}/toc.xhtml"), logger)


def fetch_all_repositories(
    force=False, logger: BoundLogger = structlog.get_logger(__name__)
) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    if not force and Path(f"{BOOK_DIR}/{today}_standardebooks_repositories.json").exists():
        return
    github = GithubApiManager()
    repositories = github.fetch_all_user_repositories("standardebooks")
    save_chunk(repositories, Path(f"{BOOK_DIR}/{today}_standardebooks_repositories.json"), logger)


def fetch_30_repositories(
    logger: BoundLogger = structlog.get_logger(__name__),
) -> list[RepositoryInfo]:
    file_path = Path(f"{BOOK_DIR}/trial_standardebooks_repositories.json")
    if file_path.exists():
        return read_dict(Path(f"{BOOK_DIR}/trial_standardebooks_repositories.json"), logger)  # type: ignore
    github = GithubApiManager()
    repositories = github.fetch_user_repositories("standardebooks")
    save_chunk(repositories, file_path, logger)

    return repositories


def fetch_book_data(
    book_name: str, force=False, logger: BoundLogger = structlog.get_logger(__name__)
) -> None:
    fetch_raw_toc_file(book_name, force, logger)
    save_tree_info(book_name, force, logger)
    scrape_files(book_name, force, logger)


def main():
    configure_logger()

    logger = structlog.get_logger(__name__)

    title = "john-maynard-keynes_the-economic-consequences-of-the-peace"
    fetch_book_data(title, False, logger)

    repos = fetch_30_repositories(logger)
    for repo in repos:
        book_name = repo["name"]
        print(book_name)
        fetch_book_data(book_name, False, logger)

    # save_chunk(repositories, Path(f"{BOOK_DIR}/{today}_standardebooks_repositories.json"), logger)

    # fetch_all_repositories(False, logger)


if __name__ == "__main__":
    main()
