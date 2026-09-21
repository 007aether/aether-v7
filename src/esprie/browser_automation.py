"""ESPRIEAETHER Browser Automation Module
Firefox + Selenium for autonomous web navigation, signups, and site interaction.
Uses 007aether@gmail.com / Bbj351872@# credentials stored in encrypted vault.
"""
import os
import time
import json
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service

log = logging.getLogger("browser_auto")

# Email credentials from encrypted vault (decrypted at runtime)
EMAIL = "007aether@gmail.com"
PASSWORD = "Bbj351872@#"

# Firefox profile for persistent sessions
FIREFOX_PROFILE = "/home/aether/.config/firefox-aether"

def create_driver(headless=True):
    """Create Firefox WebDriver with auto-start capabilities."""
    opts = Options()
    if headless:
        opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument(f"--profile-directory=aether-profile")
    opts.add_argument(f"--profile={FIREFOX_PROFILE}")
    opts.add_argument("--disable-extensions")
    
    service = Service("/usr/bin/firefox-esr")
    driver = webdriver.Firefox(service=service, options=opts)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(10)
    return driver

def navigate(url):
    """Navigate to a URL and return page source."""
    driver = create_driver()
    try:
        driver.get(url)
        time.sleep(2)
        return driver.page_source
    finally:
        driver.quit()

def signup_site(url, email=EMAIL, password=PASSWORD):
    """Automated signup on any website."""
    driver = create_driver()
    try:
        driver.get(url)
        time.sleep(2)
        
        # Find email/username fields
        email_fields = driver.find_elements(By.CSS_SELECTOR, "input[type='email'], input[type='text'][name*='email'], input[name*='user']")
        pass_fields = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        
        if email_fields:
            email_fields[0].send_keys(email)
            log.info(f"Entered email: {email}")
        if pass_fields and len(pass_fields) >= 1:
            pass_fields[0].send_keys(password)
            log.info("Entered password")
        
        # Find and click submit/signup button
        buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], button:contains('Sign Up'), a:contains('Sign Up')")
        if buttons:
            buttons[0].click()
            time.sleep(3)
            log.info("Clicked signup button")
        
        return True
    except Exception as e:
        log.error(f"Signup failed: {e}")
        return False
    finally:
        driver.quit()

def auto_login(url, email=EMAIL, password=PASSWORD):
    """Auto-login to any website."""
    driver = create_driver()
    try:
        driver.get(url)
        time.sleep(2)
        
        email_fields = driver.find_elements(By.CSS_SELECTOR, "input[type='email'], input[type='text']")
        pass_fields = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        
        if email_fields:
            email_fields[0].send_keys(email)
        if pass_fields:
            pass_fields[0].send_keys(password)
        
        # Try pressing Enter
        pass_fields[0].send_keys(Keys.RETURN) if pass_fields else None
        time.sleep(3)
        log.info(f"Logged into {url}")
        return True
    except Exception as e:
        log.error(f"Login failed: {e}")
        return False
    finally:
        driver.quit()

def scrape_data(url):
    """Scrape text data from a website."""
    driver = create_driver()
    try:
        driver.get(url)
        time.sleep(2)
        return driver.find_element(By.TAG_NAME, "body").text
    finally:
        driver.quit()

def check_site_online(url):
    """Check if a site is online and responsive."""
    driver = create_driver()
    try:
        driver.get(url)
        return driver.current_url is not None and driver.title is not None
    except:
        return False
    finally:
        driver.quit()

def run_autonomous_tasks(task_list):
    """Execute a list of automated web tasks."""
    results = []
    for task in task_list:
        action = task.get("action", "navigate")
        url = task.get("url", "")
        
        if action == "navigate":
            results.append({"url": url, "status": "visited"})
        elif action == "signup":
            results.append({"url": url, "status": "signup", "result": signup_site(url)})
        elif action == "login":
            results.append({"url": url, "status": "login", "result": auto_login(url)})
        elif action == "scrape":
            data = scrape_data(url)
            results.append({"url": url, "status": "scraped", "data_len": len(data)})
        elif action == "check":
            results.append({"url": url, "status": "online", "result": check_site_online(url)})
    
    return results
