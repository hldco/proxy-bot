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

SOURCE_URL = "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/Protocols/vless.txt"
SOURCE_CHANNELS = ["PinkProxy", "Myporoxy", "ProxyWR", "P500Y", "ProxyMTProto"]

CUSTOM_REMARK = "@goololgoo 🔐 وی‌پی‌ان رایگان | Free Proxy💥"

MAX_V2RAY_POST = 5
MAX_MTPROTO_POST = 12
# ==========================================

SENT_IPS_FILE = "sent_ips.txt"

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

def get_sent_ips():
    if not os.path.exists(SENT_IPS_FILE):
        return set()
    with open(SENT_IPS_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_sent_ips(ip_set):
    with open(SENT_IPS_FILE, "w") as f:
        for ip_port in sorted(ip_set):
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

def check_port(ip, port, timeout=2.5):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
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
        payload = [{"query": ip, "fields": "query,countryCode"} for ip in valid_ips]
        res = requests.post("http://ip-api.com/batch", json=payload, timeout=12).json()
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
            new_b64 = base64.b64encode(json.dumps(json_data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
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

def test_single_config(config, sent_ips):
    ip, port = extract_ip_port(config)
    if not ip or not port:
        return None
    ip_port_str = f"{ip}:{port}"
    is_new = ip_port_str not in sent_ips
    if check_port(ip, port):
        return {"config": config, "ip_port": ip_port_str, "is_new": is_new, "ip": ip}
    return None

def send_post(configs_to_post, post_type):
    date_str, time_str = get_tehran_time()

    if post_type == "v2ray":
        header = f"""⚡️ پروکسی v2ray مخصوص اینستاگرام و دانلود ✌️

⛽️ جدید پر سرعت و پایدار  💦
🆕 آخرین به روز رسانی {date_str} ساعت {time_str}  🕘
تست شده و فعال✅
تمام اپراتور ها📱
📍رایتل ، همراه اول ، ایرانسل ، مخابرات 📍
📌 برنامه مورد نیاز: V2rayNG, MahsaNG, Hiddify 
🔘با ضربه 👇 کپی میشود🔘

"""
        footer = "\nبرای دانلود آخرین نسخه برنامه ها به پست پین شده کانال مراجعه کنید\n♨️با دوستان خود به اشتراک بگذارید ♨️\n#MahsaNG #v2ray #فیلترشکن #hiddify #proxy #اینترنت_مجانی \n#پروکسی \n👇همین الان عضو بشید👇\n@goololgoo\n@goololgoo_group\n💬نظرات خود را با ما به اشتراک بگذارید 👇"
    else:
        header = f"""☄ پروکسی MTProto مخصوص تلگرام 🔥

🆕 آخرین به روز رسانی {date_str} ساعت {time_str} 🕘
تست شده و فعال✅
تمام اپراتور ها📱
📍رایتل ، همراه اول ، ایرانسل ، مخابرات 📍
👇برای اتصال کلیک کنید / برای اشتراک کپی کنید👇

"""
        footer = "\n♨️با دوستان خود به اشتراک بگذارید ♨️\n#MTProto #MahsaNG #v2ray #فیلترشکن #hiddify #proxy #هوش_مصنوعی \n#پروکسی #تلگرام #telegram\n👇همین الان عضو بشید👇\n@goololgoo\n@goololgoo_group\n💬نظرات خود را با ما به اشتراک بگذارید 👇"

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

    payload = {
        "chat_id": CHANNEL_USERNAME,
        "text": full_message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        r = requests.post(url, json=payload, timeout=30)
        if r.status_code == 200:
            print(f"✅ {len(configs_to_post)} کانفیگ {post_type} با موفقیت پست شد.")
        else:
            print(f"❌ خطا در ارسال {post_type}: {r.status_code} - {r.text[:200]}")
    except Exception as e:
        print(f"❌ Error sending {post_type}: {e}")

def get_v2ray_configs(sent_ips):
    print("در حال دریافت کانفیگ‌ها از گیت‌هاب...")
    try:
        response = requests.get(SOURCE_URL, timeout=20)
        content = response.text.strip()
        try:
            configs = base64.b64decode(content).decode('utf-8').strip().split('\n')
        except:
            configs = content.split('\n')
    except Exception as e:
        print(f"خطا در دریافت از گیت‌هاب: {e}")
        return []

    valid_raw = [c.strip() for c in configs if c.strip().startswith(("vless://", "vmess://", "trojan://", "ss://"))]
    print(f"تعداد {len(valid_raw)} کانفیگ پیدا شد.")

    # جدا کردن جدید و قدیمی
    new_configs = []
    old_configs = []
    for cfg in valid_raw:
        ip, port = extract_ip_port(cfg)
        if not ip:
            continue
        ip_port = f"{ip}:{port}"
        if ip_port not in sent_ips:
            new_configs.append(cfg)
        else:
            old_configs.append(cfg)

    print(f"جدید: {len(new_configs)} | قبلی: {len(old_configs)}")

    selected = []
    used_ips = set()

    def collect_alive(config_list, max_needed):
        alive = []
        with ThreadPoolExecutor(max_workers=40) as executor:
            futures = {executor.submit(test_single_config, cfg, sent_ips): cfg for cfg in config_list}
            for future in as_completed(futures):
                result = future.result()
                if result and result["ip_port"] not in used_ips:
                    alive.append(result)
                    used_ips.add(result["ip_port"])
                    if len(alive) >= max_needed:
                        # بقیه رو کنسل نمی‌کنیم چون ساده‌تره، ولی دیگه اضافه نمی‌کنیم
                        break
        return alive

    # اول فقط جدیدها
    if new_configs:
        print("در حال تست کانفیگ‌های جدید...")
        alive_new = collect_alive(new_configs, MAX_V2RAY_POST)
        selected.extend(alive_new)
        print(f"{len(alive_new)} کانفیگ جدید سالم پیدا شد.")

    # اگر کافی نبود، از قدیمی‌ها
    if len(selected) < MAX_V2RAY_POST and old_configs:
        print("کانفیگ جدید کافی نبود، در حال تست کانفیگ‌های قبلی...")
        needed = MAX_V2RAY_POST - len(selected)
        alive_old = collect_alive(old_configs, needed)
        selected.extend(alive_old)
        print(f"{len(alive_old)} کانفیگ قبلی سالم اضافه شد.")

    # اگر هنوز کم بود و حافظه پر بوده، پاک کردن و تست مجدد از همه
    if len(selected) < MAX_V2RAY_POST:
        print("حافظه تقریباً پر بود. پاک کردن حافظه و تست مجدد از کل لیست...")
        sent_ips.clear()
        used_ips.clear()
        selected = collect_alive(valid_raw, MAX_V2RAY_POST)

    return selected

def get_mtproto_proxies(sent_ips):
    print("در حال دریافت پروکسی‌های MTProto از کانال‌ها...")
    found = []

    for src_chan in SOURCE_CHANNELS:
        tg_url = f"https://t.me/s/{src_chan}"
        try:
            resp = requests.get(tg_url, timeout=12)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, 'html.parser')
            messages = soup.find_all('div', class_='tgme_widget_message')[-8:]
            for msg in messages:
                # متن پیام
                text_div = msg.find('div', class_='tgme_widget_message_text')
                if text_div:
                    matches = re.findall(r'(https://t\.me/proxy\?[^\s<>"\']+|tg://proxy\?[^\s<>"\']+)', text_div.get_text())
                    found.extend(matches)
                # دکمه‌ها
                for btn in msg.find_all('a', href=True):
                    href = btn['href']
                    if "tg://proxy" in href or "https://t.me/proxy" in href:
                        found.append(href)
        except Exception as e:
            print(f"خطا در کانال {src_chan}: {e}")
            continue

    # یکتا کردن
    unique = list(dict.fromkeys(found))  # حفظ ترتیب
    print(f"تعداد {len(unique)} پروکسی یکتا پیدا شد.")

    new_proxies = []
    old_proxies = []

    for proxy in unique:
        ip, port = extract_ip_port(proxy)
        if not ip:
            continue
        ip_port = f"{ip}:{port}"
        if ip_port not in sent_ips:
            new_proxies.append(proxy)
        else:
            old_proxies.append(proxy)

    selected = []
    # اولویت با جدید
    selected.extend(new_proxies[:MAX_MTPROTO_POST])

    # اگر کم بود از قدیمی‌ها
    if len(selected) < MAX_MTPROTO_POST:
        needed = MAX_MTPROTO_POST - len(selected)
        selected.extend(old_proxies[:needed])

    # اگر هنوز کم بود، از همه به صورت رندم
    if len(selected) < MAX_MTPROTO_POST and unique:
        remaining = [p for p in unique if p not in selected]
        random.shuffle(remaining)
        selected.extend(remaining[:MAX_MTPROTO_POST - len(selected)])

    return selected[:MAX_MTPROTO_POST]

def main():
    # تأخیر رندم اول کار (۰ تا ۱۲۰ ثانیه)
    delay = random.randint(0, 120)
    print(f"ربات برای طبیعی بودن {delay} ثانیه صبر می‌کند...")
    time.sleep(delay)

    sent_ips = get_sent_ips()
    print(f"تعداد IPهای ذخیره‌شده قبلی: {len(sent_ips)}")

    # ========== V2Ray ==========
    print("\n" + "="*40)
    print("شروع دور V2Ray")
    print("="*40)

    v2ray_results = get_v2ray_configs(sent_ips)

    if v2ray_results:
        ips_for_flag = [item["ip"] for item in v2ray_results]
        flags = get_flags_batch(ips_for_flag)

        configs_to_post = []
        for item in v2ray_results:
            flag = flags.get(item["ip"], "🌐")
            modified = change_remark_v2ray(item["config"], f"{flag} {CUSTOM_REMARK}")
            configs_to_post.append(modified)
            sent_ips.add(item["ip_port"])

        send_post(configs_to_post, "v2ray")
    else:
        print("هیچ کانفیگ V2Ray زنده‌ای پیدا نشد.")

    # تأخیر رندم بین دو پست (۳ تا ۱۲ دقیقه)
    between_delay = random.randint(180, 720)
    print(f"\n⏳ فاصله رندم بین دو پست: {between_delay // 60} دقیقه و {between_delay % 60} ثانیه...")
    time.sleep(between_delay)

    # ========== MTProto ==========
    print("\n" + "="*40)
    print("شروع دور MTProto")
    print("="*40)

    mt_proxies = get_mtproto_proxies(sent_ips)

    if mt_proxies:
        all_ips = []
        for proxy in mt_proxies:
            ip, _ = extract_ip_port(proxy)
            if ip:
                all_ips.append(ip)

        flags = get_flags_batch(all_ips)

        configs_to_post = []
        for proxy in mt_proxies:
            ip, port = extract_ip_port(proxy)
            flag = flags.get(ip, "🌐") if ip else "🌐"
            modified = change_remark_mtproto(proxy, f"{flag} {CUSTOM_REMARK}")
            configs_to_post.append(modified)
            if ip and port:
                sent_ips.add(f"{ip}:{port}")

        send_post(configs_to_post, "mtproto")
    else:
        print("هیچ پروکسی MTProto پیدا نشد.")

    # ذخیره نهایی
    save_sent_ips(sent_ips)
    print(f"\n✅ حافظه ذخیره شد. تعداد کل IPهای ثبت‌شده: {len(sent_ips)}")

if __name__ == "__main__":
    main()
