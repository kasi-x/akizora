import re
from dataclasses import dataclass
from dataclasses import field

import spacy


@dataclass
class Sentence:
    text: str
    token_count: int = field(init=False)
    # add words count.
    # append total char count.
    # llm token_count

    def __post_init__(self):
        self.token_count = len(self.text.split())

    # def __llm_token_count(self):
    # return llm_token_count(self.text) # change name but not implement needed.


@dataclass
class Section:
    section_number_in_chapter: int
    content: str
    sentences: list[Sentence] = field(init=False)

    def __post_init__(self):
        self.sentences = [
            Sentence(text=sent.strip()) for sent in self.content.split(".") if sent.strip()
        ]


@dataclass
class Chapter:
    chapter_number: int
    chapter_title: str
    sections: list[Section]
    # append total token_count.
    # append total word count.
    # append total char count.


@dataclass
class Book:
    chapters: list[Chapter] = field(default_factory=list)
    # append total token_count.
    # append total word count.
    # append total char count.


# spaCyのモデルをロード
nlp = spacy.load("en_core_web_sm")

# Loggerの設定
configure_logger()
logger = structlog.get_logger()

# 正規表現パターン
CHAPTER_PATTERN = re.compile(r"\bCHAPTER\s+\d+\b", re.IGNORECASE)
SECTION_PATTERN = re.compile(r"\bSECTION\s+\d+\b")


def mark_text_elements(text: str) -> str:
    # 章をマークする
    text = CHAPTER_PATTERN.sub(lambda m: f"<<Chapter>>{m.group(0)}<</Chapter>>", text)

    # セクションと段落のマークは仮定に基づくもので、実際の用途に応じて調整が必要
    text = re.sub(r"\n{3,}", "<<SectionBreak>>", text)  # セクションの区切りをマーク
    text = re.sub(r"\n{2}", "<<ParagraphBreak>>", text)  # 段落の区切りをマーク

    # 余分な改行とスペースを削除
    text = re.sub(r"\s{2,}", " ", text)  # 余分なスペースを削除
    text = re.sub(
        r"(?<=Chapter>>)\s+|\s+(?=<</Chapter>)", "", text,
    )  # 章マークの内側のスペースを削除

    return text.strip()


def process_chapter_text(chapter_text: str, chapter_index: int) -> Chapter:
    """チャプターテキスト内のセクションを処理する。."""
    # この例では、セクションの分割やタイトル抽出は示していませんが、
    # 実際にはテキストの構造に応じた追加処理が必要になります。
    sections = []  # セクションの処理を追加する場合
    chapter_title = chapter_text.split(">>", 1)[0][9:]  # 簡易的なタイトル抽出
    return Chapter(chapter_index, chapter_title, sections)


def split_into_chapters_and_process(text: str) -> list[Chapter]:
    """テキストを章に分割して処理する。."""
    marked_text = mark_text_elements(text)
    chapters_texts = re.split(r"<<Chapter>>|<</Chapter>>", marked_text)[1:]
    chapters = [
        process_chapter_text(chapters_texts[i], i // 2 + 1)
        for i in range(0, len(chapters_texts), 2)
    ]
    return chapters


# テキストを読み込む
with open("sample.txt") as file:
    text = file.read()

# テキストを正規化し、章に分割して処理する
chapters = split_into_chapters_and_process(text)

# チャプターをファイルに保存する（デモ用の簡易的な保存方法）
for chapter in chapters:
    filename = f"chapter_{chapter.chapter_number}_{chapter.chapter_title}.txt"
    with open(filename, "w") as file:
        file.write(f"Chapter Title: {chapter.chapter_title}\nSections: {chapter.sections}")
