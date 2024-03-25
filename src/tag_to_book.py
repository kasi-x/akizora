from src.book_domain import Book
from src.book_domain import Chapter
from src.book_domain import Line
from src.book_domain import Section
from src.book_domain import TextComponent
from src.tag import ProtoBook
from src.tag import ProtoChapter
from src.tag import ProtoLine
from src.tag import ProtoSection
from src.tag import ProtoTextComponent


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
