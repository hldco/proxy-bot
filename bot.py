import requests
import base64
import json
import urllib.parse
import os
import jdatetime
import pytz
import random
import time
import html
import re
import socket
from datetime import datetime

# ==========================================
# تنظیمات ربات
BOT_TOKEN = "8924162958:AAERLm6RZNwczvStWvlCiizTDqsxzQcsBPQ" 
CHANNEL_USERNAME = "@goololgoo"
SOURCE_URL = "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/refs/heads/main/configtg.txt"
CUSTOM_REMARK = "@goololgoo 🔐 وی‌پی‌ان رایگان | Free Proxy💥"
MAX_CONFIGS_PER_POST = 5
# ==========================================

SENT_FILE = "sent_configs.txt"

def to_persian_digits(text):
    mapping = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
    return text.translate(mapping)

def get_tehran_time():
    tz = pytz.timezone('Asia/Tehran')
    now = jdatetime.datetime.fromtimestamp(datetime.now(tz).timestamp(), tz)
    day = to_persian_digits(str(now.day))
    month = jdatetime.date.j_months_fa[now.month - 1]
    date_str = f"{day} {month}"
    hour = to_persian_digits(str(now.hour).zfill(2))
    minute = to_persian_digits(str(now.minute).zfill(2))
    time_str = f"{hour}:{minute}"
    return date_str, time_str

