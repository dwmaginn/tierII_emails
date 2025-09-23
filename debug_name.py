def get_first_name(contact_name):
    """Extract first name from contact name"""
    if not contact_name:
        return "there"

    # Split by common delimiters and take first part
    name_parts = contact_name.split()
    if name_parts:
        first_name = name_parts[0].strip()
        # Remove common titles (with and without periods)
        titles = ['mr', 'mrs', 'ms', 'dr', 'prof', 'rev', 'sir', 'madam',
                 'mr.', 'mrs.', 'ms.', 'dr.', 'prof.', 'rev.', 'sir.', 'madam.']
        first_name_lower = first_name.lower()
        if first_name_lower in titles:
            return name_parts[1].strip() if len(name_parts) > 1 else "there"
        return first_name
    return "there"

# Test the function
test_name = "José María González"
result = get_first_name(test_name)
print(f"Input: {repr(test_name)}")
print(f"Output: {repr(result)}")
print(f"Expected in message: 'Hi {result},'")