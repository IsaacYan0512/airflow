from airflow import DAG
import base64
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.dummy_operator import DummyOperator
from datetime import datetime, timedelta
import psycopg2
from clicksend_mailer import ClickSendMailer
from airflow.models import Variable
from jinja2 import Environment, FileSystemLoader

# 包含生成Base64图片并插入HTML模板的函数
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def replace_image_with_base64(html_content, image_path, image_placeholder):
    image_base64 = image_to_base64(image_path)
    image_base64_tag = f"data:image/png;base64,{image_base64}"
    return html_content.replace(image_placeholder, image_base64_tag)

def generate_email_with_base64_image(template_path, image_path, output_path, image_placeholder):
    env = Environment(loader=FileSystemLoader('/opt/airflow/dags/repo/templates'))
    template = env.get_template(template_path)

    html_content = template.render()
    modified_html_content = replace_image_with_base64(html_content, image_path, image_placeholder)

    with open(output_path, "w") as file:
        file.write(modified_html_content)

    print("HTML email template with Base64 encoded image generated successfully.")

# 定义fetch_unlogged_users函数
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

# 定义生成HTML模板的函数
def generate_email_template():
    template_path = 'welcome.html'
    image_path = '/opt/airflow/dags/repo/templates/logo2.png'
    output_path = '/opt/airflow/dags/repo/templates/reminder.html'
    image_placeholder = 'src="logo2.png"'

    generate_email_with_base64_image(template_path, image_path, output_path, image_placeholder)

# 定义发送邮件的函数
def send_email(**kwargs):
    ti = kwargs['ti']

    clicksend_username = Variable.get("CLICKSEND_USERNAME")
    clicksend_password = Variable.get("CLICKSEND_PASSWORD")
    clicksend_email_from_id = Variable.get("CLICKSEND_EMAIL_FROM_ID")

    print(f"Using ClickSend username: {clicksend_username}")
    print(f"Using ClickSend password: {clicksend_password}")
    print(f"Using ClickSend email address ID: {clicksend_email_from_id}")

    users = ti.xcom_pull(task_ids='fetch_unlogged_users', key='unlogged_users')
    if not users:
        print("No users to email.")
        return 'skip_email'

    mailer = ClickSendMailer()

    subject = "Reminder: Have you logged in recently?"
    template_loader = FileSystemLoader('/opt/airflow/dags/repo/templates')
    template_env = Environment(loader=template_loader)
    template = template_env.get_template('reminder.html')

    for user in users:
        body = template.render(username=user['username'])
        try:
            mailer.send_email(to_email=user['email'], to_name=user['username'], subject=subject, body=body)
            print(f"Email sent to {user['email']}")
        except Exception as e:
            print(f"Failed to send email to {user['email']}: {str(e)}")

    return 'send_email'

# 定义决定是否发送邮件的函数
def decide_to_email(**kwargs):
    ti = kwargs['ti']
    users = ti.xcom_pull(task_ids='fetch_unlogged_users', key='unlogged_users')
    if not users:
        return 'skip_email'
    else:
        return 'send_email'

# 定义Airflow DAG
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
    schedule_interval=timedelta(days=7),
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["example"],
) as dag:

    t1 = PythonOperator(
        task_id="fetch_unlogged_users",
        python_callable=fetch_unlogged_users
    )

    generate_template_task = PythonOperator(
        task_id='generate_email_template',
        python_callable=generate_email_template
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

    t1 >> generate_template_task >> decide_to_email_task >> [send_email_task, skip_email]
