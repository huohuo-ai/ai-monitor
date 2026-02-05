import smtplib
import os
import re
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_verification_email(to_email, code):
    """
    发送验证码邮件
    返回: True/False 表示发送成功或失败
    """
    # 验证收件人邮箱格式
    if not to_email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', to_email):
        print(f"收件人邮箱格式错误: {to_email}")
        return False
    
    # 从环境变量获取邮箱配置
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    
    # 处理 SMTP_PORT，确保是数字
    try:
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    except (ValueError, TypeError):
        print(f"SMTP_PORT 格式错误，使用默认端口 587")
        smtp_port = 587
    
    smtp_username = os.environ.get('SMTP_USERNAME', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    from_email = os.environ.get('FROM_EMAIL', smtp_username)
    
    # 确保 from_email 不为空
    if not from_email:
        from_email = smtp_username
    
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
        
        # 添加邮件内容，明确指定编码
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # 根据端口选择连接方式
        # 465 端口使用 SSL 直连
        # 其他端口使用 STARTTLS
        server = None
        try:
            if smtp_port == 465:
                # SSL 直连（如 QQ 邮箱、Gmail 的 SSL 端口）
                print(f"使用 SSL 连接 {smtp_server}:{smtp_port}")
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
            else:
                # STARTTLS（如 587 端口）
                print(f"使用 STARTTLS 连接 {smtp_server}:{smtp_port}")
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            
            # 如果是 STARTTLS，启用 TLS
            if smtp_port != 465:
                server.starttls()
            
            # 登录
            server.login(smtp_username, smtp_password)
            
            # 发送邮件
            server.sendmail(from_email, to_email, msg.as_string())
            print(f"邮件发送成功: {to_email}")
            return True
            
        finally:
            # 确保连接关闭
            if server:
                try:
                    server.quit()
                except Exception:
                    pass
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"邮件发送失败: 认证错误 - {e}")
        print("可能原因：用户名或密码错误，或者需要使用授权码而非密码")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"邮件发送失败: 连接错误 - {e}")
        print(f"可能原因：无法连接到 {smtp_server}:{smtp_port}")
        return False
        
    except smtplib.SMTPRecipientsRefused as e:
        print(f"邮件发送失败: 收件人地址被拒绝 - {e}")
        return False
        
    except smtplib.SMTPSenderRefused as e:
        print(f"邮件发送失败: 发件人地址被拒绝 - {e}")
        return False
        
    except TimeoutError:
        print(f"邮件发送失败: 连接超时（10秒）")
        print(f"可能原因：{smtp_server}:{smtp_port} 无法访问或网络问题")
        return False
        
    except Exception as e:
        print(f"邮件发送失败: {type(e).__name__} - {e}")
        print("详细错误信息:")
        traceback.print_exc()
        return False
