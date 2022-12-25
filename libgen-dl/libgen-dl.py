import argparse
import os
from tabulate import tabulate
from search import SearchRequest

__version__ = "0.10.1"

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
    parser.add_argument("-s", "--search",
                        help="searches libgen from the given query", nargs='+')
    parser.add_argument("-f", "--filter",
                        help="filter by title, author, series, year, publisher or ISBN when searching. Default is title + author.",
                        default=["title", "author"], choices=["title", "author", "series", "year", "publisher", "isbn"],
                        nargs='+')
    parser.add_argument("-t", "--topic",
                        help="filter by topic. Available topics are: libgen, fiction, fiction_rus, scimag, magazines, comics, standarts. Multiple topics can be specified by separating them with a space",
                        nargs='+',
                        default=["libgen"], choices=["libgen", "fiction", "fiction_rus", "scimag", "magazines", "comics", "standarts"])
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
    parser.add_argument("-all", "--download-all",
                        help="will attempt to download all content in a specific topic. A --topic must be specified",
                        action='store_true')
    parser.add_argument("-db", "--database",
                        help="optionally used alongside --download-all. Creates an SQLite database containing the information of the media that was downloaded",
                        metavar=('PATH'))

    args = parser.parse_args()

    if args.search:
        query = ' '.join(args.search)
        request = SearchRequest(query=query, filters=args.filter, topics=args.topic,
                                language=args.language, ext=args.ext)
        results = request.get_results()
        toPrint = results
        for result in toPrint:
            del result["isbn"]
            del result["pages"]
            if len(result["title"]) > 35:
                result["title"] = result["title"][:35] + "..."
        print(tabulate([list(result.values()) for result in results], headers=["ID", "Title", "Author(s)", "Publisher", "Year", "Language", "Size (MB)", "Format"]))

        if args.download is not None:
            ## TODO: Download all results
            pass

if __name__ == "__main__":
    main()