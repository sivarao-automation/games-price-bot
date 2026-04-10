import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# GitHub Secrets
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FILE_NAME = "games_old.txt"

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def format_msg(site, title, price, old):
    return (f"🎮 {site} Update:\n📌 *DISCOUNT ALERT*\n\n"
            f"Subject\n📝 {title}\n\n"
            f"Price\n💰 Now: {price} (Old: {old})\n\n"
            f"Published on\n{time.strftime('%d-%m-%Y')}")

def scrap_steam(driver):
    try:
        driver.get("https://store.steampowered.com/search/?specials=1")
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        res = []
        for item in soup.find_all("a", {"class": "search_result_row"})[:5]:
            title = item.find("span", {"class": "title"}).text
            p_div = item.find("div", {"class": "search_price"})
            if p_div and p_div.find("strike"):
                old = p_div.find("strike").text.strip()
                now = p_div.get_text(strip=True).replace(old, "").strip()
                res.append(format_msg("Steam", title, now, old))
        return res
    except: return []

def scrap_psn(driver):
    try:
        driver.get("https://store.playstation.com/en-in/category/05a79eb2-f046-4bf8-9279-05260840552b/1")
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        res = []
        for item in soup.find_all("li", {"class": "psw-l-w-1/2@mobile-s"})[:5]:
            try:
                name = item.find("span", {"class": "psw-t-body"}).get_text(strip=True)
                price = item.find("span", {"class": "psw-m-r-3"}).get_text(strip=True)
                old_tag = item.find("s")
                old = old_tag.get_text(strip=True) if old_tag else "Sale"
                res.append(format_msg("PSN India", name, price, old))
            except: continue
        return res
    except: return []

def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Error: Secrets missing!")
        return
    
    driver = get_driver()
    all_news = scrap_steam(driver) + scrap_psn(driver)
    driver.quit()

    old_news = []
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            old_news = f.read().splitlines()

    new_items = [n for n in all_news if n.replace('\n', ' ').strip() not in [o.replace('\n', ' ').strip() for o in old_news]]

    if new_items:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        for item in reversed(new_items):
            requests.post(url, data={"chat_id": CHAT_ID, "text": item, "parse_mode": "Markdown"})
            time.sleep(1)
        
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            f.write("\n".join([n.replace('\n', ' ') for n in all_news]))
    else:
        print("No new deals.")

if __name__ == "__main__":
    main()
