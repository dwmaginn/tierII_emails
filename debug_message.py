from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Create message like in send_email function
msg = MIMEMultipart()
msg['From'] = "sender@example.com"
msg['To'] = "recipient@example.com"
msg['Subject'] = "Test Subject"

# Email body with personalized first name
body = """Hi there,

This is David from Honest Pharmco. We have a variety of high-quality cannabis available in sativa, indica, and hybrid strains, all with high THC percentages, including:
B&C's
Smalls
Premium flower

Our pricing starts at $600/lb for our lowest grade and increases from there based on quality.

Please feel free to reach out with any questions or to discuss availability.

Best,
David"""

msg.attach(MIMEText(body, 'plain'))

# Get the message as string (like sendmail receives)
text = msg.as_string()
print("=== FULL MESSAGE ===")
print(text)
print("\n=== CHECKING FOR 'Hi there,' ===")
print(f"'Hi there,' in text: {'Hi there,' in text}")
print("\n=== CHECKING FOR 'David from Honest Pharmco' ===")
print(f"'David from Honest Pharmco' in text: {'David from Honest Pharmco' in text}")