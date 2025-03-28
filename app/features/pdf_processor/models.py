class PDFDocument:
    """Model for PDF document processing."""
    
    def __init__(self, filename, content, summary=None):
        self.filename = filename
        self.content = content
        self.summary = summary 