"""CSV reader utilities for loading contact data."""

import csv
import os
from typing import List, Dict, Any


def load_contacts(file_path: str = None) -> List[Dict[str, Any]]:
    """Load contacts from a CSV file.
    
    Args:
        file_path: Path to the CSV file. If None, uses default test data path.
        
    Returns:
        List of dictionaries containing contact information.
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist.
        ValueError: If the CSV file is malformed.
    """
    if file_path is None:
        # Default to test data file
        file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'test', 'testdata.csv')
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    contacts = []
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                contacts.append(dict(row))
    except Exception as e:
        raise ValueError(f"Error reading CSV file {file_path}: {str(e)}")
    
    return contacts


def validate_contact_data(contacts: List[Dict[str, Any]]) -> bool:
    """Validate that contact data has required fields.
    
    Args:
        contacts: List of contact dictionaries.
        
    Returns:
        True if all contacts have required fields, False otherwise.
    """
    required_fields = ['email']
    
    for contact in contacts:
        for field in required_fields:
            if field not in contact or not contact[field]:
                return False
    
    return True