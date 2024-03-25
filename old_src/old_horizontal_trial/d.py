import re


# 章、セクション、段落をマークするための関数
def mark_text_elements(text: str) -> str:
    # 章をマークする
    chapter_pattern = re.compile(r"(?i)^chapter\s+\d+.*$", re.MULTILINE)
    text = chapter_pattern.sub(lambda m: f"<<Chapter>>{m.group(0).strip()}<</Chapter>>", text)

    # セクションをマークする（例示のため、具体的なセクションのパターンが必要です）
    # ここでは3つ連続する改行をセクションの区切りと仮定します
    section_pattern = re.compile(r"\n{3}")
    text = section_pattern.sub("<<SectionBreak>>", text)

    # 段落をマークする（2つ連続する改行を段落の区切りと仮定）
    paragraph_pattern = re.compile(r"\n{2}")
    text = paragraph_pattern.sub("<<ParagraphBreak>>", text)

    # 単一の改行をスペースに置換する（段落内の改行を削除）
    single_newline_pattern = re.compile(r"(?<!\n)\n(?!\n)")
    text = single_newline_pattern.sub("", text)
    return text


# 不要なスペースを削除する関数
def remove_extra_spaces(text: str) -> str:
    extra_spaces_pattern = re.compile(r"\s{2,}")
    return extra_spaces_pattern.sub(" ", text).strip()


# テキストを正規化する関数（章、セクション、段落をマークし、不要な改行とスペースを削除）
def normalize_text(text: str) -> str:
    text = mark_text_elements(text)
    text = remove_extra_spaces(text)
    return text


# read sample.txt and try normalize_text
with open("sample.txt") as f:
    text = f.read()
    print(normalize_text(text))
