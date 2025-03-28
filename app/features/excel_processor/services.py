import pandas as pd

class ExcelProcessorService:
    """Service for processing Excel files and generating summaries."""

    def __init__(self):
        pass

    def read_excel(self, file_path):
        """Read an Excel file and return its content."""
        try:
            df = pd.read_excel(file_path)
            return df.to_string()
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {e}")

    def generate_summary(self, text, max_length=500):
        """Generate a summary of the given text."""
        # Simple summary logic (can be replaced with more complex algorithms)
        return text[:max_length]

    def process_excel(self, file_path):
        """Process an Excel file and generate a summary."""
        content = self.read_excel(file_path)
        summary = self.generate_summary(content)
        return summary
