from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import time
import threading
import os
import atexit

load_dotenv()
id = os.getenv("regn")
pwd = os.getenv("pwd")
url1 = os.getenv("login_url")
url2 = os.getenv("attendacnce_url")

app = Flask(__name__)

chrome_options = Options()
chrome_options.page_load_strategy = "none"
chrome_options.binary_location = "/usr/bin/chromium-browser"
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')

driver_lock = threading.Lock()
driver = webdriver.Chrome( options=chrome_options)

def close_driver():
    driver.quit()

atexit.register(close_driver)

driver.get(url1)

WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "txtuser_id"))).send_keys(id)
WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "txtpassword"))).send_keys(pwd)
WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnsubmit"))).click()

WebDriverWait(driver, 10).until(lambda d: d.current_url != url1)
driver.execute_script(f"window.location.href = '{url2}';")
WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")

def att(regn):
    with driver_lock: 
        try:
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_ddlroll"))
            )
            select_element = driver.find_element(By.ID, "ContentPlaceHolder1_ddlroll")
            driver.execute_script("arguments[0].removeAttribute('disabled');", select_element)

            option_text = driver.execute_script(
                f"""
                const select = document.querySelector('#ContentPlaceHolder1_ddlroll');
                const option = Array.from(select.options).find(opt => opt.value === '{regn}');
                return option ? option.text : null;
                """
            )

            if not option_text:
                return {"success": False, "message": f"Attendance for {regn} not available on portal."}

            text_parts = option_text.split(' - ')
            student_name = text_parts[1] if len(text_parts) > 1 else "Unknown"

            driver.execute_script(
                f"""
                const select = document.querySelector('#ContentPlaceHolder1_ddlroll');
                const optionToSelect = Array.from(select.options).find(option => option.value === '{regn}');
                if (optionToSelect) {{
                    optionToSelect.selected = true;
                    select.dispatchEvent(new Event('change'));
                }}
                """
            )

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_gv"))
            )
            time.sleep(5) 

            
            attendance_table = driver.find_element(By.ID, 'ContentPlaceHolder1_gv')
            attendance = []
            rows = attendance_table.find_elements(By.TAG_NAME, 'tr')
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                if not cells:
                    cells = row.find_elements(By.TAG_NAME, 'th')
                row_data = [cell.text for cell in cells]
                attendance.append(row_data)

            return {
                "success": True,
                "name": student_name,
                "attendance": attendance,
                "message": f"Attendance for {regn} fetched successfully."
            }

        except StaleElementReferenceException:
            return {"success": False, "message": "Stale element encountered. Please retry."}
        except Exception as e:
            return {"success": False, "message": str(e)}


@app.route('/att', methods=['POST'])
def fetch_attendance():
    try:
        data = request.get_json()
        regn = data.get('regn')
        if not regn:
            return jsonify({"success": False, "message": "Registration number is required."}), 400
        response = att(regn)
        return jsonify(response)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 443)))
