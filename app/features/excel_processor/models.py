class ExcelDocument:
    """Model for Excel document processing."""

    def __init__(self, filename, content, summary=None):
        self.filename = filename
        self.content = content
        self.summary = summary
