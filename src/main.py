from utils.csv_reader import parse_contacts_from_csv
import os
from mailersend import MailerSendClient, EmailBuilder
from dotenv import load_dotenv
from utils.json_reader import load_email_config

load_dotenv()
config = load_email_config()

def send_in_bulk():
    ms = MailerSendClient(os.getenv('TIERII_MAILERSEND_API_TOKEN'))
    contacts = parse_contacts_from_csv('data/test/testdata.csv')
    for contact in contacts:
        # Replace {name} placeholder with the contact's first name using string replacement
        html_content = config['html_content'].replace('{name}', contact['first_name']) if config['html_content'] else ""
        
        email = EmailBuilder() \
            .from_email(os.getenv('TIERII_SENDER_EMAIL')) \
            .to_many([{"email": contact['email'], "name": contact['contact_name']}]) \
            .subject(config['subject']) \
            .html(html_content) \
            .text(config['body'].format(name=contact['first_name'])) \
            .build()
        response = ms.emails.send(email)
        print(response)

if __name__ == "__main__":
    send_in_bulk()