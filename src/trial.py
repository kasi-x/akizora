import re
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from typing import Optional

from dotenv import load_dotenv
from structlog import get_logger

from src.book_domain import LLM_TYPE_NAME
from src.book_domain import Book
from src.book_domain import Language
from src.book_domain import LanguageEnum
from src.book_domain import Line
from src.book_domain import Lines
from src.book_domain import TextComponent
from src.book_domain import TranslatedLine
from src.llm_domain import LLM
from src.logger_config import configure_logger
from src.translate_domain import PromptManager


@dataclass
class SimpleLine:
    id: int
    text: str
    token: int


@dataclass
class SimpleStructure:
    data: "SimpleStructure" | list[SimpleLine]
    token: int


def make_component_into_SimpleStructure(
    component: TextComponent, info: tuple[LanguageEnum, LLM_TYPE_NAME]
) -> SimpleStructure:
    if isinstance(component, Line):
        line = component
        return [SimpleLine(id=line.id, text=line._text, token=line.get_token_count(*info))]
    else:
        return SimpleStructure(
            data=[
                SimpleStructure(
                    (
                        make_component_into_SimpleStructure(sub_component, info)
                        for sub_component in component.contents
                    ),
                    token=component.get_token_count(*info),
                )
            ],
            token=sum(
                sub_component.get_token_count(*info) for sub_component in component.contents
            ),
        )


def strucuture_to_simpleline(structure: SimpleStructure | list | SimpleLine) -> SimpleLine:
    if isinstance(structure, SimpleLine):
        return structure
    if isinstance(structure, list):
        return [strucuture_to_simpleline(a_structure) for a_structure in structure]
    else:
        return strucuture_to_simpleline(structure.data)


def make_chunks_of_SimpleStructure(
    structure: SimpleStructure | list[SimpleStructure], token_limit: int
) -> list[SimpleStructure]:
    if isinstance(structure, SimpleLine):
        if structure.token < token_limit:
            return [SimpleStructure(data=[structure], token=structure.token)]
        else:
            msg = "SimpleLine is too long to split"
            raise ValueError(msg)
    if not isinstance(structure, list):
        if structure.token < token_limit:
            return [structure]
        else:
            return make_chunks_of_SimpleStructure(structure.data, token_limit)
    else:  # isinstance(structure, list)
        total_token = sum(sub_structure.token for sub_structure in structure)
        if total_token < token_limit:
            return [SimpleStructure(data=structure, token=total_token)]
        if structure[0].token >= token_limit and len(structure) == 1:
            return [make_chunks_of_SimpleStructure(structure[0].data, token_limit)]
        if structure[0].token >= token_limit:
            return [
                make_chunks_of_SimpleStructure(structure[0].data, token_limit)
                + make_chunks_of_SimpleStructure(structure[1:], token_limit)
            ]
        else:
            index = 0
            current_token = 0
            next_token = structure[0].token
            while index < len(structure) and current_token + next_token < token_limit:
                current_token += next_token
                index += 1
                next_token = structure[index].token
            return [
                SimpleStructure(data=structure[:index], token=current_token),
                *make_chunks_of_SimpleStructure(structure[index:], token_limit),
            ]

    if isinstance(structure.data, list):
        chunks = []
        chunk = SimpleStructure(data=[], self_token=0)
        for sub_structure in structure.data:
            if chunk.self_token + sub_structure.self_token > token_limit:
                chunks.append(chunk)
                chunk = SimpleStructure(data=[], self_token=0)
            chunk.data.append(sub_structure)
            chunk.self_token += sub_structure.self_token
        chunks.append(chunk)
        return chunks
    else:
        return [structure]
