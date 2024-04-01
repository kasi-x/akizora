from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field
from typing import Optional
from typing import Self
from typing import TypedDict

from dotenv import load_dotenv
from structlog import get_logger

from domain.componet import NATIVE_CONTENT
from domain.componet import TextComponent
from logger_config import configure_logger

configure_logger()
logger = get_logger().bind(module="book_domain")

load_dotenv("GOOGLE_API_KEY")


def remove_noise_space(text: str) -> str:
    return text.replace("\n", " ").strip()
    # NOTE: In some case the latter can be better.
    # return re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # NOTE: I remove wastefull whitespace.
    # But in some case, like Askey Art, could use whitespace as art. But Novel's text maight not use white space as an art.


@dataclass
class Series(TextComponent):
    depth_level = -3


@dataclass
class Book(TextComponent):
    depth_level = -2


@dataclass
class Part(TextComponent):
    depth_level = -1


@dataclass
class Chapter(TextComponent):
    depth_level = 0


@dataclass
class Section(TextComponent):
    depth_level = 1


class SubSection(TextComponent):
    depth_level = 2


class Paragraph(TextComponent):
    depth_level = 3


class SubParagraph(TextComponent):
    depth_level = 4


class Line(TextComponent):
    depth_level = 5


class Sentence(TextComponent):
    depth_level = 6
    contents: NATIVE_CONTENT
    a_content: NATIVE_CONTENT = field(init=False)

    def __post_init__(self):
        self.contents = remove_noise_space(self.contents)
        self.a_content = remove_noise_space(self.contents)
