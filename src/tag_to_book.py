from src.book_domain import Book
from src.book_domain import Chapter
from src.book_domain import Line
from src.book_domain import Section
from src.book_domain import TextComponent
from tag import ProtoBook
from tag import ProtoChapter
from tag import ProtoLine
from tag import ProtoSection
from tag import ProtoTextComponent


def proto_to_domain(proto: ProtoTextComponent) -> TextComponent:
    if isinstance(proto, ProtoBook):
        return Book(
            _title=proto.title,
            contents=[proto_to_domain(content) for content in proto.contents],  # type: ignore
        )
    if isinstance(proto, ProtoChapter):
        return Chapter(
            _title=proto.title,
            contents=[proto_to_domain(content) for content in proto.contents],  # type: ignore
        )
    if isinstance(proto, ProtoSection):
        return Section(
            _title=proto.title,
            contents=[proto_to_domain(content) for content in proto.contents],  # type: ignore
        )
    if isinstance(proto, ProtoLine):
        return Line(_text=proto.text)
    msg = f"Unknown type: {type(proto)}"
    raise ValueError(msg)
