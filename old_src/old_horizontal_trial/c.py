import re


def mark_chapters(text: str) -> str:
    # 章のタイトルを検出する正規表現パターン
    chapter_pattern = re.compile(r"(?i)^chapter\s+\d+.*$|(?<=\n\n\n\n)(.*?$)", re.MULTILINE)

    # マークを付けたテキストを生成する
    def mark(match):
        # マッチしたテキスト（章のタイトル）を取得
        chapter_title = match.group(0).strip()
        # マークを付けた章のタイトルを返す
        return f"<<Chapter>>{chapter_title}<</Chapter>>"

    # 章のタイトルにマークを付ける
    marked_text = chapter_pattern.sub(mark, text)

    # 連続する改行を一つに減らし、不要な空白を削除
    cleaned_text = re.sub(r"\n{2,}", "\n", marked_text)

    return cleaned_text


# 使用例
text = """
CHAPTER 1 Start of Adventure


end of epilogue



Start of Adventure

in the long time age, a hero...
"""

processed_text = mark_chapters(text)
print(processed_text)
