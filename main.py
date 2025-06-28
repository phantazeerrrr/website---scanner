import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, Menu

def analyze_website(url, output_box, status_label):
    output_box.delete("1.0", "end")
    status_label.config(text="🔄 Анализируем...", bootstyle=WARNING)

    start = time.time()
    try:
        response = requests.get(url, timeout=10)
    except requests.RequestException as e:
        output_box.insert("end", f"❌ Ошибка подключения: {e}\n")
        status_label.config(text="❌ Ошибка!", bootstyle=DANGER)
        return

    end = time.time()
    load_time = end - start
    page_size = len(response.content) / 1024
    soup = BeautifulSoup(response.text, "html.parser")

    # Базовая инфа
    output_box.insert("end", f"🌐 URL: {url}\n")
    output_box.insert("end", f"✅ Статус: {response.status_code}\n")
    output_box.insert("end", f"⏱ Время загрузки: {load_time:.2f} сек\n")
    output_box.insert("end", f"📦 Размер страницы: {page_size:.2f} KB\n")

    # HTTP Заголовки
    output_box.insert("end", "\n📌 Заголовки:\n")
    for k, v in response.headers.items():
        output_box.insert("end", f"  - {k}: {v}\n")

    output_box.insert("end", f"\n🍪 Cookies:\n")
    for cookie in response.cookies:
        output_box.insert("end", f"  - {cookie.name} = {cookie.value}\n")

    output_box.insert("end", "\n📁 Ресурсы страницы:\n")
    resources = []
    for tag in soup.find_all(["script", "img", "link"]):
        src = tag.get("src") or tag.get("href")
        if src:
            resources.append(urljoin(url, src))
    output_box.insert("end", f"  🔗 Найдено: {len(resources)}\n")
    for r in resources[:5]:
        output_box.insert("end", f"  - {r}\n")

    output_box.insert("end", "\n🔐 Безопасность:\n")
    if not url.startswith("https"):
        output_box.insert("end", "  ⚠️ Используется HTTP\n")
    headers_needed = [
        "Content-Security-Policy", "X-Frame-Options", "Strict-Transport-Security",
        "X-XSS-Protection", "X-Content-Type-Options", "Referrer-Policy"
    ]
    for h in headers_needed:
        if h not in response.headers:
            output_box.insert("end", f"  ⚠️ Нет {h}\n")
        else:
            output_box.insert("end", f"  ✅ {h}: {response.headers[h]}\n")

    output_box.insert("end", "\n🧪 Проверка уязвимостей:\n")
    test_paths = [
        ".git/config", ".env", "admin/", "login", "phpinfo.php", "robots.txt",
        "sitemap.xml", "config.php", "backup.zip", "db.sql", "dump.sql",
        "wp-admin/", "cpanel", "server-status", "test/", "tmp/", "old/", "dev/"
    ]
    for path in test_paths:
        full = urljoin(url + "/", path)
        try:
            r = requests.get(full, timeout=5)
            if r.status_code in [200, 403] and "Index of" in r.text or r.status_code == 200:
                output_box.insert("end", f"  ⚠️ Доступный путь: {full} ({r.status_code})\n")
        except:
            pass

    # Примитивная XSS и SQL-инъекция
    test_params = {
        "xss": "<script>alert(1)</script>",
        "sql": "' OR '1'='1"
    }
    for name, payload in test_params.items():
        try:
            test_url = f"{url}?test={payload}"
            r = requests.get(test_url, timeout=5)
            if payload in r.text:
                output_box.insert("end", f"  ⚠️ Уязвимость на {name.upper()} найдена через параметр: {test_url}\n")
        except:
            pass

    output_box.insert("end", "\n🔍 JS-файлы на ключи:\n")
    for src in soup.find_all("script"):
        link = src.get("src")
        if link:
            full = urljoin(url, link)
            try:
                js = requests.get(full, timeout=5).text
                if any(k in js.lower() for k in ["apikey", "token", "secret", "auth"]):
                    output_box.insert("end", f"  ⚠️ Возможные ключи в: {full}\n")
            except:
                pass

    forms = soup.find_all("form")
    output_box.insert("end", f"\n📝 Формы на странице: {len(forms)}\n")
    for i, form in enumerate(forms):
        inputs = form.find_all("input")
        has_hidden = any("hidden" in inp.get("type", "") for inp in inputs)
        has_token = any("csrf" in inp.get("name", "").lower() for inp in inputs)
        if not has_hidden and not has_token:
            output_box.insert("end", f"  ⚠️ Форма #{i+1} может быть без CSRF защиты\n")

    iframes = soup.find_all("iframe")
    if iframes:
        output_box.insert("end", f"\n🪟 Обнаружено iframe: {len(iframes)} — потенциальный фишинг или внедрение\n")

    output_box.insert("end", "\n🧩 CMS:\n")
    if "wp-content" in response.text:
        output_box.insert("end", "  🔍 WordPress\n")
    elif "Joomla" in response.text:
        output_box.insert("end", "  🔍 Joomla\n")
    elif "Drupal" in response.text:
        output_box.insert("end", "  🔍 Drupal\n")
    status_label.config(text="✅ Завершено", bootstyle=SUCCESS)

def run_check():
    url = url_entry.get()
    if url:
        if not url.startswith("http"):
            url = "https://" + url
        analyze_website(url, output_text, status_label)
    else:
        messagebox.showwarning("Внимание", "Пожалуйста, введите URL сайта.")

def enable_copy_paste(widget):
    menu = Menu(widget, tearoff=0)
    menu.add_command(label="Копировать", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Вставить", command=lambda: widget.event_generate("<<Paste>>"))

    def show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)

    widget.bind("<Button-3>", show_menu) 

app = ttk.Window(themename="superhero")
app.title("🛡️ Сканер сайта")
app.geometry("900x650")
app.resizable(False, False)
app.iconbitmap("shield.ico")  
ttk.Label(app, text="🔗 Введите URL сайта:", font=("Segoe UI", 12)).pack(pady=10)
url_entry = ttk.Entry(app, width=80, font=("Segoe UI", 11))
url_entry.pack(pady=5)
url_entry.insert(0, "https://example.com")
enable_copy_paste(url_entry)
check_btn = ttk.Button(app, text="Начать анализ", bootstyle=SUCCESS, command=run_check)
check_btn.pack(pady=10)
status_label = ttk.Label(app, text="Ожидание", font=("Segoe UI", 4), bootstyle=INFO)
status_label.pack()
output_frame = ttk.Frame(app)
output_frame.pack(padx=10, pady=10, fill=BOTH, expand=True)
output_text = ttk.Text(output_frame, font=("Consolas", 10), wrap="word")
output_text.pack(side="left", fill=BOTH, expand=True)
enable_copy_paste(output_text)
scrollbar = ttk.Scrollbar(output_frame, command=output_text.yview)
scrollbar.pack(side="right", fill=Y)
output_text.config(yscrollcommand=scrollbar.set)
app.mainloop()
