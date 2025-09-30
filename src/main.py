from .utils.csv_reader import parse_contacts_from_csv
import os
import csv
import json
import time
import logging
from datetime import datetime
from mailersend import MailerSendClient, EmailBuilder
from dotenv import load_dotenv
from .utils.json_reader import load_email_config
from .utils.report_generator import generate_email_summary_report
from tqdm import tqdm
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

load_dotenv()
# Load config at module level for CONTACT_FILE initialization
config = load_email_config()
rate_config = json.load(open('rate_config.json'))

BATCH_SIZE = rate_config['batch_size']
COOLDOWN = rate_config['cooldown']
INDIVIDUAL_COOLDOWN = rate_config['individual_cooldown']

CONTACT_FILE = config['contacts']

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels."""
    
    # Define colors for different log levels
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.MAGENTA + Style.BRIGHT
    }
    
    def format(self, record):
        # Get the original formatted message
        log_message = super().format(record)
        
        # Add color based on log level
        color = self.COLORS.get(record.levelname, '')
        if color:
            # Color the entire message
            log_message = f"{color}{log_message}{Style.RESET_ALL}"
        
        return log_message

def setup_logging():
    """Set up structured logging with both console and file handlers."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create timestamp for log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'logs/email_campaign_{timestamp}.log'
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create file handler (no colors for file output)
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Create console handler with colors
    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"📧 Email campaign logging initialized - Log file: {log_filename}")
    return logger

logger = setup_logging()

def log_failed_emails(failed_contacts):
    """Log failed email attempts to a CSV file."""
    if not failed_contacts:
        return
    
    bounced_file_path = 'logs/failures.csv'
    with open(bounced_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        # Use all original CSV fieldnames plus tracking fields
        fieldnames = [
            'License Number', 'License Type', 'License Type Code', 'License Status', 
            'License Status Code', 'Issued Date', 'Effective Date', 'Expiration Date',
            'Application Number', 'Entity Name', 'Address Line 1', 'Address Line 2',
            'City', 'State', 'Zip Code', 'County', 'Region', 'Business Website',
            'Operational Status', 'Business Purpose', 'Tier Type', 'Processor Type',
            'Primary Contact Name', 'Email', 'first_name', 'email_status', 'status_code', 
            'error_message', 'timestamp'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(failed_contacts)
    logger.info(f"❌ Failed emails logged to: {bounced_file_path}")
    
def log_successful_emails(contacts, failed_contacts):
    """Log successful email attempts using set difference."""
    failed_emails = {contact['Email'] for contact in failed_contacts}
    successful_contacts = [contact for contact in contacts if contact['Email'] not in failed_emails]
    
    if not successful_contacts:
        return
    
    success_file_path = 'logs/successful.csv'
    with open(success_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        # Use all original CSV fieldnames plus tracking fields
        fieldnames = [
            'License Number', 'License Type', 'License Type Code', 'License Status', 
            'License Status Code', 'Issued Date', 'Effective Date', 'Expiration Date',
            'Application Number', 'Entity Name', 'Address Line 1', 'Address Line 2',
            'City', 'State', 'Zip Code', 'County', 'Region', 'Business Website',
            'Operational Status', 'Business Purpose', 'Tier Type', 'Processor Type',
            'Primary Contact Name', 'Email', 'first_name', 'email_status', 'timestamp'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for contact in successful_contacts:
            # Create a copy of the contact and add tracking fields
            log_entry = contact.copy()
            log_entry['email_status'] = 'success'
            log_entry['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow(log_entry)
    logger.info(f"✅ Successful emails logged to: {success_file_path}")
    
def send_in_bulk():
    # Load config inside the function to allow for mocking
    config = load_email_config()
    
    ms = MailerSendClient(os.getenv('TIERII_MAILERSEND_API_TOKEN'))
    contacts = parse_contacts_from_csv(CONTACT_FILE)
    successes = 0
    iterations = 0
    failures = []
    
    logger.info(f"🚀 Starting email campaign for {len(contacts)} contacts")
    
    # Use tqdm for progress tracking
    for contact in tqdm(contacts, desc="📧 Sending emails", unit="email"):
        try:
            #if iterations >= BATCH_SIZE:
            #    logger.info(f"⏸️ Avoiding rate limiting with a {COOLDOWN} second cooldown...")
            #    time.sleep(COOLDOWN)
            #    iterations = 0
            # Replace {name} placeholder with the contact's first name using string replacement
            html_content = config['html_content'].replace('{name}', contact['first_name']) if config['html_content'] else ""
            
            email_builder = EmailBuilder() \
                .from_email(os.getenv('TIERII_SENDER_EMAIL')) \
                .to_many([{"email": contact['Email'], "name": contact['Primary Contact Name']}]) \
                .subject(config['subject']) \
                .html(html_content) \
                .text(config['body'].format(name=contact['first_name']))
            
            # Add attachments if they exist
            if config.get('processed_attachments'):
                for attachment in config['processed_attachments']:
                    path = attachment['path']
                    email_builder.attach_file(path, disposition=attachment['disposition'])
                    
            
            email = email_builder.build()
            response = ms.emails.send(email)
            if response.status_code == 202:
                logger.info(f"✅ Email sent to {contact['Email']} successfully!")
                successes += 1
            else:
                # Create a copy of the contact and add failure tracking fields
                failure_entry = contact.copy()
                failure_entry['email_status'] = 'failed'
                failure_entry['status_code'] = response.status_code
                failure_entry['error_message'] = response.text
                failure_entry['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                failures.append(failure_entry)
                logger.warning(f"⚠️ Failed to send email to {contact['Email']}: {response.status_code} - {response.text}")
            
            iterations += 1
        except Exception as e:
            # Create a copy of the contact and add failure tracking fields
            failure_entry = contact.copy()
            failure_entry['email_status'] = 'failed'
            failure_entry['status_code'] = 'exception'
            failure_entry['error_message'] = str(e)
            failure_entry['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            failures.append(failure_entry)
            logger.error(f"❌ Email to {contact['Email']} failed to send with the exception {e.__class__.__name__} - {e}. Sleeping for {INDIVIDUAL_COOLDOWN} seconds to avoid rate limiting...")
        
        # Update progress bar description with current status
        tqdm.write(f"⏳ Sleeping for {INDIVIDUAL_COOLDOWN} seconds before next email to avoid rate limiting...")
        time.sleep(INDIVIDUAL_COOLDOWN) # current rate is 10 requests per minute, bump from 6 to 7 so we don't get any errors
    
    log_failed_emails(failures)
    log_successful_emails(contacts, failures)
    
    success_rate = (successes / len(contacts)) * 100 if len(contacts) > 0 else 0
    logger.info(f"🎉 Batch emailing complete. Success rate: {success_rate:.2f}%")
    
    # Generate and display HTML summary report
    generate_email_summary_report(
        total_contacts=len(contacts),
        successful_count=successes,
        failed_count=len(failures),
        success_rate=success_rate,
        failed_contacts=failures,
        report_title="TierII Email Campaign Summary"
    )

def main():
    """Entry point for the email campaign tool."""
    send_in_bulk()

if __name__ == "__main__":
    main()