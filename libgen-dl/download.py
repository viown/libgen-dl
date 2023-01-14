from collections import deque
import threading


class DownloadRequest:
    """
    This class is for handling --download-all operations.
    """
    def __init__(self, dlpath, dbpath=None, gateways=[], language=None, ext=None, topics=None, filters=None):
        self.dlpath = dlpath
        self.dbpath = dbpath
        self.gateways = gateways
        self.language = language
        self.ext = ext
        self.topics = topics
        self.filters = filters

        """
        Pages will be traversed backwards so that new books added to libgen don't interfere with the download operation.
        The new books can then be synced after the operation is complete with --sync.
        """
        self.page_start = None
        self.page_end = 1

        """
        Content that hasn't been downloaded yet are placed in a thread-safe queue.
        """
        self.queue = deque()