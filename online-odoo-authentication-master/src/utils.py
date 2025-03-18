"""
Utility functions for the Online Odoo Authentication module.
"""
import logging
import datetime
import pytz

_logger = logging.getLogger(__name__)

def format_date(date_obj, format_str='%Y-%m-%d %H:%M:%S'):
    """
    Format a datetime object as a string.
    
    Args:
        date_obj (datetime): The datetime object to format
        format_str (str): The format string to use
        
    Returns:
        str: The formatted date string
    """
    if not date_obj:
        return ''
    
    return date_obj.strftime(format_str)

def convert_timezone(date_obj, from_tz='UTC', to_tz='UTC'):
    """
    Convert a datetime object from one timezone to another.
    
    Args:
        date_obj (datetime): The datetime object to convert
        from_tz (str): The source timezone
        to_tz (str): The target timezone
        
    Returns:
        datetime: The converted datetime object
    """
    if not date_obj:
        return None
    
    from_timezone = pytz.timezone(from_tz)
    to_timezone = pytz.timezone(to_tz)
    
    if date_obj.tzinfo is None:
        date_obj = from_timezone.localize(date_obj)
        
    return date_obj.astimezone(to_timezone)

def log_error(message, exception=None):
    """
    Log an error message.
    
    Args:
        message (str): The error message
        exception (Exception, optional): The exception that caused the error
    """
    if exception:
        _logger.error("%s: %s", message, str(exception))
    else:
        _logger.error(message)

def validate_url(url):
    """
    Validate a URL.
    
    Args:
        url (str): The URL to validate
        
    Returns:
        bool: True if the URL is valid, False otherwise
    """
    if not url:
        return False
    
    # Simple validation - check if the URL starts with http:// or https://
    return url.startswith('http://') or url.startswith('https://')

def get_current_timestamp():
    """
    Get the current timestamp.
    
    Returns:
        str: The current timestamp in ISO format
    """
    return datetime.datetime.now().isoformat() 