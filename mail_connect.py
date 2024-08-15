import os
import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup

from dotenv import load_dotenv
load_dotenv()

# Account credentials
username = os.getenv('GMAIL_USER')
password = os.getenv('GMAIL_PW')

# Connect to the server
mail = imaplib.IMAP4_SSL("imap.gmail.com")

# Log in to your account
mail.login(username, password)

# Select the mailbox you want to check (INBOX is default)
mail.select("inbox")

# Search for emails from DeepLearning.AI
# Note: Replace the email with the actual sender email address if available
status, messages = mail.search(None, 'FROM "DeepLearning.AI"')

# Convert the result to a list of email IDs
email_ids = messages[0].split()

# Iterate over each email ID and fetch the email content
for email_id in email_ids:
    # Fetch the email by ID
    status, msg_data = mail.fetch(email_id, "(RFC822)")

    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])

            # Decode the email subject
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                # If it's a bytes object, decode to str
                subject = subject.decode(encoding if encoding else 'utf-8')
            print("Subject:", subject)

            # From who?
            from_ = msg.get("From")
            print("From:", from_)

            # If the email message is multipart
            if msg.is_multipart():
                # Iterate over email parts
                for part in msg.walk():
                    # Extract the content type of the email part
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    try:
                        # Get the email body
                        body = part.get_payload(decode=True).decode()
                    except:
                        pass

                    if "attachment" not in content_disposition:
                        # If it's text/plain or text/html, print the content
                        if content_type == "text/plain" or content_type == "text/html":
                            # Print text/html emails using BeautifulSoup for better formatting
                            if content_type == "text/html":
                                soup = BeautifulSoup(body, "html.parser")
                                body = soup.get_text()
                            print("Body:", body)
            else:
                # Extract content type of the email
                content_type = msg.get_content_type()

                # Get the email body
                body = msg.get_payload(decode=True).decode()
                if content_type == "text/plain" or content_type == "text/html":
                    if content_type == "text/html":
                        soup = BeautifulSoup(body, "html.parser")
                        body = soup.get_text()
                    print("Body:", body)

# Close the connection and logout
mail.close()
mail.logout()