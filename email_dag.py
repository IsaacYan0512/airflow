from airflow import DAG
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.dummy_operator import DummyOperator
from datetime import datetime, timedelta
import psycopg2
from clicksend_mailer import ClickSendMailer
from jinja2 import Environment, FileSystemLoader
from airflow.models import Variable

def fetch_unlogged_users(**kwargs):
    print("Connecting to database...")
    conn = psycopg2.connect(
        dbname=Variable.get('POSTGRES_DB'),
        user=Variable.get('POSTGRES_USER'),
        password=Variable.get('POSTGRES_PASSWORD'),
        host=Variable.get('POSTGRES_HOST'),
        port=Variable.get('POSTGRES_PORT')
    )
    cursor = conn.cursor()
    print("Executing query...")
    cursor.execute("""
        SELECT username, email, last_login
        FROM users
        WHERE last_login < NOW() - INTERVAL '3 days';
    """)
    rows = cursor.fetchall()
    dict_rows = [{'username': row[0], 'email': row[1], 'last_login': row[2]} for row in rows]
    print(f"Query returned {len(rows)} rows.")
    if dict_rows:
        print("Actual data to push to XCom:", dict_rows)
        kwargs['ti'].xcom_push(key='unlogged_users', value=dict_rows)
    else:
        print("No data to push to XCom.")
    cursor.close()
    conn.close()

def send_email(**kwargs):
    ti = kwargs['ti']


    clicksend_username = Variable.get("CLICKSEND_USERNAME")
    clicksend_password = Variable.get("CLICKSEND_PASSWORD")
    clicksend_email_address_id = Variable.get("CLICKSEND_EMAIL_ADDRESS_ID")

    print(f"Using ClickSend username: {clicksend_username}")
    print(f"Using ClickSend password: {clicksend_password}")
    print(f"Using ClickSend email address ID: {clicksend_email_address_id}")

    users = ti.xcom_pull(task_ids='fetch_unlogged_users', key='unlogged_users')
    if not users:
        print("No users to email.")
        return 'skip_email'

    mailer = ClickSendMailer()

    subject = "Reminder: Have you logged in recently?"
    template_loader = FileSystemLoader('/opt/airflow/dags/repo/templates')
    template_env = Environment(loader=template_loader)
    template = template_env.get_template('welcome.html')

    for user in users:
        body = template.render(username=user['username'])
        try:
            # 尝试发送邮件
            mailer.send_email(to_email=user['email'], to_name=user['username'], subject=subject, body=body,from_email_address_id=clicksend_email_address_id)
            print(f"Email sent to {user['email']}")
        except Exception as e:
            print(f"Failed to send email to {user['email']}: {str(e)}")

    return 'send_email'


def decide_to_email(**kwargs):
    ti = kwargs['ti']
    users = ti.xcom_pull(task_ids='fetch_unlogged_users', key='unlogged_users')
    if not users:
        return 'skip_email'
    else:
        return 'send_email'

with DAG(
    "email_testing",
    default_args={
        "depends_on_past": False,
        "email": ["airflow@example.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
        "retry_delay": timedelta(minutes=5),
    },
    description="A simple email_test DAG",
    schedule_interval=timedelta(days=1),
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["example"],
) as dag:

    t1 = PythonOperator(
        task_id="fetch_unlogged_users",
        python_callable=fetch_unlogged_users
    )

    decide_to_email_task = BranchPythonOperator(
        task_id='decide_to_email',
        python_callable=decide_to_email,
        provide_context=True
    )

    send_email_task = PythonOperator(
        task_id='send_email',
        python_callable=send_email,
        provide_context=True
    )

    skip_email = DummyOperator(
        task_id='skip_email'
    )

    t1 >> decide_to_email_task >> [send_email_task, skip_email]