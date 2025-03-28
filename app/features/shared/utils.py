def format_date(date_obj, format_str='%Y-%m-%d'):
    """Format a date object to string."""
    return date_obj.strftime(format_str)
    
def validate_input(data, required_fields):
    """Validate that input data contains all required fields."""
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    return True, "Valid input"
