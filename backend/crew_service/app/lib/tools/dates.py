from datetime import datetime
from typing import Union
from crewai.tools import tool


def _parse_date(date_str: str) -> datetime:
    """
    Parse a date string in various formats.
    Supports:
    - ISO format: '2024-01-01' or '2024-01-01T00:00:00Z'
    - DD-MMM-YYYY: '01-Nov-2024'
    - DD/MM/YYYY: '01/11/2024'
    - YYYY-MM-DD: '2024-11-01'
    """
    date_str = date_str.strip()
    
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00').split('T')[0])
    except (ValueError, AttributeError):
        pass
    
    try:
        return datetime.strptime(date_str, '%d-%b-%Y')
    except ValueError:
        pass
    
    try:
        return datetime.strptime(date_str, '%d/%m/%Y')
    except ValueError:
        pass
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        pass
    
    try:
        return datetime.strptime(date_str, '%d-%m-%Y')
    except ValueError:
        pass
    
    raise ValueError(f"Unable to parse date: {date_str}. Supported formats: ISO (YYYY-MM-DD), DD-MMM-YYYY, DD/MM/YYYY")


def calculate_num_weeks_impl(start_date: str, end_date: str) -> int:
    """
    Calculates the number of weeks between a start date and an end date (inclusive).
    
    The calculation includes both the start and end dates, so a single week period
    (e.g., Monday to Sunday) returns 1 week.
    
    This is the core implementation that can be reused without the CrewAI tool wrapper.
    
    Args:
        start_date: Start date in various formats:
            - ISO format: '2024-01-01' or '2024-01-01T00:00:00Z'
            - DD-MMM-YYYY: '01-Nov-2024'
            - DD/MM/YYYY: '01/11/2024'
            - YYYY-MM-DD: '2024-11-01'
        end_date: End date in the same formats as start_date.
    
    Returns:
        int: The number of weeks between the dates (inclusive, rounded up).
    
    Examples:
        - start_date: "01-Nov-2024", end_date: "30-Nov-2024" -> 5 weeks
        - start_date: "2024-01-01", end_date: "2024-01-07" -> 1 week
    """
    try:
        start = _parse_date(start_date)
        end = _parse_date(end_date)
        
        if end < start:
            return 0
        
        delta = end - start
        days = delta.days + 1
        
        weeks = (days + 6) // 7
        
        return weeks
    except Exception as e:
        raise ValueError(f"Error calculating weeks: {e}")


@tool("calculate number of weeks")
def calculate_num_weeks(start_date: str, end_date: str) -> int:
    """
    Calculates the number of weeks between a start date and an end date (inclusive).
    
    The calculation includes both the start and end dates, so a single week period
    (e.g., Monday to Sunday) returns 1 week.
    
    Args:
        start_date: Start date in various formats:
            - ISO format: '2024-01-01' or '2024-01-01T00:00:00Z'
            - DD-MMM-YYYY: '01-Nov-2024'
            - DD/MM/YYYY: '01/11/2024'
            - YYYY-MM-DD: '2024-11-01'
        end_date: End date in the same formats as start_date.
    
    Returns:
        int: The number of weeks between the dates (inclusive, rounded up).
    
    Examples:
        - start_date: "01-Nov-2024", end_date: "30-Nov-2024" -> 5 weeks
        - start_date: "2024-01-01", end_date: "2024-01-07" -> 1 week
    """
    return calculate_num_weeks_impl(start_date, end_date)