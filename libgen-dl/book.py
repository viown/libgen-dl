from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from exceptions import DownloadLinkNotFound, ChecksumMismatch, GatewayDownloadFail, FileNotFound
import requests
import hashlib
import search
import re
import os
import time
import pyrfc6266

MIRROR_SOURCES = ["GET", "Cloudflare", "IPFS.io", "Crust", "Pinata"]

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

    def get_mirror(self, domains):
        for mirror in self.mirrors:
            if urlparse(mirror).netloc in domains:
                return mirror
        return None

    def get_download_link(self, gateway):
        if gateway == "libgenlc":
            mirror = self.get_mirror(["libgen.rocks", "libgen.lc"])
        elif gateway in ["libgen", "cloudflare", "ipfs.io", "crust", "pinata"]:
            mirror = self.get_mirror(["library.lol", "gen.lib.rus.ec"])
        r = requests.get(mirror)
        links = {"get": None, "cloudflare": None, "ipfs.io": None, "crust": None, "pinata": None}
        if r.ok:
            soup = BeautifulSoup(r.content, 'lxml')
            for source in MIRROR_SOURCES:
                link = soup.find("a", string=source)
                if link:
                    link = link.get("href")
                    if not link.startswith("http"):
                        link = "https://" + urlparse(mirror).netloc + '/' + link
                    links[source.lower()] = link
            if gateway in ["libgen", "libgenlc"]:
                return links["get"]
            else:
                return links[gateway]
        elif r.status_code == 404:
            raise FileNotFound(f"File could not be found through mirror {mirror}")

    def verify_file(self, path):
        with open(path, "rb") as f:
            fileSum = hashlib.md5(f.read()).hexdigest().lower()
            if fileSum == self.md5.lower():
                return True
            else:
                raise ChecksumMismatch(f"MD5 checksum mismatch with {path}. Expected {self.md5}, instead got {fileSum}")

    def download_cover(self, path):
        if not self.cover:
            r = requests.get(self.get_mirror(["library.lol", "gen.lib.rus.ec"]))
            if r.ok:
                soup = BeautifulSoup(r.content, 'lxml')
                cover = soup.find("img").get("src")
                if not cover.startswith("http"):
                    self.cover = "http://" + urlparse(r.url).netloc + soup.find("img").get("src")
                else:
                    self.cover = cover
        if self.cover:
            r = requests.get(self.cover)
            with open(path, "wb") as f:
                f.write(r.content)

    def download(self, path, verify=True, output=False, timeout=None, gateway="libgenlc"):
        download_link = self.get_download_link(gateway)
        if download_link:
            if output:
                print(f"Using download link {download_link}")
            with requests.get(download_link, allow_redirects=True, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                content_disposition = r.headers["Content-Disposition"]
                filename = pyrfc6266.parse_filename(content_disposition)
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
                                print(f"Downloading {filename} ({str(percent_downloaded)}%) ({str(megabytes_per_second)} MB/s) (gateway={gateway})", end='\r')
                            else:
                                print(f"Downloading {filename} ({str(percent_downloaded)}%)", end='\r')

                if output:
                    print(end='\n')

                if verify:
                    if self.md5:
                        if output:
                            print(f"Verifying {fullpath}")
                        if self.verify_file(fullpath):
                            if output:
                                print("Verification successful. Download complete.")
                    else:
                        if output:
                            print("Download completed but file integrity could not be verified.")
                else:
                    if output:
                        print("Download completed")

                return fullpath
        else:
            raise DownloadLinkNotFound("Could not fetch download link. Perhaps libgen is down?")

    def download_with_retry(self, gateway_list, output=False, *args, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = 10
        downloadCompleted = False
        gateway = 0
        while True:
            try:
                path = self.download(*args, **kwargs, output=output, gateway=gateway_list[gateway])
                if path:
                    return path
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                if output:
                    print(f"Gateway {gateway_list[gateway]} failed. Retrying with another gateway.")
                gateway += 1
                if (gateway + 1) > len(gateway_list):
                    raise GatewayDownloadFail("All specified gateways failed to respond")

if __name__ == "__main__":
    book = get_book_from_id(5240666)
    book.download_cover("cover.jpg")