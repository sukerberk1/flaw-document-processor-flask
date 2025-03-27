import pandas as pd
from typing import List, Dict

class ExcelExtractor:
    """Extracts text content from Excel files."""
    
    def extract_text(self, excel_file) -> str:
        """
        Extract text from an Excel file.
        
        Args:
            excel_file: File-like object containing Excel data
            
        Returns:
            str: Extracted text content
        """
        try:
            # Read all sheets
            excel_data = pd.read_excel(excel_file, sheet_name=None)
            
            # Extract text from each sheet
            text_content = []
            
            for sheet_name, df in excel_data.items():
                # Add sheet name as a heading
                text_content.append(f"Sheet: {sheet_name}")
                
                # Fill NaN values with empty string to avoid issues when converting to string
                df = df.fillna("")
                
                # Get column headers
                headers = df.columns.tolist()
                text_content.append("Headers: " + ", ".join(str(h) for h in headers))
                
                # Convert each row to text
                for _, row in df.iterrows():
                    row_text = " | ".join(f"{headers[i]}: {str(value)}" for i, value in enumerate(row) if str(value).strip())
                    if row_text:
                        text_content.append(row_text)
                
                # Add a separator between sheets
                text_content.append("\n")
            
            return "\n".join(text_content)
            
        except Exception as e:
            raise Exception(f"Error extracting text from Excel: {str(e)}")
    
    def get_metadata(self, excel_file) -> Dict:
        """
        Extract metadata from an Excel file.
        
        Args:
            excel_file: File-like object containing Excel data
            
        Returns:
            Dict: Metadata about the Excel file
        """
        try:
            # Read all sheets
            excel_data = pd.read_excel(excel_file, sheet_name=None)
            
            # Collect metadata
            sheet_count = len(excel_data)
            total_rows = sum(df.shape[0] for df in excel_data.values())
            total_columns = sum(df.shape[1] for df in excel_data.values())
            sheet_names = list(excel_data.keys())
            
            return {
                "sheet_count": sheet_count,
                "total_rows": total_rows,
                "total_columns": total_columns,
                "sheet_names": sheet_names
            }
            
        except Exception as e:
            raise Exception(f"Error extracting metadata from Excel: {str(e)}")
