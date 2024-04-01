import re
from abc import ABC
from abc import abstractmethod

import lxml.html
import requests


class Scraper(ABC):
    def __init__(self, url):
        self.url = url
        self.response = requests.get(url)
        self.tree = lxml.html.fromstring(self.response.text)

    @abstractmethod
    def get_title(self):
        pass

    @abstractmethod
    def get_language(self):
        pass

    @abstractmethod
    def get_text(self):
        pass

    @abstractmethod
    def get_author(self):
        pass

    @abstractmethod
    def get_metadata(self):
        pass

    @abstractmethod
    def get_chapters(self):
        pass

    @abstractmethod
    def get_chapter(self, chapter):
        pass

    @abstractmethod
    def get_chapter_text(self, chapter):
        pass


class Gutenberg(ABC):
    def __init__(self, url):
        self.url = url
        self.response = requests.get(url)
        self.tree = lxml.html.fromstring(self.response.text)

    @staticmethod
    def _parse_ebook_metadata(text):
        metadata = {}
        for line in text.splitlines():
            match = re.match(r"(.*?):\s*(.*)", line)
            if match:
                key, value = match.groups()
                metadata[key] = value
        return metadata

    def _get_meta_data(self):
        return self.tree.xpath("/html/body/p[1]")[0].text_content()

    def get_title(self):
        return self._parse_ebook_metadata(self._get_meta_data())["Title"].split()

    def get_language(self):
        return self._parse_ebook_metadata(self._get_meta_data())["Language"].split()

    def get_author(self):
        return self._parse_ebook_metadata(self._get_meta_data())["Author"].split()

    def get_chapters(self):
        return [
            chapter.text_content()
            for chapter in self.tree.xpath("/html/body/h2")
            if chapter.text_content() != "Contents"
        ]  # First one is the table of contents

    def get_chapter(self, chapter_number: int):
        return self.get_chapters()[chapter_number]

    def get_chapter_text(self, chapter):
        return self.tree.xpath("/html/body/h3")[chapter].tail
