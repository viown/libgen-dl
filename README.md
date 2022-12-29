# libgen-dl
libgen-dl is a command-line tool for downloading books and other content from Library Genesis.
# Usage

    python libgen-dl.py [ID, MD5 or URL...]
   
A download path can be specified using `-p PATH`
# Searching
Searching libgen can be done like so:

    python libgen-dl.py --search Silent Spring
By default, the `libgen` topic will be searched.
A different topic can be specified using `--topic`

    python libgen-dl.py --search The Deep - Nick Cutter --topic fiction
Multiple topics can be specified by separating them with spaces.
The currently supported topics are:

 - libgen
 - fiction
 - fiction_rus
 - scimag
 - magazines
 - comics
 - standards

By default, `--search` will search by title and author only. To change this, use `--filter` to specify one or more filters. The available filters are: `title`, `author`, `series`, `year`, `publisher`, `isbn`
It's also possible to filter by language or format using `--language` and `--ext`
# Search and Download
Results from a search can be downloaded using the `-d` or `--download` flag.
Example:

    python libgen-dl.py -d --search The Dark Tower --filter series
# Info
Information about a specific book can be fetched using `--info`

    python libgen-dl.py --info [ID, MD5 or URL]
# Gateway
A gateway can be specified using the `--gateway` option. Available gateways are: `libgen`, `libgenlc`, `cloudflare`, `ipfs.io`, `crust`, `pinata`
Alternative gateways can be specified as well. For example:

    python libgen-dl.py [items...] --gateway cloudflare ipfs.io libgen
In this example, libgen-dl will first try downloading through the Cloudflare IPFS. If the download fails, it'll retry again with `ipfs.io`.  If that happens to fail as well, it'll finally try downloading directly from `gen.lib.rus.ec`.

When downloading books in bulk, it's recommended to have multiple gateways lined up just in case.
# Download all content
libgen-dl supports downloading all content from specific topic(s).
This operation can take a long time depending on the topic you're downloading from.
For example, to download all fictional books that are in english and in epub format:

    python libgen-dl.py --download-all --topic fiction --language English --ext epub -db content.db -p data
When `-db` is specified, libgen-dl will create an SQLite database containing information about every downloaded book. Specifying `-db` is optional, but highly recommended as it'll allow you to sync new books later on using the `--sync` option, as well as allow you to safely `CTRL+C` the download operation and resume it later by running the same command.

At least one topic has to be specified for `--download-all` to work. Check https://libgen.lc/stat.php to see the size of each topic.
# Sync
If you've previously used `--download-all` to download a copy of libgen, you can use `--sync` to keep it up to date. Simply point `--sync` to the database file to start syncing.

    python libgen-dl.py --sync [DB_PATH]

