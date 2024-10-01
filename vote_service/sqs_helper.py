import boto3


def send_email_to_sqs(email_list, subject, body):
    sqs = boto3.client('sqs')
    queue_url = 'YOUR_SQS_QUEUE_URL'

    message = {
        'email_list': email_list,
        'subject': subject,
        'body': body
    }

    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=str(message)
    )

    return response
