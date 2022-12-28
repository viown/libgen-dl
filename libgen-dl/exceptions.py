class DownloadLinkNotFound(BaseException):
    pass

class ChecksumMismatch(BaseException):
    pass

class GatewayDownloadFail(BaseException):
    pass

class FileNotFound(BaseException):
    pass