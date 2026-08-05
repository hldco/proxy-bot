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
from bs4 import BeautifulSoup

# ==========================================
# تنظیمات ربات
BOT_TOKEN = os.environ.get("BOT_TOKEN", "") 
CHANNEL_USERNAME = "@goololgoo"

# منبع اول: گیت‌هاب (برای V2ray)
SOURCE_URL = "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/refs/heads/main/configtg.txt"

# منبع دوم: کانال‌های تلگرام (برای MTProto) - ۵ کانال را بدون @ وارد کنید
SOURCE_CHANNELS = ["PinkProxy", "Myporoxy", "ProxyWR" , "P500Y", "ProxyMTProto"] 

CUSTOM_REMARK = "@goololgoo 🔐 وی‌پی‌ان رایگان | Free Proxy💥"
MAX_CONFIGS_PER_POST = 12 # افزایش به 12 پروکسی در هر پست
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

def get_next_post_type():
    tz = pytz.timezone('Asia/Tehran')
    now = datetime.now(tz)
    if now.minute < 30:
        return "v2ray"
    else:
        return "mtproto"

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
        elif "tg://proxy" in config or "https://t.me/proxy" in config:
            ip_match = re.search(r'server=([^&]+)', config)
            port_match = re.search(r'port=(\d+)', config)
            if ip_match and port_match:
                return ip_match.group(1), port_match.group(1)
    except:
        pass
    return None, None

def check_port(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, int(port)))
        sock.close()
        return result == 0
    except:
        return False

def get_flags_batch(ip_list):
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

def change_remark_v2ray(config, new_remark):
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

def change_remark_mtproto(link, new_remark):
    clean_link = re.sub(r'&name=[^&]*', '', link)
    return f"{clean_link}&name={urllib.parse.quote(new_remark)}"

