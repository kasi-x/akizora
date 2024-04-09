import json
from pathlib import Path

import structlog

# from logger_config import configure_logger
from scrayping.github_api import GithubAPI

# configure_logger()

# logger = structlog.get_logger(__name__)


def save_dict(data: dict, path: Path) -> None:
    if not path.exists():
        path.touch()
    with open(path, "w") as fp:
        json.dump(data, fp)


def read_dict(path):
    with open(path) as fp:
        return json.load(fp)


def save_file(title: str = "john-maynard-keynes_the-economic-consequences-of-the-peace") -> None:
    cached_file_path = Path(f"{title}/info.json")
    if cached_file_path.exists():
        tree_info = read_dict(cached_file_path)
    else:
        github_api = GithubAPI()
        tree_info = github_api.get_tree_info(title)
        save_dict(tree_info, cached_file_path)

    for file_name, file_info in tree_info.items():
        file_content_path = Path(f"{title}/{file_name}.json")
        if not file_content_path.exists():
            try:
                file_content = github_api.process_file_info(file_info)
                print(f"--- {file_name} ---")
            except Exception:
                pass
                # logger.exception("Failed to process file.", file_path=file_name, error=str(e))
            with open(file_content_path, "w") as fp:
                json.dump(file_content, fp)


def main():
    title = "john-maynard-keynes_the-economic-consequences-of-the-peace"
    save_file(title)
    info_dict = read_dict(f"{title}/info.json")
    for file_name in info_dict:
        file_content = read_dict(f"{title}/{file_name}.json")
        print(f"--- {file_name} ---")
        print(file_content)


if __name__ == "__main__":
    main()