def get_sent_configs():
    if not os.path.exists(SENT_FILE):
        return set()
    with open(SENT_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def save_sent_config(configs_list):
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        for config in configs_list:
            f.write(config + "\n")

def extract_ip_port(config):
    """استخراج آی‌پی و پورت از داخل کانفیگ"""
    try:
        if config.startswith("vmess://"):
            b64_str = config.replace("vmess://", "")
            b64_str += '=' * (-len(b64_str) % 4)
            json_data = json.loads(base64.b64decode(b64_str).decode('utf-8'))
            return json_data.get("add", ""), str(json_data.get("port", ""))
        elif config.startswith(("vless://", "trojan://", "ss://")):
            match = re.search(r'@([^:]+):(\d+)', config)
            if match:
                return match.group(1), match.group(2)
    except:
        pass
    return None, None

def check_port(ip, port):
    """تست می‌کند آیا سرور کانفیگ روشن است و پذیرای اتصال هست یا خیر"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3) # 3 ثانیه زمان برای تست
        result = sock.connect_ex((ip, int(port)))
        sock.close()
        return result == 0 # 0 یعنی پورت باز است و سرور زنده است
    except:
        return False

def get_flags_batch(ip_list):
    """گرفتن پرچم همه آی‌پی‌ها در یک درخواست برای جلوگیری از مسدود شدن"""
    flags = {}
    valid_ips = [ip for ip in ip_list if ip and re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip)]
    if not valid_ips:
        return {ip: "🌐" for ip in ip_list}
    
    try:
        res = requests.post("http://ip-api.com/batch", json=[{"query": ip, "fields": "query,countryCode"} for ip in valid_ips], timeout=10).json()
        for item in res:
            ip = item.get("query")
            code = item.get("countryCode", "")
            if len(code) == 2:
                flags[ip] = chr(0x1F1E6 + ord(code[0]) - ord('A')) + chr(0x1F1E6 + ord(code[1]) - ord('A'))
            else:
                flags[ip] = "🌐"
    except:
        pass
    
    for ip in ip_list:
        if ip not in flags:
            flags[ip] = "🌐"
    return flags

def change_remark(config, new_remark):
    try:
        if config.startswith("vmess://"):
            b64_str = config.replace("vmess://", "")
            b64_str += '=' * (-len(b64_str) % 4)
            json_data = json.loads(base64.b64decode(b64_str).decode('utf-8'))
            json_data["ps"] = new_remark
            new_b64 = base64.b64encode(json.dumps(json_data).encode('utf-8')).decode('utf-8')
            return f"vmess://{new_b64}"
        elif config.startswith(("vless://", "trojan://", "ss://")):
            base_url = config.split("#")[0] if "#" in config else config
            encoded_remark = urllib.parse.quote(new_remark)
            return f"{base_url}#{encoded_remark}"
        return config
    except:
        return config

def main():
    delay_seconds = random.randint(0, 600)
    print(f"ربات برای طبیعی بودن، {delay_seconds} ثانیه صبر می‌کند...")
    time.sleep(delay_seconds)

    sent_configs = get_sent_configs()
    new_configs_data = []
    all_ips = []
    
    try:
        response = requests.get(SOURCE_URL)
        response.raise_for_status()
        content = response.text
        
        try:
            decoded_content = base64.b64decode(content).decode('utf-8')
            configs = decoded_content.strip().split('\n')
        except:
            configs = content.strip().split('\n')
            
        # مرحله ۱: استخراج آی‌پی‌ها و پورت‌ها
        for config in configs:
            config = config.strip()
            if config.startswith(("vless://", "vmess://", "trojan://", "ss://")) and config not in sent_configs:
                ip, port = extract_ip_port(config)
                if ip:
                    new_configs_data.append({"original": config, "ip": ip, "port": port})
                    all_ips.append(ip)
                    
        if new_configs_data:
            print(f"{len(new_configs_data)} کانفیگ جدید پیدا شد. در حال گرفتن پرچم کشورها...")
            flags_map = get_flags_batch(all_ips)
            
            valid_configs = []
            print("در حال تست پورت سرورها برای پیدا کردن کانفیگ‌های زنده...")
            for item in new_configs_data:
                ip = item["ip"]
                port = item["port"]
                # مرحله ۲: تست زنده بودن کانفیگ
                if check_port(ip, port):
                    flag = flags_map.get(ip, "🌐")
                    final_remark = f"{flag} {CUSTOM_REMARK}"
                    modified_config = change_remark(item["original"], final_remark)
                    valid_configs.append({"original": item["original"], "modified": modified_config})
                    print(f"✅ زنده است: {ip}:{port} - {flag}")
                else:
                    print(f"❌ مرده است: {ip}:{port}")
                    
            if valid_configs:
                # مرحله ۳: انتخاب ۵ کانفیگ سالم
                if len(valid_configs) > MAX_CONFIGS_PER_POST:
                    selected_data = random.sample(valid_configs, MAX_CONFIGS_PER_POST)
                else:
                    selected_data = valid_configs
                    
                configs_to_post = [item["modified"] for item in selected_data]
                original_configs_posted = [item["original"] for item in selected_data]
                
                save_sent_config(original_configs_posted)
                date_str, time_str = get_tehran_time()
                
                header = f"""🔵🟡🟣 پروکسی جدید پر سرعت و پایدار✌️

⛽️مخصوص اینستاگرام و دانلود  💦

🆕 آخرین به روز رسانی {date_str} ساعت {time_str}  🕘

تست شده و فعال✅

تمام اپراتور ها📱
📍رایتل ، همراه اول ، ایرانسل ، مخابرات 📍

📌 برنامه مورد نیاز:
V2rayNG 
MahsaNG 
Hiddify 

🔘با ضربه 👇 کپی میشود🔘

"""
                footer = """

برای دانلود آخرین نسخه برنامه ها به پست پین شده کانال مراجعه کنید

♨️با دوستان خود به اشتراک بگذارید ♨️

#MahsaNG #v2ray #فیلترشکن #hiddify #proxy #اینترنت_مجانی 
#پروکسی 

👇همین الان عضو بشید👇
@goololgoo
@goololgoo_group

💬نظرات خود را با ما به اشتراک بگذارید 👇"""

                all_configs_str = "\n\n".join(configs_to_post)
                safe_configs_str = html.escape(all_configs_str)
                configs_text = f"<pre>{safe_configs_str}</pre>"
                full_message = header + configs_text + footer
                
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                payload = {"chat_id": CHANNEL_USERNAME, "text": full_message, "parse_mode": "HTML"}
                requests.post(url, json=payload)
                print(f"{len(configs_to_post)} کانفیگ سالم و زنده با موفقیت پست شد.")
            else:
                print("هیچ کانفیگ زنده‌ای در اینbatch پیدا نشد.")
        else:
            print("کانفیگ جدیدی پیدا نشد.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
