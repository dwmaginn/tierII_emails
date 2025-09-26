import utils.contact_parser as parser
import os

from mailersend import MailerSendClient, EmailBuilder
from dotenv import load_dotenv

load_dotenv()

def send_in_bulk():
    ms = MailerSendClient(os.getenv('TIERII_MAILERSEND_API_TOKEN'))
    contacts = parser.parse_contacts_from_csv('data/test/testdata.csv')
    emails = [
        EmailBuilder() \
            .from_email(os.getenv('TIERII_SENDER_EMAIL')) \
            .to_many([{"email": contact['email'], "name": contact['contact_name']} for contact in contacts]) \
            .subject('Test Email') \
            .html('<p>Hello, World!</p>') \
            .text('Hello, World!') \
            .build()
    ]
        
    response = ms.emails.send_bulk(emails)
    
    print(response)
    
def main():
    send_in_bulk()
    
    
if __name__ == '__main__':
    main()