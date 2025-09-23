import csv

def get_first_name(contact_name):
    """Extract first name from contact name"""
    if not contact_name:
        return "there"

    # Split by common delimiters and take first part
    name_parts = contact_name.split()
    if name_parts:
        first_name = name_parts[0].strip()
        # Remove common titles
        titles = ['mr', 'mrs', 'ms', 'dr', 'prof', 'rev', 'sir', 'madam']
        first_name_lower = first_name.lower()
        if first_name_lower in titles:
            return name_parts[1].strip() if len(name_parts) > 1 else "there"
        return first_name

    return "there"

def read_contacts_from_csv(csv_file):
    """Read contacts from CSV file"""
    contacts = []

    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                contact_name = row.get('Primary Contact Name', '').strip()
                email = row.get('Email', '').strip()

                if email and '@' in email:  # Basic email validation
                    first_name = get_first_name(contact_name)
                    contacts.append({
                        'email': email,
                        'first_name': first_name,
                        'contact_name': contact_name
                    })

        print(f"Found {len(contacts)} valid contacts")
        return contacts

    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return []

def main():
    # Read contacts from CSV
    csv_file = "tier_i_tier_ii_emails_verified.csv"
    contacts = read_contacts_from_csv(csv_file)

    if not contacts:
        print("No contacts found. Exiting.")
        return

    print("\n" + "="*60)
    print("CONTACTS PREVIEW")
    print("="*60)
    print(f"Total contacts: {len(contacts)}")
    print("="*60)

    # Show first few contacts as preview
    print("\nPREVIEW OF FIRST 10 CONTACTS:")
    for i, contact in enumerate(contacts[:10]):
        print(f"{i+1"2d"}. {contact['contact_name']"30"} -> First name: \"{contact['first_name']"15"}\" -> {contact['email']}")

    if len(contacts) > 10:
        print("...")

    print("\n" + "="*60)
    print("READY TO SEND EMAILS")
    print("="*60)
    print("Next steps:")
    print("1. Update config.py with your email credentials")
    print("2. Run: python email_campaign.py")
    print("3. The script will first send a test email to dwmaginn@gmail.com")
    print("4. After you confirm the test worked, it will ask for approval to send to all contacts")
    print("="*60)

if __name__ == "__main__":
    main()
