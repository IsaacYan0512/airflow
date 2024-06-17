import base64
import re

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def replace_image_with_base64(html_content, image_path, image_placeholder):
    image_base64 = image_to_base64(image_path)
    image_base64_tag = f"data:image/png;base64,{image_base64}"
    return html_content.replace(image_placeholder, image_base64_tag)

# 读取 HTML 模板文件
def read_html_template(template_path):
    with open(template_path, "r") as file:
        return file.read()

# 保存修改后的 HTML 文件
def save_html_to_file(html_content, output_path):
    with open(output_path, "w") as file:
        file.write(html_content)

# 配置文件路径
template_path = "welcome.html"
image_path = "logo2.png"
output_html_path = "reminder.html"

# 读取 HTML 模板
html_content = read_html_template(template_path)

# 替换图片路径为 Base64 编码
image_placeholder = 'src="logo2.png"'
modified_html_content = replace_image_with_base64(html_content, image_path, image_placeholder)

# 保存修改后的 HTML 文件
save_html_to_file(modified_html_content, output_html_path)

print("HTML email template with Base64 encoded image generated successfully.")
