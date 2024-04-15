import json
from pathlib import Path

from structlog.stdlib import BoundLogger

from scrayping.github_api import ContentData
from scrayping.github_api import FileInfo
from scrayping.github_api import RepositoryInfo


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


def read_dict(path, logger=None) -> list:
    if logger:
        logger.info("Reading data.", path=path)
    with open(path) as fp:
        return json.load(fp)


def read_xhtml(path: Path | str, logger=None) -> str:
    if logger:
        logger.info("Reading data.", path=path)
    with open(path) as fp:
        return fp.read()
