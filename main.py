import time
import random
import string
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# === CONFIG ===
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"  # Sesuai path Railway
SIGNUP_URL = "https://openrouter.ai/signup"

# === GEN RANDOM ===
def random_email():
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    domain = requests.get("https://api.mail.tm/domains").json()["hydra:member"][0]["domain"]
    return f"{name}@{domain}"

def random_password():
    letters = ''.join(random.choices(string.ascii_lowercase, k=5))
    caps = random.choice(string.ascii_uppercase)
    nums = random.choice(string.digits)
    return f"{letters}{caps}{nums}"

# === MAIL.TM ===
def create_mail_account(email, password):
    data = {"address": email, "password": password}
    res = requests.post("https://api.mail.tm/accounts", json=data)
    res.raise_for_status()
    print(f"📧 Email dibuat: {email}")
    return email

def get_mail_token(email, password):
    res = requests.post("https://api.mail.tm/token", json={"address": email, "password": password})
    return res.json()["token"]

def get_verif_link(token):
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(20):
        time.sleep(5)
        msgs = requests.get("https://api.mail.tm/messages", headers=headers).json()["hydra:member"]
        if msgs:
            for msg in msgs:
                detail = requests.get(f"https://api.mail.tm/messages/{msg['id']}", headers=headers).json()
                body = detail.get("html", "") or detail.get("text", "")
                if "openrouter.ai/email/verify" in body:
                    start = body.find("https://openrouter.ai/email/verify")
                    return body[start:].split('"')[0]
    return None

# === SELENIUM SETUP ===
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)

# === CREATE ACCOUNT OPENROUTER ===
def register_openrouter(email, password):
    driver = get_driver()
    driver.get(SIGNUP_URL)
    time.sleep(3)
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']").click()
    driver.find_element(By.XPATH, "//button[contains(text(), 'Continue')]").click()
    print("📝 Signup dikirim...")
    time.sleep(10)
    driver.quit()

def verify_account(link):
    driver = get_driver()
    driver.get(link)
    time.sleep(5)
    driver.quit()
    print("✅ Verifikasi berhasil!")

def create_apikey(email, password):
    driver = get_driver()
    driver.get("https://openrouter.ai/login")
    time.sleep(3)
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[contains(text(), 'Continue')]").click()
    print("🔐 Login berhasil...")
    time.sleep(10)

    driver.get("https://openrouter.ai/keys")
    time.sleep(3)
    driver.find_element(By.XPATH, "//button[contains(text(), 'Create API key')]").click()
    time.sleep(1)
    keyname = ''.join(random.choices(string.ascii_letters, k=6))
    driver.find_element(By.NAME, "name").send_keys(f"key_{keyname}")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Create')]").click()
    time.sleep(3)

    el = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
    apikey = el.get_attribute("value")
    driver.quit()
    print(f"🧠 API Key: {apikey}")
    return apikey

# === MAIN LOOP ===
def main():
    for i in range(50):
        try:
            email = random_email()
            password = random_password()
            create_mail_account(email, password)
            register_openrouter(email, password)

            token = get_mail_token(email, password)
            verif_link = get_verif_link(token)

            if verif_link:
                verify_account(verif_link)
                apikey = create_apikey(email, password)
                with open("openrouter_keys.txt", "a") as f:
                    f.write(f"Key{i+1}: {apikey}\n")
                print(f"✅ Sukses [{i+1}/50]")
            else:
                print(f"⚠️ Gagal verifikasi akun {email}")
        except Exception as e:
            print(f"❌ Gagal buat akun ke-{i+1}: {str(e)}")
        time.sleep(10)

if __name__ == "__main__":
    main()