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
    delay_seconds = random.randint(0, 1800)
    print(f"ربات برای طبیعی بودن، {delay_seconds} ثانیه صبر می‌کند...")
    time.sleep(delay_seconds)

    sent_configs = get_sent_configs()
    new_configs_list = []
    
    try:
        response = requests.get(SOURCE_URL)
        response.raise_for_status()
        content = response.text
        
        try:
            decoded_content = base64.b64decode(content).decode('utf-8')
            configs = decoded_content.strip().split('\n')
        except:
            configs = content.strip().split('\n')
            
        for config in configs:
            config = config.strip()
            if config.startswith(("vless://", "vmess://", "trojan://", "ss://")) and config not in sent_configs:
                modified_config = change_remark(config, CUSTOM_REMARK)
                new_configs_list.append(modified_config)
                
        if new_configs_list:
            if len(new_configs_list) > MAX_CONFIGS_PER_POST:
                configs_to_post = random.sample(new_configs_list, MAX_CONFIGS_PER_POST)
            else:
                configs_to_post = new_configs_list
                
            original_configs_posted = []
            for posted in configs_to_post:
                for orig in configs:
                    if change_remark(orig, CUSTOM_REMARK) == posted:
                        original_configs_posted.append(orig)
                        break
            save_sent_config(original_configs_posted)
            
            date_str, time_str = get_tehran_time()
            
            header = f"""🔵🟡🟣 موشک جدید پر سرعت و پایدار✌️

⛽️مخصوص اینستاگرام و دانلود  💦

🆕 آخرین به روز رسانی {date_str} ساعت {time_str}  🕘

تست شده و فعال✅

تمام اپراتور ها📱
📍رایتل ، همراه اول ، ایرانسل ، مخابرات 📍

📌 برنامه مورد نیاز:
V2rayNG 
MahsaNG 
Hiddify 

🔘با ضربه روی کانفیگ👇 کپی میشود🔘

"""
            footer = """
برای دانلود آخرین نسخه به پست پین شده کانال مراجعه کنید 
♨️با دوستان خود به اشتراک بگذارید ♨️
#MahsaNG #v2ray #فیلترشکن #hiddify #proxy #اینترنت_مجانی 
#پروکسی 

👇همین الان عضو کانال بشید👇
@goololgoo

💬نظرات خود را با ما به اشتراک بگذارید 👇"""

            # فرمت‌بندی کانفیگ‌ها به صورت Quote (نقل قول) و قابل کپی با یک ضربه
            formatted_configs = []
            for cfg in configs_to_post:
                safe_cfg = html.escape(cfg)
                # استفاده از blockquote برای فرمت نقل قول و code برای کپی شونده بودن
                formatted_configs.append(f"<blockquote><code>{safe_cfg}</code></blockquote>")
            
            configs_text = "\n".join(formatted_configs)
            full_message = header + configs_text + footer
            
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            # تغییر فرمت به HTML برای پشتیبانی از Quote
            payload = {"chat_id": CHANNEL_USERNAME, "text": full_message, "parse_mode": "HTML"}
            requests.post(url, json=payload)
            print(f"{len(configs_to_post)} کانفیگ با موفقیت پست شد.")
        else:
            print("کانفیگ جدیدی پیدا نشد.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
