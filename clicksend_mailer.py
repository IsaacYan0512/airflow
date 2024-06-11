import clicksend_client
from clicksend_client import EmailRecipient, EmailFrom, Email
from airflow.models import Variable

class ClickSendMailer:
    def __init__(self):
        self.client = clicksend_client
        self.configuration = self.client.Configuration()
        self.configuration.username = Variable.get('CLICKSEND_USERNAME')
        self.configuration.password = Variable.get('CLICKSEND_PASSWORD')
        self.api_instance = self.client.TransactionalEmailApi(self.client.ApiClient(self.configuration))

    def send_email(self, to_email, to_name, subject, body):
        to_list = [EmailRecipient(email=to_email, name=to_name)]
        bcc_list = [EmailRecipient(email="anqfsh@gmail.com", name="William")]
        email_from = EmailFrom(email_address_id=Variable.get('CLICKSEND_EMAIL_FROM_ID'), name="DoJobNow")

        # Construct email
        email = self.client.Email(
            to=to_list,
            bcc=bcc_list,
            _from=email_from,
            subject=subject,
            body=body
        )
        try:
            self.api_instance.email_send_post(email)
        except Exception as e:
            print(f"Failed to send email due to API error: {str(e)}")
            raise
