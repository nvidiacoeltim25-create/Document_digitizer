from azure.communication.email import EmailClient
import os
from dotenv import load_dotenv
from utils.utils import clean_text_email
load_dotenv()



def send_email(recipient_email: str, subject: str, plain_text: str, html_content: str) -> None:
    """
    Sends an email using Azure Communication Services.

    Parameters:
        recipient_email (str): The recipient's email address.
        subject (str): The subject of the email.
        plain_text (str): The plain text version of the email body.
        html_content (str): The HTML version of the email body.
    """
    clean_text = clean_text_email(plain_text)
    try:
        connection_string = os.getenv("AZURE_EMAIL_CONNECTION_STRING")
        client = EmailClient.from_connection_string(connection_string)

        message = {
            "senderAddress": "DoNotReply@90f45265-edf9-4b9f-a172-d6b42d0da880.azurecomm.net",
            "recipients": {
                "to": [{"address": recipient_email}]
            },
            "content": {
                "subject": subject,
                "plainText": clean_text
                # "html": html_content
            },
        }

        poller = client.begin_send(message)
        result = poller.result()
        print("Message sent: ", result)

    except Exception as ex:
        print("Failed to send email:", ex)
