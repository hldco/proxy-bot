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
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# تنظیمات ربات
BOT_TOKEN = os.environ.get("BOT_TOKEN", "") 
CHANNEL_USERNAME = "@goololgoo"

# منابع
SOURCE_URL = "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/Protocols/vless.txt"
SOURCE_CHANNELS = ["PinkProxy", "Myporoxy", "ProxyWR" , "P500Y", "ProxyMTProto"] 

CUSTOM_REMARK = "@goololgoo 🔐 وی‌پی‌ان رایگان | Free Proxy💥"

MAX_V2RAY_POST = 5
MAX_MTPROTO_POST = 12
# ==========================================

SENT_FILE = "sent_configs.txt"
SENT_IPS_FILE = "sent_ips.txt" 
STATE_FILE = "state.txt"

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

def get_state():
    if not os.path.exists(STATE_FILE):
        return "v2ray"
    with open(STATE_FILE, "r") as f:
        state = f.read().strip()
        if state not in ["v2ray", "mtproto"]:
            return "v2ray"
        return state

def update_state(current):
    nxt = {"v2ray": "mtproto", "mtproto": "v2ray"}
    with open(STATE_FILE, "w") as f:
        f.write(nxt.get(current, "v2ray"))

def get_sent_ips():
    if not os.path.exists(SENT_IPS_FILE):
        return set()
    with open(SENT_IPS_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_sent_ip(ip_list):
    with open(SENT_IPS_FILE, "w") as f:
        for ip_port in ip_list:
            f.write(f"{ip_port}\n")

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
        sock.settimeout(1.0) 
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

# تابع تست همزمان (Threading)
def test_single_config(config, sent_ips):
    ip, port = extract_ip_port(config)
    if not ip: return None
    ip_port_str = f"{ip}:{port}"
    is_new = ip_port_str not in sent_ips
    if check_port(ip, port):
        return {"config": config, "ip_port": ip_port_str, "is_new": is_new}
    return None

def send_post(configs_to_post, post_type):
    date_str, time_str = get_tehran_time()
    
    if post_type == "v2ray":
        header = f"""⚡️ پروکسی v2ray مخصوص اینستاگرام و دانلود ✌️

⛽️ جدید پر سرعت و پایدار  💦
🆕 آخرین به روز رسانی {date_str} ساعت {time_str}  🕘
تست شده و فعال✅
تمام اپراتور ها📱
📍رایتل ، همراه اول ، ایرانسل ، مخابرات 📍
📌 برنامه مورد نیاز: V2rayNG, MahsaNG, Hiddify 
🔘با ضربه 👇 کپی میشود🔘

"""
        footer = "\nبرای دانلود آخرین نسخه برنامه ها به پست پین شده کانال مراجعه کنید\n♨️با دوستان خود به اشتراک بگذارید ♨️\n#MahsaNG #v2ray #فیلترشکن #hiddify #proxy #اینترنت_مجانی \n#پروکسی \n👇همین الان عضو بشید👇\n@goololgoo\n@goololgoo_group\n💬نظرات خود را با ما به اشتراک بگذارید 👇"
    else:
        header = f"""☄ پروکسی Mtporoto مخصوص تلگرام 🔥

🆕 آخرین به روز رسانی {date_str} ساعت {time_str} 🕘
تست شده و فعال✅
تمام اپراتور ها📱
📍رایتل ، همراه اول ، ایرانسل ، مخابرات 📍
👇برای اتصال کلیک کنید / برای اشتراک کپی کنید👇

"""
        footer = "\n♨️با دوستان خود به اشتراک بگذارید ♨️\n#Mtporoto #MahsaNG #v2ray #فیلترشکن #hiddify #proxy #هوش_مصنوعی \n#پروکسی #تلگرام #telegram\n👇همین الان عضو بشید👇\n@goololgoo\n@goololgoo_group\n💬نظرات خود را با ما به اشتراک بگذارید 👇"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    if post_type == "v2ray":
        all_configs_str = "\n\n".join(configs_to_post)
        safe_configs_str = all_configs_str.replace("<", "&lt;").replace(">", "&gt;")
        configs_text = f"<pre>{safe_configs_str}</pre>"
        full_message = header + configs_text + footer
    else:
        links_html = [f'<a href="{html.escape(cfg)}">🚀 Proxy {i}</a>' for i, cfg in enumerate(configs_to_post, 1)]
        rows = ["  |  ".join(links_html[i:i+3]) for i in range(0, len(links_html), 3)]
        configs_text = "\n\n".join(rows)
        full_message = header + configs_text + footer
        
    payload = {"chat_id": CHANNEL_USERNAME, "text": full_message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
        print(f"{len(configs_to_post)} کانفیگ {post_type} با موفقیت پست شد.")
    except Exception as e:
        print("Error:", e)

def main():
    delay_seconds = random.randint(0, 60)
    print(f"ربات برای طبیعی بودن، {delay_seconds} ثانیه صبر می‌کند...")
    time.sleep(delay_seconds)

    sent_ips = get_sent_ips() 
    target_type = get_state()
    print(f"نوبت ارسال برای: {target_type}")
    
    configs_to_post = []
    
    try:
        if target_type == "v2ray":
            print("در حال دریافت کانفیگ‌ها از گیت‌هاب...")
            response = requests.get(SOURCE_URL)
            content = response.text
            try:
                configs = base64.b64decode(content).decode('utf-8').strip().split('\n')
            except:
                configs = content.strip().split('\n')
                
            valid_raw_configs = [c.strip() for c in configs if c.strip().startswith(("vless://", "vmess://", "trojan://", "ss://"))]
            print(f"تعداد {len(valid_raw_configs)} کانفیگ پیدا شد. در حال تست همزمان (سرعت بالا)...")

            alive_new = []
            alive_old = []
            
            # تست همزمان 50 کانفیگ در آنِ واحد
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = {executor.submit(test_single_config, cfg, sent_ips): cfg for cfg in valid_raw_configs}
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        if result["is_new"]:
                            alive_new.append(result)
                        else:
                            alive_old.append(result)

            print(f"تست پایان یافت. {len(alive_new)} کانفیگ جدید و {len(alive_old)} کانفیگ قبلی زنده هستند.")

            selected_data = []
            
            # اول جدیدها را می‌گذاریم
            for item in alive_new:
                if len(selected_data) < MAX_V2RAY_POST:
                    selected_data.append(item)
                    sent_ips.add(item["ip_port"])

            # اگر جدیدها کم بود، حافظه را پاک می‌کنیم و قبلی‌ها را می‌گذاریم
            if len(selected_data) < MAX_V2RAY_POST:
                print("کانفیگ جدید کافی نبود، حافظه پاک شد و از کانفیگ‌های قبلی استفاده می‌شود.")
                sent_ips.clear()
                for item in selected_data:
                    sent_ips.add(item["ip_port"])
                    
                for item in alive_old:
                    if len(selected_data) < MAX_V2RAY_POST:
                        selected_data.append(item)
                        sent_ips.add(item["ip_port"])

            if selected_data:
                for item in selected_data:
                    ip, port = extract_ip_port(item["config"])
                    modified = change_remark_v2ray(item["config"], f"{get_flags_batch([ip]).get(ip, '🌐')} {CUSTOM_REMARK}")
                    configs_to_post.append(modified)
                
                send_post(configs_to_post, target_type)
                save_sent_ip(list(sent_ips))
            else:
                print("هیچ کانفیگ زنده‌ای پیدا نشد.")
                
        else: # MTProto
            print("در حال دریافت پروکسی‌ها از کانال‌های تلگرام...")
            found_proxies = set()
            all_ips = []
            for src_chan in SOURCE_CHANNELS:
                tg_url = f"https://t.me/s/{src_chan}"
                try:
                    tg_response = requests.get(tg_url, timeout=10)
                    if tg_response.status_code == 200:
                        soup = BeautifulSoup(tg_response.text, 'html.parser')
                        messages = soup.find_all('div', class_='tgme_widget_message')[-5:]
                        for msg in messages:
                            text_div = msg.find('div', class_='tgme_widget_message_text')
                            if text_div:
                                matches = re.findall(r'(https://t.me/proxy\?server=[^\s]+|tg://proxy\?server=[^\s]+)', text_div.get_text())
                                found_proxies.update(matches)
                            buttons = msg.find_all('a', href=True)
                            for btn in buttons:
                                href = btn['href']
                                if "tg://proxy" in href or "https://t.me/proxy" in href: found_proxies.add(href)
                except: pass
                
            if found_proxies:
                selected = random.sample(list(found_proxies), min(len(found_proxies), MAX_MTPROTO_POST))
                for proxy in selected:
                    ip, port = extract_ip_port(proxy)
                    if ip: all_ips.append(ip)
                    flag = get_flags_batch(all_ips).get(ip, "🌐")
                    configs_to_post.append(change_remark_mtproto(proxy, f"{flag} {CUSTOM_REMARK}"))
                
                send_post(configs_to_post, "mtproto")
            else:
                print("هیچ پروکسی MTProto پیدا نشد.")
                
        update_state(target_type)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
