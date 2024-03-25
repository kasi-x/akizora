import re


def save_text_sections(text):
    # 正規表現パターンを定義
    chapter_pattern = r"\bCHAPTER\s+\d+\b"  # "CHAPTER" followed by one or more digits
    section_pattern = r"\bSECTION\s+\d+\b"  # "SECTION" followed by one or more digits
    noise_pattern = r"^(?!_).*\n"  # Lines not starting with an underscore

    # 正規表現パターンを使って章とセクションの位置を見つける
    chapter_matches = re.finditer(chapter_pattern, text)
    section_matches = re.finditer(section_pattern, text)

    # 章の位置をリストに保存
    chapter_positions = [match.start() for match in chapter_matches]
    chapter_positions.append(len(text))  # 最後の章の位置を追加

    # セクションの位置をリストに保存
    section_positions = [match.start() for match in section_matches]
    section_positions.append(len(text))  # 最後のセクションの位置を追加

    # ノイズの位置をリストに保存
    noise_matches = re.finditer(noise_pattern, text)
    [match.start() for match in noise_matches]

    # テキストを章ごとに分割して保存
    for i in range(len(chapter_positions) - 1):
        start = chapter_positions[i]
        end = chapter_positions[i + 1]
        chapter_text = text[start:end].strip()  # 章のテキストを取得してトリム
        chapter_title = chapter_text.split("\n", 1)[0]  # 章のタイトルを取得
        # テキストを保存
        with open(f"chapter_{i + 1}_{chapter_title}.txt", "w") as file:
            file.write(chapter_text)

    # セクションがあれば、それぞれのセクションを章ごとに分割して保存
    if section_positions != [len(text)]:
        for i in range(len(chapter_positions) - 1):
            start = chapter_positions[i]
            end = chapter_positions[i + 1]
            section_text = text[start:end].strip()  # セクションのテキストを取得してトリム
            section_title = section_text.split("\n", 1)[0]  # セクションのタイトルを取得
            # テキストを保存
            with open(f"chapter_{i + 1}_section_{i + 1}_{section_title}.txt", "w") as file:
                file.write(section_text)


# テキストを読み込む
with open("sample.txt") as file:
    text = file.read()

# テキストを章とセクションに分割して保存
save_text_sections(text)
