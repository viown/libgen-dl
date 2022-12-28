import requests
import book
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup

class SearchRequest:
    def __init__(self, query, filters, topics, language=None, ext=None, page=1):
        self.query = query
        self.filters = filters
        self.topics = topics
        self.language = language
        self.ext = ext
        self.page = page

    def search_page(self):
        params = {
            "req": self.query,
            "res": 100,
            "columns[]": [filter[0].lower() for filter in self.filters],
            "topics[]": [topic[0].lower() for topic in self.topics],
            "objects[]": "f",
            "page": self.page
        }
        return requests.get("https://libgen.lc/index.php", params=params)

    def convert_size_string_to_mb(self, str):
        s = str.split(' ')
        if s[1].lower() == "mb":
            return float(s[0])
        elif s[1].lower() == "kb":
            return round(float(s[0]) / 1000, 2)
        else:
            return str

    def get_results(self):
        pageData = self.search_page()

        results = []

        soup = BeautifulSoup(pageData.content, "lxml")

        table = soup.find("table", {"id": "tablelibgen"})
        if not table:
            return []

        table = table.find("tbody")


        for result in table.findAll("tr"):
            result_info = result.findAll("td")
            title_section = result_info[0].findAll("a", recursive=False)

            url = "https://libgen.lc/" + title_section[0].get("href")

            if len(title_section) > 1 and title_section[1].find("font"):
                isbn = [n.strip() for n in title_section[1].find("font").text.split(';')]
            else:
                isbn = None


            item = book.Book(edition_id=parse_qs(urlparse(url).query)["id"][0],
                        title=title_section[0].text.strip(),
                        author=result_info[1].text.strip(),
                        publisher=result_info[2].text,
                        isbn=isbn,
                        year=result_info[3].text if result_info[3].text != "" else None,
                        lang=result_info[4].text,
                        pages=result_info[5].text if result_info[5].text != "0" else None,
                        size=self.convert_size_string_to_mb(result_info[6].text),
                        format=result_info[7].text,
                        mirrors=[mirror.get("href") for mirror in result_info[8].findAll("a")]
                        )

            if self.ext:
                if item.format != self.ext.lower():
                    continue
            if self.language:
                if item.lang != self.language.lower():
                    continue

            results.append(item)
        return results