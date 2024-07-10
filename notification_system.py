# 邮箱系统
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os

def send_email(subject, message, image_path=None):
    sender_email = "plate_rec_sender@163.com"  # 您的发件邮箱
    password = "xxxxxxxxx"  # 您的密码或授权码
    receiver_email = "xxxxxxxxx@qq.com" # 接收者的邮箱

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    # 如果提供了图像路径，将其添加为附件
    if image_path:
        with open(image_path, 'rb') as file:
            img = MIMEImage(file.read(), _subtype="jpeg")  # 使用 MIMEImage 并设置子类型为 jpeg
            img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path))
            msg.attach(img)

    try:
        # 使用SMTP_SSL连接到服务器
        server = smtplib.SMTP_SSL('smtp.163.com', 465)
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {e}")

# 短信宝短信系统
# coding=utf-8
import urllib
import urllib.request
import hashlib
 
def md5(str):
    import hashlib
    m = hashlib.md5()
    m.update(str.encode("utf8"))
    return m.hexdigest()
 
def send_sms_smsbao(content):
    statusStr = {
        '0': '短信发送成功',
        '-1': '参数不全',
        '-2': '服务器空间不支持,请确认支持curl或者fsocket,联系您的空间商解决或者更换空间',
        '30': '密码错误',
        '40': '账号不存在',
        '41': '余额不足',
        '42': '账户已过期',
        '43': 'IP地址限制',
        '50': '内容含有敏感词'
    }
    
    smsapi = "http://api.smsbao.com/"
    # 短信平台账号
    user = 'xxxxxxx'
    # 短信平台密码
    password = md5('xxxxxxxxx')
    # 要发送短信的手机号码
    phone = 'xxxxxxxxxx'
    
    data = urllib.parse.urlencode({'u': user, 'p': password, 'm': phone, 'c': content})
    send_url = smsapi + 'sms?' + data
    response = urllib.request.urlopen(send_url)
    the_page = response.read().decode('utf-8')
    print (statusStr[the_page])