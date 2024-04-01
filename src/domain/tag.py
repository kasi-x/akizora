import re
from dataclasses import dataclass

from domain.book import Book
from domain.book import Chapter
from domain.book import Line
from domain.book import Section
from domain.book import TextComponent


class ProtoTextComponent:
    def __init__(self, contents, title=None):
        self.contents = contents
        self.title = title


class ProtoChapter(ProtoTextComponent):
    pass


class ProtoBook(ProtoTextComponent):
    pass


class ProtoSeries(ProtoTextComponent):
    pass


class ProtoSection(ProtoTextComponent):
    pass


class ProtoLine(ProtoTextComponent):
    pass


class ProtoSentence(ProtoTextComponent):
    pass


# def make_sentenec(raw_line: ProtoLine):
#     return ProtoSentence(raw_line.text)
#
#
# def proto_to_domain(proto: ProtoTextComponent) -> TextComponent:
#     if isinstance(proto, ProtoBook):
#         return Book(
#             title=proto.title,
#             contents=[proto_to_domain(content) for content in proto.contents],  # type: ignore
#         )
#     if isinstance(proto, ProtoChapter):
#         return Chapter(
#             title=proto.title,
#             contents=[proto_to_domain(content) for content in proto.contents],  # type: ignore
#         )
#     if isinstance(proto, ProtoSection):
#         return Section(
#             title=proto.title,
#             contents=[proto_to_domain(content) for content in proto.contents],  # type: ignore
#         )
#     if isinstance(proto, ProtoLine):
#         return Line(text=proto.text)
#     msg = f"Unknown type: {type(proto)}"
#     raise ValueError(msg)
