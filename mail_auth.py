import os
import yaml
import logging
import imaplib
import pandas as pd
import json
import email
from email.utils import parsedate_to_datetime
from datetime import datetime
import pytz

from dotenv import load_dotenv
load_dotenv()

def load_credentials(filepath):
    try:
        with open(filepath, 'r') as file:
            credentials = yaml.safe_load(file)
            user = credentials['user']
            password = credentials['password']
            return user, password
    except Exception as e:
        logging.error("Failed to load credentials: {}".format(e))
        raise

def connect_to_gmail_imap(user, password):
    imap_url = 'imap.gmail.com'
    try:
        mail = imaplib.IMAP4_SSL(imap_url)
        mail.login(user, password)
        mail.select('inbox')  # Connect to the inbox.
        return mail
    except Exception as e:
        logging.error("Connection failed: {}".format(e))
        raise

def get_emails_to_print(mail, filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
        emails_to_print = data['emails']

    cest = pytz.timezone('Europe/Berlin')
    summary = pd.DataFrame(columns=['Email', 'Count', 'Latest_Date'])
    for email_address in emails_to_print:
        _, messages = mail.search(None, 'FROM "{}"'.format(email_address))
        message_ids = messages[0].split()
        count = len(message_ids)
        latest_date = None
        
        for num in message_ids:
            # Fetch the email message by ID
            _, msg = mail.fetch(num, '(RFC822)')
            for response in msg:
                if isinstance(response, tuple):
                    # Parse the email content
                    email_body = email.message_from_bytes(response[1])
                    
                    # Extract the date and convert to CEST
                    date_str = email_body['Date']
                    date = parsedate_to_datetime(date_str)
                    date_cest = date.astimezone(cest)
                    
                    if latest_date is None or date_cest > latest_date:
                        latest_date = date_cest
                    
                    # Get the body of the email
                    if email_body.is_multipart():
                        for part in email_body.walk():
                            if part.get_content_type() == "text/plain":
                                print(f"Email from {email_address}:")
                                print(f"Date (CEST): {date_cest}")
                                print(part.get_payload(decode=True).decode())
                                print("--------------------")
                    else:
                        print(f"Email from {email_address}:")
                        print(f"Date (CEST): {date_cest}")
                        print(email_body.get_payload(decode=True).decode())
                        print("--------------------")
        
        summary = pd.concat([summary, pd.DataFrame({'Email': [email_address], 'Count': [count], 'Latest_Date': [latest_date]})], ignore_index=True)
    return summary

def main():
    credentials = load_credentials("./credentials.yaml")
    mail = connect_to_gmail_imap(*credentials)
    summary = get_emails_to_print(mail, "./mailing_list.json")
    print("\nSummary:")
    print(summary)
    mail.close()
    mail.logout()

if __name__ == "__main__":
    main()