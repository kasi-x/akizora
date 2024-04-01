import pprint
import re

from bs4 import BeautifulSoup as bs

from domain.book import Book
from domain.tag import ProtoBook
from domain.tag import ProtoChapter
from domain.tag import ProtoLine
from domain.tag import ProtoSection
from domain.tag import ProtoTextComponent

unsorted_tag_priorities = {
    "PART": 5,
    "CHAPTER": 4,
    "CHAPTER_TITLE": 3,
    "TRANSCRIBER_NOTES": 6,
    "TRANSCRIBER_NOTES_TITLE": 2,
    "SECTION": 3,
    "SECTION_TITLE": 2,
    "THE_END": 6,
    "EPILOGUE": 4,
    "EPILOGUE_TITLE": 2,
    "PROLOGUE": 4,
    "PROLOGUE_TITLE": 2,
    "DATA": 3,
    "HEADER": 5,
    "BODY": 2,
    "FOOTER": 5,
}


# OPTIMIZE: sorted_dict is smarter, but it's just under 0.00.. sec saving)
def get_specific_key_of_bigger_than_some(name="CHAPTER"):
    keys = []
    d = unsorted_tag_priorities
    for key in d:
        if d[key] >= d[name]:
            keys.append(key)
    return keys


SORTED_TAG_PRIORITIES = dict(
    sorted(unsorted_tag_priorities.items(), key=lambda item: item[1], reverse=False)
)


def replace_text_with_placeholder(html_content):
    pattern = re.compile(r"(<[^>]+>)|([^<>]+)")
    placeholder_counter = 1
    text_placeholders = {}

    def replacement_function(match):
        nonlocal placeholder_counter
        is_text = bool(match.group(2))  # is_text mean, it is not tag value.
        if is_text:
            placeholder_key = f"placeholder{placeholder_counter}"
            text_placeholders[placeholder_key] = match.group(2).strip()
            placeholder_counter += 1
            return placeholder_key
        else:
            # return tag with priority
            return match.group(1)

    replaced_html = pattern.sub(replacement_function, html_content)
    return replaced_html, text_placeholders


def restore_text_from_placeholder(replaced_html: str, text_placeholders_dict: dict):
    placeholder_pattern = re.compile(r"placeholder\d+")

    def restore_text(match: re.Match):
        placeholder_key = match.group(0)
        return text_placeholders_dict.get(placeholder_key, "")

    restored_html = placeholder_pattern.sub(restore_text, replaced_html)
    return restored_html


# REFACTOR: more readable and maintainable.
def tag_to_priority_str_with_closing(tag, priorities):
    def get_tag_name(tag):
        tag = tag.strip("<>")
        if tag.startswith("/"):
            tag = tag[1:]
        return tag

    tag_name = get_tag_name(tag)  # Extract the tag name
    priority = priorities.get(tag_name, -1)  # Get the priority or default to -1
    if tag.startswith("</"):  # Check if it's a closing tag
        return f"</{tag_name}: {priority}>"
    else:  # It's an opening tag
        return f"<{tag_name}: {priority}>"


def replace_tags_with_rules(text):
    replacements = {
        f"<{tag}>": f"<{tag}:p{priority}>" for tag, priority in unsorted_tag_priorities.items()
    }
    replacements.update(
        {f"</{tag}>": f"</{tag}:p{priority}>" for tag, priority in unsorted_tag_priorities.items()}
    )

    for original, replacement in replacements.items():
        text = re.sub(original, replacement, text, flags=re.IGNORECASE)
    return text


# REFACTOR: refactor this function to make it more readable and maintainable.
def parse_and_correct_html(text):
    tag_or_placeholder_pattern = re.compile(r"<(/?)(\w+)(\d*):p?(\d*)>|placeholder\d+")
    stack = []
    result = []

    def should_insert_stack(stack, new_tag_priority):
        return stack[-1][1] <= new_tag_priority

    def append_tag(tag, is_open_tag) -> None:
        if is_open_tag:
            result.append(f"\n<{tag}>\n")
        else:
            result.append(f"\n</{tag}>\n")

    for match in tag_or_placeholder_pattern.finditer(text):
        is_place_holder = "placeholder" in match.group(0)
        if is_place_holder:
            result.append(match.group(0))
        else:
            is_open_tag = match.group(1) == ""
            target_tag_name = match.group(2)
            if is_open_tag:
                target_tag_priority_str = match.group(4)
                target_tag_priority = (
                    int(target_tag_priority_str) if target_tag_priority_str.isdigit() else -1
                )

                while stack and should_insert_stack(stack, target_tag_priority):
                    tag_name, _ = stack.pop()
                    append_tag(tag_name, False)
                stack.append((target_tag_name, target_tag_priority))
                append_tag(target_tag_name, True)
            else:
                while stack:
                    tag_name, _ = stack.pop()
                    append_tag(tag_name, False)
                    if tag_name == target_tag_name:
                        break

    while stack:
        tag_name, _ = stack.pop()
        append_tag(tag_name, False)

    return "".join(result)


