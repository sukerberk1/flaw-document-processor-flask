import logging
import pandas as pd
from openpyxl import load_workbook
from dataclasses import dataclass
import openai
from typing import Dict, Any, List

# Ensure to set your OpenAI API key
openai.api_key = 'your-api-key-here'

@dataclass
class ExcelDocument:
    filename: str
    summary: Dict[str, Any]

class ExcelProcessorService:
    def process_excel(self, file_path: str) -> Dict[str, Any]:
        """
        Process an Excel file and extract useful information.
        
        Args:
            file_path: Path to the uploaded Excel file
            
        Returns:
            Dictionary containing summary information about the Excel file
        """
        logging.debug(f"Processing file: {file_path}")
        if file_path.endswith('.csv'):
            # Read CSV file
            logging.debug("Reading CSV file.")
            df = pd.read_csv(file_path)
            summary = self._generate_summary_from_dataframe(df, 'CSV')
        else:
            # Load the workbook to get sheet names and metadata
            logging.debug("Loading Excel workbook.")
            workbook = load_workbook(file_path, read_only=True, data_only=True)
            
            # Get basic information
            summary = {
                'sheet_names': workbook.sheetnames,
                'active_sheet': workbook.active.title,
                'sheet_summaries': {}
            }
            
            # Use pandas to read each sheet and get statistics
            for sheet_name in workbook.sheetnames:
                # Read sheet with pandas
                logging.debug(f"Reading sheet: {sheet_name}")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheet_summary = self._generate_summary_from_dataframe(df, sheet_name)
                summary['sheet_summaries'][sheet_name] = sheet_summary
        
        logging.debug(f"Generated summary before return: {summary}")
        # Generate a text summary using ChatGPT
        text_summary = self._generate_text_summary(summary)
        logging.debug(f"Generated text summary: {text_summary}")
        return {'summary': summary, 'text_summary': text_summary}

    def _generate_text_summary(self, summary: Dict[str, Any]) -> str:
        """Generate a text summary using ChatGPT."""
        prompt = f"Summarize the following Excel data summary in plain English:\n{summary}"
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=150
            )
            return response.choices[0].text.strip()
        except Exception as e:
            logging.error(f"Error generating text summary: {e}")
            return "Failed to generate text summary."

    def _generate_summary_from_dataframe(self, df, sheet_name):
        """Generate a summary from a DataFrame."""
        sheet_summary = {
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist(),
            'numeric_columns': df.select_dtypes(include=['number']).columns.tolist(),
            'non_null_counts': df.count().to_dict(),
        }
        
        # Add basic statistics for numeric columns
        if len(sheet_summary['numeric_columns']) > 0:
            stats = df[sheet_summary['numeric_columns']].describe().to_dict()
            sheet_summary['statistics'] = stats
        
        return sheet_summary
