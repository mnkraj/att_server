from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask_cors import CORS 
from selenium.common.exceptions import StaleElementReferenceException
from dotenv import load_dotenv
import time
import os
import atexit

# Load environment variables
load_dotenv()
id = os.getenv("regn")
pwd = os.getenv("pwd")
url1 = os.getenv("login_url")
url2 = os.getenv("attendance_url")
RAILWAY_GRID_URL = os.getenv("SELENIUM_GRID_URL")
app = Flask(__name__)
CORS(app)
# Configure Chrome options for Selenium
chrome_options = Options()
chrome_options.page_load_strategy = "none"
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")

# Global driver instance
print("Initializing WebDriver...")
driver = webdriver.Remote(
    command_executor=RAILWAY_GRID_URL,
    options=chrome_options
)


def close_driver():
    """Close the Selenium driver when the app exits."""
    print("Closing WebDriver...")
    driver.quit()

atexit.register(close_driver)

# Perform initial login only once
print("Logging in to the attendance system...")
driver.get(url1)
WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.ID, "txtuser_id"))).send_keys(id)
WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.ID, "txtpassword"))).send_keys(pwd)
WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.ID, "btnsubmit"))).click()

# Ensure login success and navigate to attendance page
WebDriverWait(driver, 10).until(lambda d: d.current_url != url1)
driver.execute_script(f"window.location.href = '{url2}';")
# WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
print("Login successful. Ready for attendance fetch requests.")


def att(regn):
    """Fetch attendance for the given registration number."""
    try:
        print("request for " + regn + " received...")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_ddlroll"))
        )
        print("1")
        select_element = driver.find_element(By.ID, "ContentPlaceHolder1_ddlroll")
        driver.execute_script("arguments[0].removeAttribute('disabled');", select_element)
        print("2")
        # Select the dropdown option dynamically
        option_text = driver.execute_script(
            f"""
            const select = document.querySelector('#ContentPlaceHolder1_ddlroll');
            const option = Array.from(select.options).find(opt => opt.value === '{regn}');
            if (option) {{
                option.selected = true;
                select.dispatchEvent(new Event('change'));
            }}
            return option ? option.text : null;
            """
        )
        print("3")

        if not option_text:
            return {"success": False, "message": f"Attendance for {regn} not available on portal."}
        print("4")
        text_parts = option_text.split(' - ')
        student_name = text_parts[1] if len(text_parts) > 1 else "Unknown"
        print("5")
        # Wait for the attendance table to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_gv"))
        )
        print("6")
        time.sleep(5)  # Small delay to ensure data is loaded
        print("7")
        # Extract attendance table
        attendance_table = driver.find_element(By.ID, 'ContentPlaceHolder1_gv')
        print("8")
        attendance = []
        rows = attendance_table.find_elements(By.TAG_NAME, 'tr')
        print("9")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if not cells:
                cells = row.find_elements(By.TAG_NAME, 'th')
            row_data = [cell.text for cell in cells]
            attendance.append(row_data)
        print("10")
        return {
            "success": True,
            "name": student_name,
            "attendance": attendance,
            "message": f"Attendance for {regn} fetched successfully."
        }

    except Exception as e:
        return {"success": False, "message": str(e)}


@app.route('/att', methods=['POST'])
def fetch_attendance():
    """API endpoint to fetch attendance."""
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
    app.run(host="10.250.15.5", port=int(os.environ.get("PORT", 4444)))