def send_post(configs_to_post, original_configs_posted, post_type):
    save_sent_config(original_configs_posted)
    date_str, time_str = get_tehran_time()
    
    if post_type == "v2ray":
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
    else:
        header = f"""☄ پروکسی Mtporoto مخصوص تلگرام 🔥

🆕 آخرین به روز رسانی {date_str} ساعت {time_str} 🕘

تست شده و فعال✅

تمام اپراتور ها📱
📍رایتل ، همراه اول ، ایرانسل ، مخابرات 📍

👇برای اتصال روی دکمه‌ها کلیک کنید👇

"""
        footer = """

♨️با دوستان خود به اشتراک بگذارید ♨️

#Mtporoto #MahsaNG #v2ray #فیلترشکن #hiddify #proxy #هوش_مصنوعی 
#پروکسی #تلگرام #telegram

👇همین الان عضو بشید👇
@goololgoo
@goololgoo_group

💬نظرات خود را با ما به اشتراک بگذارید 👇"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # ==========================================
    # تفاوت در نحوه نمایش کانفیگ‌ها
    # ==========================================
    if post_type == "v2ray":
        all_configs_str = "\n\n".join(configs_to_post)
        safe_configs_str = html.escape(all_configs_str)
        configs_text = f"<pre>{safe_configs_str}</pre>"
        full_message = header + configs_text + footer
        
        payload = {"chat_id": CHANNEL_USERNAME, "text": full_message, "parse_mode": "HTML"}
        requests.post(url, json=payload)
    else:
        # برای MTProto دکمه‌های شیشه‌ای در 4 ردیف 3 تایی می‌سازیم
        full_message = header + footer
        keyboard = []
        row = []
        for cfg in configs_to_post:
            row.append({"text": "proxy", "url": cfg})
            # وقتی ردیف به ۳ دکمه رسید، آن را به کیبورد اضافه می‌کنیم و ردیف جدید شروع می‌شود
            if len(row) == 3:
                keyboard.append(row)
                row = []
        # اگر دکمه‌ای باقی ماند (مثلاً 13 تا بود) آن را در ردیف آخر می‌گذاریم
        if row:
            keyboard.append(row)
            
        reply_markup = {"inline_keyboard": keyboard}
        payload = {
            "chat_id": CHANNEL_USERNAME, 
            "text": full_message, 
            "parse_mode": "HTML",
            "reply_markup": reply_markup
        }
        requests.post(url, json=payload)
    # ==========================================
    
    print(f"{len(configs_to_post)} کانفیگ {post_type} با موفقیت پست شد.")

def main():
    delay_seconds = random.randint(0, 420)
    print(f"ربات برای طبیعی بودن، {delay_seconds} ثانیه صبر می‌کند...")
    time.sleep(delay_seconds)

    sent_configs = get_sent_configs()
    target_type = get_next_post_type()
    print(f"نوبت ارسال برای: {target_type}")
    
    target_data = []
    all_ips = []
    
    try:
        if target_type == "v2ray":
            print("در حال دریافت کانفیگ‌ها از گیت‌هاب...")
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
                    ip, port = extract_ip_port(config)
                    if ip:
                        target_data.append({"original": config, "ip": ip, "port": port})
                        all_ips.append(ip)
        else:
            print("در حال دریافت پروکسی‌ها از کانال‌های تلگرام (بررسی ۵ پست آخر)...")
            found_proxies = set()
            
            for src_chan in SOURCE_CHANNELS:
                tg_url = f"https://t.me/s/{src_chan}"
                try:
                    tg_response = requests.get(tg_url, timeout=10)
                    if tg_response.status_code == 200:
                        soup = BeautifulSoup(tg_response.text, 'html.parser')
                        
                        all_messages = soup.find_all('div', class_='tgme_widget_message')
                        recent_messages = all_messages[-5:] if len(all_messages) >= 5 else all_messages
                        
                        for msg in recent_messages:
                            text_div = msg.find('div', class_='tgme_widget_message_text')
                            if text_div:
                                text = text_div.get_text()
                                matches = re.findall(r'(https://t.me/proxy\?server=[^\s]+|tg://proxy\?server=[^\s]+)', text)
                                for match in matches:
                                    found_proxies.add(match)
                                    
                            buttons = msg.find_all('a', href=True)
                            for btn in buttons:
                                href = btn['href']
                                if "tg://proxy" in href or "https://t.me/proxy" in href:
                                    found_proxies.add(href)
                                    
                        print(f"از کانال @{src_chan} - ۵ پست آخر بررسی شد.")
                except:
                    pass
                    
            for proxy_link in found_proxies:
                if proxy_link not in sent_configs:
                    ip, port = extract_ip_port(proxy_link)
                    target_data.append({"original": proxy_link, "ip": ip, "port": port})
                    if ip:
                        all_ips.append(ip)
                                
        if target_data:
            print(f"در مجموع {len(target_data)} کانفیگ {target_type} جدید پیدا شد.")
            flags_map = get_flags_batch(all_ips)
            
            valid_configs = []
            print("در حال آماده‌سازی...")
            for item in target_data:
                flag = "🌐"
                if item["ip"]:
                    flag = flags_map.get(item["ip"], "🌐")
                
                final_remark = f"{flag} {CUSTOM_REMARK}"
                
                if target_type == "v2ray":
                    if check_port(item["ip"], item["port"]):
                        modified = change_remark_v2ray(item["original"], final_remark)
                        valid_configs.append({"original": item["original"], "modified": modified})
                        print(f"✅ زنده است: {item['ip']}:{item['port']}")
                    else:
                        print(f"❌ مرده است: {item['ip']}:{item['port']}")
                else:
                    modified = change_remark_mtproto(item["original"], final_remark)
                    valid_configs.append({"original": item["original"], "modified": modified})
                    print(f"✅ اضافه شد: {item['original']}")

            if valid_configs:
                # انتخاب تعداد مناسب بر اساس نوع پست
                limit = MAX_MTPROTO_POST if target_type == "mtproto" else MAX_V2RAY_POST
                selected = random.sample(valid_configs, min(len(valid_configs), limit))
                configs_to_post = [x["modified"] for x in selected]
                originals = [x["original"] for x in selected]
                send_post(configs_to_post, originals, target_type)
            else:
                print(f"هیچ کانفیگ {target_type} زنده‌ای پیدا نشد.")
        else:
            print(f"کانفیگ {target_type} جدیدی پیدا نشد.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
