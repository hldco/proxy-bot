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

# منابع
SOURCE_URL = "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/refs/heads/main/configtg.txt"
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

def get_sent_configs():
    if not os.path.exists(SENT_FILE):
        return set()
    with open(SENT_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def save_sent_config(configs_list):
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        for config in configs_list:
            f.write(config + "\n")

def get_sent_ips():
    if not os.path.exists(SENT_IPS_FILE):
        return set()
    with open(SENT_IPS_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_sent_ip(ip_list):
    # اینجا تغییر کرد که کل فایل رو بازنویسی کنه تا وقتی پاک میشه دیگه خط تکراری نمونه
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
        sock.settimeout(1.5) 
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
    if post_type == "v2ray":
        save_sent_config(original_configs_posted)
        
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
        # رفع باگ &amp; با جایگزینی دستی کاراکترها
        safe_configs_str = all_configs_str.replace("<", "&lt;").replace(">", "&gt;")
        configs_text = f"<pre>{safe_configs_str}</pre>"
        full_message = header + configs_text + footer
        payload = {"chat_id": CHANNEL_USERNAME, "text": full_message, "parse_mode": "HTML"}
        try:
            tg_response = requests.post(url, json=payload)
            print("Telegram Response:", tg_response.text)
            print(f"{len(configs_to_post)} کانفیگ {post_type} با موفقیت پست شد.")
        except Exception as e:
            print("Error:", e)
    else:
        links_html = [f'<a href="{html.escape(cfg)}">🚀 Proxy {i}</a>' for i, cfg in enumerate(configs_to_post, 1)]
        rows = ["  |  ".join(links_html[i:i+3]) for i in range(0, len(links_html), 3)]
        configs_text = "\n\n".join(rows)
        full_message = header + configs_text + footer
        payload = {"chat_id": CHANNEL_USERNAME, "text": full_message, "parse_mode": "HTML"}
        try:
            tg_response = requests.post(url, json=payload)
            print("Telegram Response:", tg_response.text)
            print(f"{len(configs_to_post)} کانفیگ {post_type} با موفقیت پست شد.")
        except Exception as e:
            print("Error:", e)

def main():
    delay_seconds = random.randint(0, 60)
    print(f"ربات برای طبیعی بودن، {delay_seconds} ثانیه صبر می‌کند...")
    time.sleep(delay_seconds)

    sent_configs = get_sent_configs()
    sent_ips = get_sent_ips() 
    target_type = get_state()
    print(f"نوبت ارسال برای: {target_type}")
    
    valid_configs = []
    originals_to_save = []
    all_ips = []
    
    try:
        if target_type == "v2ray":
            print("در حال دریافت کانفیگ‌ها از گیت‌هاب...")
            response = requests.get(SOURCE_URL)
            content = response.text
            try:
                configs = base64.b64decode(content).decode('utf-8').strip().split('\n')
            except:
                configs = content.strip().split('\n')
                
            target_limit = MAX_V2RAY_POST
            new_ips_found = False
            
            for config in configs:
                config = config.strip()
                if not config.startswith(("vless://", "vmess://", "trojan://", "ss://")): continue
                
                ip, port = extract_ip_port(config)
                if ip:
                    ip_port_str = f"{ip}:{port}"
                    
                    if ip_port_str in sent_ips:
                        print(f"⏭️ آی‌پی تکراری در تاریخچه: {ip_port_str}")
                        continue
                    
                    new_ips_found = True
                    all_ips.append(ip)
                    if check_port(ip, port):
                        modified = change_remark_v2ray(config, f"{get_flags_batch([ip]).get(ip, '🌐')} {CUSTOM_REMARK}")
                        valid_configs.append({"original": config, "modified": modified})
                        print(f"✅ زنده است: {ip}:{port} (تا الان {len(valid_configs)} پیدا کردیم)")
                        
                        sent_ips.add(ip_port_str)
                        
                        if len(valid_configs) >= target_limit:
                            print(f"به حد نصاب ({target_limit}) رسیدیم! تست متوقف می‌شود.")
                            break
                    else:
                        print(f"❌ مرده است: {ip}:{port}")

            # اگر هیچ آی‌پی جدیدی پیدا نشده بود، یعنی منبع گیت‌هاب آپدیت نشده
            # پس حافظه را پاک میکنیم تا از همان کانفیگ‌های قبلی استفاده کنیم و کانال خالی نماند
            if not new_ips_found and len(valid_configs) == 0:
                print("💡 منبع آپدیت نشده. حافظه آی‌پی‌ها پاک می‌شود تا از کانفیگ‌های فعلی استفاده شود.")
                sent_ips.clear()
                if os.path.exists(SENT_IPS_FILE):
                    os.remove(SENT_IPS_FILE)
                
                # یک دور دیگر فایل را می‌خوانیم تا 5 تا کانفیگ زنده پیدا کنیم
                for config in configs:
                    config = config.strip()
                    if not config.startswith(("vless://", "vmess://", "trojan://", "ss://")): continue
                    ip, port = extract_ip_port(config)
                    if ip:
                        all_ips.append(ip)
                        if check_port(ip, port):
                            modified = change_remark_v2ray(config, f"{get_flags_batch([ip]).get(ip, '🌐')} {CUSTOM_REMARK}")
                            valid_configs.append({"original": config, "modified": modified})
                            print(f"♻️ کانفیگ قبلی زنده است: {ip}:{port} (تا الان {len(valid_configs)} پیدا کردیم)")
                            sent_ips.add(f"{ip}:{port}")
                            if len(valid_configs) >= target_limit:
                                break

            if valid_configs:
                configs_to_post = [x["modified"] for x in valid_configs]
                originals = [x["original"] for x in valid_configs]
                send_post(configs_to_post, originals, target_type)
                save_sent_ip(list(sent_ips)) # ذخیره مجدد آی‌پی‌ها
            else:
                print("هیچ کانفیگ زنده‌ای پیدا نشد.")
                
        else: # MTProto
            print("در حال دریافت پروکسی‌ها از کانال‌های تلگرام...")
            found_proxies = set()
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
                    valid_configs.append({"original": proxy, "modified": change_remark_mtproto(proxy, f"{flag} {CUSTOM_REMARK}")})
                
                configs_to_post = [x["modified"] for x in valid_configs]
                originals = [x["original"] for x in valid_configs]
                send_post(configs_to_post, originals, "mtproto")
            else:
                print("هیچ پروکسی MTProto پیدا نشد.")
                
        update_state(target_type)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
