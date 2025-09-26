"""Contact CSV parser for email campaigns.

This module provides unified CSV parsing functionality for contact data,
ensuring each contact is returned as a properly structured dictionary.
"""

import csv
import os
import re
from typing import List, Dict, Any, Optional


class ContactParseError(Exception):
    """Exception raised when contact parsing fails."""
    pass


def parse_contacts_from_csv(csv_file_path: str) -> List[Dict[str, Any]]:
    """Parse contacts from a CSV file and return as a list of contact dictionaries.
    
    Args:
        csv_file_path: Path to the CSV file containing contact data.
        
    Returns:
        List of contact dictionaries, each containing:
        - email: Contact's email address
        - first_name: First name extracted from contact name
        - contact_name: Full contact name
        - entity_name: Business/entity name (if available)
        - license_number: License number (if available)
        - business_website: Website URL (if available)
        - address: Full address information (if available)
        
    Raises:
        ContactParseError: If the CSV file cannot be read or parsed.
        FileNotFoundError: If the CSV file doesn't exist.
    """
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
    
    contacts = []
    
    try:
        with open(csv_file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 for header row
                try:
                    contact = _parse_contact_row(row)
                    if contact:  # Only add valid contacts
                        contacts.append(contact)
                except Exception as e:
                    print(f"Warning: Skipping row {row_num} due to parsing error: {e}")
                    continue
        
        print(f"Successfully parsed {len(contacts)} valid contacts from {csv_file_path}")
        return contacts
        
    except Exception as e:
        raise ContactParseError(f"Error reading CSV file {csv_file_path}: {str(e)}")


def _parse_contact_row(row: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Parse a single CSV row into a contact dictionary.
    
    Args:
        row: Dictionary representing a CSV row.
        
    Returns:
        Contact dictionary or None if the row is invalid.
    """
    # Extract and validate email
    email = row.get("Email", "").strip()
    if not email or not _is_valid_email(email):
        return None
    
    # Extract contact name and derive first name
    contact_name = row.get("Primary Contact Name", "").strip()
    first_name = _extract_first_name(contact_name)
    
    # Build address from available fields
    address_parts = []
    for field in ["Address Line 1", "Address Line 2", "City", "State", "Zip Code"]:
        value = row.get(field, "").strip()
        if value:
            address_parts.append(value)
    
    full_address = ", ".join(address_parts) if address_parts else ""
    
    # Create contact dictionary preserving all original CSV fields
    contact = {
        # Original CSV fields (preserve exact column names)
        "License Number": row.get("License Number", "").strip(),
        "License Type": row.get("License Type", "").strip(),
        "License Type Code": row.get("License Type Code", "").strip(),
        "License Status": row.get("License Status", "").strip(),
        "License Status Code": row.get("License Status Code", "").strip(),
        "Issued Date": row.get("Issued Date", "").strip(),
        "Effective Date": row.get("Effective Date", "").strip(),
        "Expiration Date": row.get("Expiration Date", "").strip(),
        "Application Number": row.get("Application Number", "").strip(),
        "Entity Name": row.get("Entity Name", "").strip(),
        "Address Line 1": row.get("Address Line 1", "").strip(),
        "Address Line 2": row.get("Address Line 2", "").strip(),
        "City": row.get("City", "").strip(),
        "State": row.get("State", "").strip(),
        "Zip Code": row.get("Zip Code", "").strip(),
        "County": row.get("County", "").strip(),
        "Region": row.get("Region", "").strip(),
        "Business Website": row.get("Business Website", "").strip(),
        "Operational Status": row.get("Operational Status", "").strip(),
        "Business Purpose": row.get("Business Purpose", "").strip(),
        "Tier Type": row.get("Tier Type", "").strip(),
        "Processor Type": row.get("Processor Type", "").strip(),
        "Primary Contact Name": row.get("Primary Contact Name", "").strip(),
        "Email": row.get("Email", "").strip(),
        
        # Additional tracking fields for email processing
        "first_name": first_name,
    }
    
    return contact


def _extract_first_name(contact_name: str) -> str:
    """Extract first name from a full contact name.
    
    Args:
        contact_name: Full contact name string.
        
    Returns:
        First name or empty string if extraction fails.
    """
    if not contact_name:
        return ""
    
    # Handle common name formats
    name_parts = contact_name.strip().split()
    
    if not name_parts:
        return ""
    
    # Return the first part as first name
    first_name = name_parts[0]
    
    # Clean up common prefixes/titles
    prefixes_to_remove = ["mr.", "mrs.", "ms.", "dr.", "prof."]
    first_name_lower = first_name.lower().rstrip(".")
    
    if first_name_lower in prefixes_to_remove and len(name_parts) > 1:
        first_name = name_parts[1]
    
    # Remove any non-alphabetic characters and capitalize
    first_name = re.sub(r'[^a-zA-Z]', '', first_name)
    return first_name.capitalize() if first_name else ""


def _is_valid_email(email: str) -> bool:
    """Validate email address format.
    
    Args:
        email: Email address to validate.
        
    Returns:
        True if email appears valid, False otherwise.
    """
    if not email or "@" not in email:
        return False
    
    # Basic email validation regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def validate_contacts(contacts: List[Dict[str, Any]]) -> List[str]:
    """Validate a list of contacts and return any validation errors.
    
    Args:
        contacts: List of contact dictionaries to validate.
        
    Returns:
        List of validation error messages. Empty list if all contacts are valid.
    """
    errors = []
    
    for i, contact in enumerate(contacts):
        # Check required fields
        if not contact.get("email"):
            errors.append(f"Contact {i+1}: Missing email address")
        elif not _is_valid_email(contact["email"]):
            errors.append(f"Contact {i+1}: Invalid email format: {contact['email']}")
        
        if not contact.get("first_name") and not contact.get("contact_name"):
            errors.append(f"Contact {i+1}: Missing both first name and contact name")
    
    return errors


def load_default_contacts() -> List[Dict[str, Any]]:
    """Load contacts from the default CSV file.
    
    Returns:
        List of contact dictionaries from the default file.
        
    Raises:
        ContactParseError: If the default file cannot be loaded.
    """
    default_path = os.path.join(
        os.path.dirname(__file__), 
        "..", "..", 
        "data", "contacts", 
        "tier_i_tier_ii_emails_verified.csv"
    )
    
    return parse_contacts_from_csv(default_path)