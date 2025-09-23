from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Simulate the email creation process
def create_test_message():
    msg = MIMEMultipart()
    msg['From'] = "test@example.com"
    msg['To'] = "recipient@example.com"
    msg['Subject'] = "Test Subject"
    
    # Create the body with special characters
    first_name = "José"
    body = f"""Hi {first_name},

I hope this email finds you well. I'm David from Honest Pharmco, and I wanted to reach out to you personally.

We've been working on some exciting developments in pharmaceutical research, and I believe you might find them interesting.

Best regards,
David
Honest Pharmco"""
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    return msg.as_string()

# Test the message
message_text = create_test_message()
print("Full message:")
print(repr(message_text))
print("\n" + "="*50 + "\n")
print("Readable message:")
print(message_text)
print("\n" + "="*50 + "\n")
print("Checking for 'Hi José,':")
print("'Hi José,' in message_text:", 'Hi José,' in message_text)
print("'Hi Jos' in message_text:", 'Hi Jos' in message_text)
print("'José' in message_text:", 'José' in message_text)