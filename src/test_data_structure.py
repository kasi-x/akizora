import pytest
from data_structure import Book
from data_structure import Chapter
from data_structure import Section
from data_structure import Sentence


def test_sentence_whitespace_removal():
    sentence = Sentence("  A sentence with leading and trailing spaces.  ")
    assert sentence.text == "A sentence with leading and trailing spaces."


def test_section_with_empty_sentence():
    section = Section()
    section.sentences.append(Sentence(""))
    assert section.sentences_count == 1
    # assert section.token_count == 0
    assert section.char_count == 0


def test_book_with_multiple_chapters():
    book = Book("Test Book")
    chapter1 = Chapter("Chapter 1")
    chapter1.sections.append(
        Section(sentences=[Sentence("First sentence."), Sentence("Second sentence.")]),
    )
    chapter2 = Chapter("Chapter 2")
    chapter2.sections.append(
        Section(
            sentences=[
                Sentence("Third sentence."),
                Sentence("Fourth sentence."),
                Sentence("Fifth sentence."),
            ],
        ),
    )
    book.chapters.extend([chapter1, chapter2])

    assert book.chapters_count == 2
    assert book.sections_count == 2
    assert book.sentences_count == 5
    # assert book.token_count == 10  # 仮定: 各文は2トークン


def test_sentence_with_only_spaces():
    sentence = Sentence("    ")
    assert sentence.token_count == 0  # 空白のみの文はトークンを持たない
    assert sentence.char_count == 0  # strip後、文字数は0になる


def test_complex_document_structure():
    book = Book(title="Complex Book")
    book.chapters.append(Chapter("Chapter 1"))
    book.chapters[0].sections.append(
        Section(sentences=[Sentence("First sentence."), Sentence("Second sentence.")]),
    )
    assert book.token_count == 4  # 仮に各文が2トークンとする
    assert book.char_count == len("First sentence.") + len("Second sentence.")
    assert book.sentences_count == 2
    assert book.sections_count == 1
    assert book.chapters_count == 1


def test_chapter_with_multiple_sections():
    section1 = Section(sentences=[Sentence("First sentence."), Sentence("Second sentence.")])
    section2 = Section(sentences=[Sentence("Third sentence.")])
    chapter = Chapter("Test Chapter", [section1, section2])
    assert chapter.sections_count == 2
    assert chapter.sentences_count == 3
    # assert chapter.token_count == 6
    assert chapter.char_count == sum(len(s.text) for s in section1.sentences + section2.sentences)


def test_chapter_with_multiple_sections_sentences():
    chapter = Chapter("Chapter 1")
    section1 = Section()
    section1.sentences.extend(
        [
            Sentence("First sentence of first section."),
            Sentence("Second sentence of first section."),
        ],
    )
    section2 = Section()
    section2.sentences.append(Sentence("Single sentence in second section."))
    chapter.sections.extend([section1, section2])

    assert chapter.sections_count == 2
    assert chapter.sentences_count == 3
    assert chapter.char_count == sum(len(s.text) for s in section1.sentences) + sum(
        len(s.text) for s in section2.sentences
    )


def test_empty_titles_in_chapters_and_books():
    empty_chapter = Chapter("", [])
    book_with_empty_chapter = Book("Book With Empty Chapter Title", [empty_chapter])
    assert book_with_empty_chapter.title == "Book With Empty Chapter Title"
    assert empty_chapter.chapter_title == ""  # 空のタイトルが保持される
    assert book_with_empty_chapter.chapters_count == 1


def test_empty_chapter_section_sentence():
    book = Book("Empty Book")
    book.chapters.append(Chapter("Empty Chapter"))
    book.chapters[0].sections.append(Section())

    assert book.chapters_count == 1
    assert book.sections_count == 1
    assert book.sentences_count == 0
