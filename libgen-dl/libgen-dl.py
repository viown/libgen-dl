import argparse
import os
import requests
from tabulate import tabulate
from book import get_book_from_id, get_book_from_md5
from search import SearchRequest

__version__ = "0.10.1"

def truncate(s, maximumLength):
    if len(s) > maximumLength:
        return s[:maximumLength] + "..."
    return s

def get_book_from_argument(arg):
    if len(arg) == 32:
        return get_book_from_md5(arg)
    elif arg.isdigit():
        return get_book_from_id(arg)
    # TODO: Check if it's a URL as well

def download(arg_list, gateway_list, path, download_cover, create_metadata):
    for argument in arg_list:
        book = get_book_from_argument(argument)
        if book:
            book.download_with_retry(path=path, gateway_list=gateway_list, output=True)

def main():
    parser = argparse.ArgumentParser(prog='libgen-dl', description='Content downloader for libgen.')

    parser.add_argument("id",
                        help="The ID, MD5 or URL of the content to download.",
                        nargs='*')
    parser.add_argument("-v", "--version",
                        help="displays current version",
                        action="version",
                        version="v"+__version__)
    parser.add_argument("-d", "--download",
                        help="downloads one or multiple items given the ID, MD5 or URL. Can also be used alongside --search to download all results",
                        nargs="*")
    parser.add_argument("-i", "--info",
                        help="displays content information from the given ID, MD5 or URL")
    parser.add_argument("-s", "--search",
                        help="searches libgen from the given query",
                        nargs='+')
    parser.add_argument("-f", "--filter",
                        help="filter by title, author, series, year, publisher or ISBN when searching. Default is title + author.",
                        default=["title", "author"], choices=["title", "author", "series", "year", "publisher", "isbn"],
                        nargs='+')
    parser.add_argument("-t", "--topic",
                        help="filter by topic. Available topics are: libgen, fiction, fiction_rus, scimag, magazines, comics, standards. Multiple topics can be specified by separating them with a space",
                        nargs='+',
                        default=["libgen"], choices=["libgen", "fiction", "fiction_rus", "scimag", "magazines", "comics", "standards"])
    parser.add_argument("-l", "--language",
                        help="filter by language")
    parser.add_argument("-e", "--ext",
                        help="filter by extension")
    parser.add_argument("-p", "--path",
                        help="specifies a path. Default is .",
                        default=os.getcwd())
    parser.add_argument("--download-cover",
                        help="downloads the cover image",
                        action='store_true')
    parser.add_argument("--create-metadata",
                        help="creates an OPF file containing information about the downloaded content",
                        action="store_true")
    parser.add_argument("-g", "--gateway",
                        help="specifies the gateway to use",
                        nargs='+',
                        default=["libgenlc"])
    parser.add_argument("-all", "--download-all",
                        help="download all content from the specified topic(s). At least one topic has to be specified.",
                        action='store_true')
    parser.add_argument("-db", "--database",
                        help="optionally used alongside --download-all. Creates an SQLite database containing the information of the media that was downloaded",
                        metavar=('PATH'))
    parser.add_argument("--sync",
                        help="syncs a previously downloaded database",
                        metavar=('DB_PATH'))

    args = parser.parse_args()

    if args.search:
        query = ' '.join(args.search)
        request = SearchRequest(query=query, filters=args.filter, topics=args.topic,
                                language=args.language, ext=args.ext)
        results = request.get_results()
        print(tabulate([[result.edition_id, truncate(result.title, 35), result.author, truncate(result.publisher, 45), result.year, result.lang, result.size, result.format] for result in results],
                        headers=["ID", "Title", "Author(s)", "Publisher", "Year", "Language", "Size (MB)", "Format"]))

        if args.download is not None:
            for result in results:
                try:
                    result.download_with_retry(path=args.path, gateway_list=args.gateway, output=True)
                except requests.exceptions.HTTPError:
                    print(f"An error occured while downloading {result.title}. Skipped.")
    
    elif args.info:
        book = get_book_from_argument(args.info)

        if book:
            print(f"ID          :   {book.edition_id}")
            print(f"Title       :   {book.title}")
            print(f"Author      :   {book.author}")
            print(f"Publisher   :   {book.publisher}")
            if book.isbn:
                print(f"ISBN        :   {', '.join(book.isbn)}")
            if book.year:
                print(f"Year        :   {book.year}")
            if book.lang:
                print(f"Language    :   {book.lang}")
            if book.description:
                print(f"Description :   {book.description}\n")
            if book.size:
                print(f"Size        :   {book.size} MB")
            if book.format:
                print(f"Extension   :   {book.format}")
            if book.md5:
                print(f"MD5         :   {book.md5}")
            if book.topic:
                print(f"Topic       :   {book.topic}")
    elif args.download and not (args.search):
        download(args.id, args.gateway, path=args.path, download_cover=args.download_cover, create_metadata=args.create_metadata)
    else:
        download(args.id, args.gateway, path=args.path, download_cover=args.download_cover, create_metadata=args.create_metadata)

if __name__ == "__main__":
    main()