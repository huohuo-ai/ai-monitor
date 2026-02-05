import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_verification_email(to_email, code):
    """
    发送验证码邮件
    返回: True/False 表示发送成功或失败
    """
    # 从环境变量获取邮箱配置
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_username = os.environ.get('SMTP_USERNAME', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    from_email = os.environ.get('FROM_EMAIL', smtp_username)
    
    # 如果没有配置邮件服务器，使用模拟模式（开发测试用）
    if not smtp_username or not smtp_password:
        print(f"[模拟邮件] 发送验证码到 {to_email}: {code}")
        return True
    
    try:
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'AI模型拨测系统 - 验证码'
        msg['From'] = from_email
        msg['To'] = to_email
        
        # 纯文本版本
        text_content = f'''
您好！

您的验证码是：{code}

该验证码5分钟内有效，请勿泄露给他人。

如果您没有请求此验证码，请忽略此邮件。

---
AI模型性能拨测系统
        '''
        
        # HTML版本
        html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #0056b3; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
        .code {{ font-size: 32px; font-weight: bold; color: #0056b3; text-align: center; 
                 padding: 20px; margin: 20px 0; background: white; border-radius: 5px;
                 letter-spacing: 5px; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
        .warning {{ color: #d9534f; font-size: 13px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>AI模型性能拨测系统</h2>
        </div>
        <div class="content">
            <p>您好！</p>
            <p>您正在进行邮箱验证，您的验证码是：</p>
            <div class="code">{code}</div>
            <p style="text-align: center; color: #666;">该验证码 <strong>5分钟</strong> 内有效</p>
            <p class="warning">⚠️ 请勿将验证码泄露给他人。如果您没有请求此验证码，请忽略此邮件。</p>
        </div>
        <div class="footer">
            <p>此邮件由系统自动发送，请勿回复</p>
        </div>
    </div>
</body>
</html>
        '''
        
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # 发送邮件
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(from_email, to_email, msg.as_string())
        
        return True
        
    except Exception as e:
        print(f"发送邮件失败: {e}")
        return False
