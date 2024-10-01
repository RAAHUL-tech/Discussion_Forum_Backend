import json
import boto3
from botocore.exceptions import ClientError

# Initialize the SES client
ses_client = boto3.client('ses', region_name='us-west-1')


def send_email_to_recipients(email_list, subject, body):
    sender_email = "verified-sender@example.com"

    for recipient_email in email_list:
        try:
            response = ses_client.send_email(
                Source=sender_email,
                Destination={
                    'ToAddresses': [recipient_email]
                },
                Message={
                    'Subject': {
                        'Data': subject
                    },
                    'Body': {
                        'Text': {
                            'Data': body
                        }
                    }
                }
            )
            print(f"Email sent to {recipient_email}, Response: {response}")
        except ClientError as e:
            print(f"Error sending email to {recipient_email}: {e.response['Error']['Message']}")


def lambda_handler(event, context):
    # Loop through the SQS records in the event
    for record in event['Records']:
        # Get the message body (which is JSON)
        message_body = json.loads(record['body'])

        email_list = message_body['email_list']
        subject = message_body['subject']
        body = message_body['body']

        print(f"Processing email to {email_list} with subject: {subject}")

        # Send email to all recipients
        send_email_to_recipients(email_list, subject, body)

    return {
        'statusCode': 200,
        'body': json.dumps('Emails processed successfully')
    }
