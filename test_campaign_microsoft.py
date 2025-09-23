import sys
import os

# Add project root to Python path so src modules can import correctly
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)

from src.email_campaign import EmailCampaign

# Initialize with your test CSV and Microsoft OAuth
campaign = EmailCampaign(
    csv_file="data/test/testdata.csv",
    batch_size=1,  # Small batches for testing
    delay_minutes=0.25  # Short delays for testing (15 seconds)
)

# Load contacts and show preview
contacts = campaign.load_contacts()
print(f"Loaded {len(contacts)} contacts:")
for i, contact in enumerate(contacts, 1):
    print(f"{i}. {contact['contact_name']} - {contact['email']}")

# Send the campaign using Microsoft OAuth
print("\nStarting email campaign with Microsoft OAuth...")
print(f"Using sender: luke@aiautocoach.com")
print(f"Authentication: Microsoft OAuth 2.0")

result = campaign.send_campaign()
print(f"Campaign completed. Emails sent: {result}")