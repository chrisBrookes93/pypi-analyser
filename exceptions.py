

class Exception404(Exception):
    def __init__(self, url):
        super(Exception, self).__init__('404 HTTP Error: ' + url)
