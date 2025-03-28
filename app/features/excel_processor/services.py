import pandas as pd
from openpyxl import load_workbook
from dataclasses import dataclass
from typing import Dict, Any, List

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
        if file_path.endswith('.csv'):
            # Read CSV file
            df = pd.read_csv(file_path)
            summary = self._generate_summary_from_dataframe(df, 'CSV')
        else:
            # Load the workbook to get sheet names and metadata
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
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheet_summary = self._generate_summary_from_dataframe(df, sheet_name)
                summary['sheet_summaries'][sheet_name] = sheet_summary
        
        return summary

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
        
        return summary
