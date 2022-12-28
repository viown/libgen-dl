from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from exceptions import DownloadLinkNotFound, ChecksumMismatch
import requests
import hashlib
import search
import re
import os
import time

topic_map = {
    "l": "libgen",
    "c": "comics",
    "f": "fiction",
    "a": "scientific articles",
    "m": "magazines",
    "r": "fiction_rus",
    "s": "standards"
}


def get_book_from_md5(md5):
    search_request = search.SearchRequest(f"md5:{md5}", filters=["title"], topics=["libgen", "comics", "fiction", "magazines", "fiction_rus", "standards"])
    results = search_request.get_results()
    if results:
        return results[0]

def get_book_from_id(id):
    r = requests.get(f"https://libgen.lc/json.php?object=e&addkeys=*&ids={id}")
    if r.ok:
        data = r.json()[str(id)]
        md5 = list(data["files"].values())[0]["md5"]
        book = get_book_from_md5(md5)

        book.topic = topic_map[data["libgen_topic"]]
        for add in list(data["add"].values()):
            if add["name_en"].lower() == "description":
                book.description = add["value"]
            elif add["name_en"].lower() == "isbn":
                book.isbn.append(add["value"])
        
        return book


class Book:
    def __init__(self, title, author, edition_id=None, publisher=None, isbn=[],
                year=None, cover=None, lang=None, pages=None, description=None,
                size=None, format=None, md5=None, topic=None, mirrors=None):
        self.edition_id = edition_id
        self.title = title
        self.author = author
        self.publisher = publisher
        self.isbn = isbn
        self.year = year
        self.cover = cover
        self.lang = lang.lower()
        self.pages = pages
        self.description = description
        self.size = size
        self.format = format.lower()
        self.md5 = md5
        self.topic = topic
        self.mirrors = mirrors

        if not self.md5 and self.mirrors:
            self.md5 = self.get_md5_from_mirrors()

    def get_md5_from_mirrors(self):
        for mirror in self.mirrors:
            url = urlparse(mirror)
            if url.netloc == "libgen.rocks" or url.netloc == "libgen.lc":
                return parse_qs(url.query)["md5"][0]

    def get_download_link(self):
        for mirror in self.mirrors:
            r = requests.get(mirror)
            if r.ok:
                soup = BeautifulSoup(r.content, 'lxml')
                get_link = soup.find("a", string="GET")
                if get_link:
                    link = get_link.get("href")
                    if not link.startswith("http"):
                        link = "https://" + urlparse(mirror).netloc + '/' + link
                    return link
        return None

    def download(self, path, verify=True, output=False):
        download_link = self.get_download_link()
        if download_link:
            with requests.get(download_link, allow_redirects=True, stream=True) as r:
                r.raise_for_status()
                content_disposition = r.headers["Content-Disposition"]
                filename = re.findall("filename=(.+)", content_disposition)[0].replace('"', '')
                filesize = int(r.headers["Content-Length"])
                fullpath = os.path.join(path, filename)

                bytesDownloaded = 0
                timeStarted = time.time()

                with open(fullpath, "wb") as content:
                    for chunk in r.iter_content(chunk_size=8192):
                        content.write(chunk)
                        bytesDownloaded += len(chunk)
                        if output:
                            percent_downloaded = round((bytesDownloaded / filesize) * 100, 2)
                            seconds_elapsed = time.time() - timeStarted
                            if seconds_elapsed != 0:
                                megabytes_per_second = round((bytesDownloaded / seconds_elapsed) / 1e+6, 2)
                                print(f"Downloading {filename} ({str(percent_downloaded)}%) ({str(megabytes_per_second)} MB/s)", end='\r')
                            else:
                                print(f"Downloading {filename} ({str(percent_downloaded)}%)", end='\r')

                if output:
                    print(end='\n')

                if verify:
                    if self.md5:
                        if output:
                            print(f"Verifying {fullpath}...")
                        with open(fullpath, "rb") as f:
                            fileSum = hashlib.md5(f.read()).hexdigest().lower()
                            if fileSum == self.md5.lower():
                                if output:
                                    print("Verified. Download completed.")
                            else:
                                raise ChecksumMismatch(f"MD5 checksum mismatch with {fullpath}. Expected {self.md5}, instead got {fileSum}")
                    else:
                        print("Download completed but could not be verified.")
                else:
                    if output:
                        print("Download completed")


        else:
            raise DownloadLinkNotFound("Could not fetch download link. Perhaps libgen is down?")

if __name__ == "__main__":
    book = get_book_from_id(142225964)
    print(book.download(os.getcwd(), output=True))