# REFACTOR: not readable.
def find_section_boundaries(html, tags):
    tags_regex = "|".join(tags)
    pattern = re.compile(f"<(/)?({tags_regex})(:\\d*)?>")
    boundaries = []
    for match in pattern.finditer(html):
        _tag_full, is_closing, tag_name, span = (
            match.group(0),
            bool(match.group(1)),
            match.group(2),
            match.span(),
        )
        boundaries.append((is_closing, tag_name, span))
    return boundaries


# LOGIC: more smart way to find the tag name
def construct_sections(html, boundaries):
    sections = []
    open_tag = None
    section_start = 0
    for is_closing, tag_name, span in boundaries:
        if not is_closing:
            if open_tag is not None:
                sections.append((open_tag, html[section_start : span[0]].strip()))
            open_tag = tag_name
            section_start = span[1]
        elif open_tag == tag_name:
            sections.append((tag_name, html[section_start : span[0]].strip()))
            open_tag = None
    return sections


def make_section(title, body, language="en"):
    return ProtoSection(title, body)


def extract_title(soup) -> str:
    title_tag = soup.find(lambda tag: tag.name.upper().endswith("TITLE"))
    return title_tag.get_text(strip=True) if title_tag else ""


def extract_body(soup) -> list[str]:
    tag = "body"
    body_tag = soup.find(tag)
    return body_tag.get_text(strip=True).split("\n") if body_tag else []


# def process_html_into_sections(html_text, tag_list):
#     boundaries = find_section_boundaries(html_text, tag_list)
#     raw_sections = construct_sections(html_text, boundaries)
#     processed_sections = [
#         Section(*extract_content_from_section(section)) for _, section in raw_sections
#     ]
#     return processed_sections
#


# LOGIC: more samrt way to find the tag name
# REFACTOR: more good name for each variable and class-name and func-name.
class HTMLSectionProcessor:
    def __init__(self, html, tags):
        self.html = html
        self.tags = tags

    def _find_section_boundaries(self):
        tags_regex = "|".join(self.tags)
        pattern = re.compile(f"<(/)?({tags_regex})(:\\d*)?>")
        return [
            (bool(match.group(1)), match.group(2), match.span())
            for match in pattern.finditer(self.html)
        ]

    def _construct_sections(self, boundaries):
        sections = []
        open_tag = None
        section_start = None
        for is_closing, tag_name, span in boundaries:
            if not is_closing and open_tag is None:
                open_tag = tag_name
                section_start = span[1]  # タグの終了直後からセクションを開始
            elif is_closing and open_tag == tag_name:
                sections.append((tag_name, self.html[section_start : span[0]].strip()))
                open_tag = None
        return sections

    @staticmethod
    def extract_content_from_section(section) -> tuple[str, list[str]]:
        soup = bs(section, "html.parser")
        title, body = extract_title(soup), extract_body(soup)

        if not title and not body:
            title: str = soup.get_text(strip=True)
        elif title and not body:
            body: list[str] = [soup.get_text(strip=True)]

        return title, body

    @staticmethod
    def _extract_title_or_body(soup, tag, is_title=False):
        def tag_func(tag):
            return tag.name.upper().endswith("TITLE") if is_title else tag.name.lower() == tag

        found_tag = soup.find(tag_func)
        if found_tag:
            text = found_tag.get_text(strip=True)
            return text if is_title else text.split("\n")
        return "" if is_title else []

    def process(self):
        boundaries = self._find_section_boundaries()
        raw_sections = self._construct_sections(boundaries)
        return [
            ProtoSection(*self.extract_content_from_section(section))
            for _, section in raw_sections
        ]


chapter_level_tag_list = ["PROLOGUE", "CHAPTER", "EPILOGUE", "THE_END", "TRANSCRIBER_NOTES"]


