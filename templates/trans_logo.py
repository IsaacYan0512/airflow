import base64
from jinja2 import Environment, FileSystemLoader

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