def remove_single_newlines(text, newline="\n"):
    """二個以上、連続した改行コードは無視して、単個の改行コードを削除する.

    Args:
      text: 処理対象の文字列
      newline: 改行コードの種類

    Returns:
      処理後の文字列
    """
    text = text.replace(newline * 3, "<TRIPLE_LINE>")
    text = text.replace(newline * 2, "<DOUBLE_LINE>")
    text = text.replace(newline, " ")
    text = text.replace("<TRIPLE_LINE>", "\n\n\n")
    text = text.replace("<DOUBLE_LINE>", "\n\n")

    text = text.rstrip()

    return text


def make_component_tag(text):
    lines = text.split("\n")
    modified_lines = []

    is_body = False
    for line in lines:
        line = line.strip()
        if re.match(r"(?i)^CHAPTER\s+\d+", line):
            modified_lines.append(f"<CHAPTER><CHAPTER_TITLE> {line} </CHAPTER_TITLE>")
            is_body = False
        elif re.match(r"(?i)^PART\s+\d+", line):
            modified_lines.append(f"<PART><PART_TITLE> {line} </PART_TITLE>")
            is_body = False
        elif re.match(r"(?i)^EPILOGUE", line):
            modified_lines.append(f"<EPILOGUE> <EPILOGUE_TITLE> {line} </EPILOGUE_TITLE>")
            is_body = False
        elif re.match(r"^THE END$", line):
            modified_lines.append(f"<THE_END> {line} </THE_END>")
            is_body = False
        elif re.match(r"(?i)^OPENING", line):
            modified_lines.append(f"<OPENING><OPENING_TITLE> {line} </OPENING_TITLE>")
            is_body = False
        elif re.match(r"(?i)^PROLOGUE", line):
            modified_lines.append(f"<PROLOGUE><PROLOGUE_TITLE> {line} </PROLOGUE_TITLE>")
            is_body = False
        elif re.match(r"(?i)^TRANSCRIBER NOTES", line):
            modified_lines.append(
                f"<TRANSCRIBER_NOTES><TRANSCRIBER_NOTES_TITLE> {line} </TRANSCRIBER_NOTES_TITLE>"
            )
            is_body = False
        else:
            if not is_body:
                modified_lines.append("<BODY>")
                is_body = True
            modified_lines.append(line)

    return "\n".join(modified_lines)


def make_sentenec(raw_line: ProtoLine):
    return ProtoSentence(raw_line.text)


def proto_to_domain(proto: ProtoTextComponent) -> TextComponent:
    if isinstance(proto, ProtoBook):
        return Book(
            title=proto.title,
            contents=[proto_to_domain(content) for content in proto.contents],  # type: ignore
        )
    if isinstance(proto, ProtoChapter):
        return Chapter(
            title=proto.title,
            contents=[proto_to_domain(content) for content in proto.contents],  # type: ignore
        )
    if isinstance(proto, ProtoSection):
        return Section(
            title=proto.title,
            contents=[proto_to_domain(content) for content in proto.contents],  # type: ignore
        )
    if isinstance(proto, ProtoLine):
        return Line(text=proto.text)
    msg = f"Unknown type: {type(proto)}"
    raise ValueError(msg)


def main():
    text = open("sample.txt").read()
    text = remove_single_newlines(text)

    taged_text = make_component_tag(text)

    # MEMO: Not smart, more fix way to replace text with placeholder.
    start_tag_and_placeholder_text, text_placeholder_dict = replace_text_with_placeholder(
        taged_text
    )

    prioritized_tag_text = replace_tags_with_rules(start_tag_and_placeholder_text)
    tag_complited_text = parse_and_correct_html(prioritized_tag_text)
    result = restore_text_from_placeholder(tag_complited_text, text_placeholder_dict)

    processor = HTMLSectionProcessor(result, chapter_level_tag_list)
    processed_sections = processor.process()
    chapters = []
    for section in processed_sections:
        lines = []
        joined = "\n".join(section.contents).split("\n\n")
        for one_line_text in joined:
            lines.append(ProtoLine(one_line_text))
        chapters.append(ProtoChapter(title=section.title, contents=lines))
    print(chapters)
    print(chapters[0].contents[0].text)
    chaps = []
    for chapter in chapters:
        chaps.append(proto_to_domain(chapter))
    book = Book(contents=chaps)
    return book


if __name__ == "__main__":
    main()
