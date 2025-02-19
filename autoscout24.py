from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common import TimeoutException, ElementClickInterceptedException, NoSuchWindowException
from bs4 import BeautifulSoup
import time
import sqlite3

def save_db(data):
    conn = sqlite3.connect('autoscout24.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS car_details (
            vehicle_category TEXT,
            category TEXT,
            brand TEXT,
            model TEXT,
            price REAL,
            mileage INTEGER,
            gear TEXT,
            year TEXT,
            fuel TEXT,
            power TEXT
        )
    ''')
    c.execute('INSERT INTO car_details VALUES (?,?,?,?,?,?,?,?,?,?)', 
              (data['vehicle_category'], data['category'],data['brand'], data['model'], data['price'], data['mileage'], data['gear'], data['year'], data['fuel'], data['power']))
    conn.commit()
    conn.close()


def get_car_details(url, vehicle_category):
    wait = time.sleep

    chrome_options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1600, 900)

    driver.get(url)
    wait(1)

    cookie = driver.find_element(By.CSS_SELECTOR, value='._consent-accept_1lphq_114')
    cookie.click()
    wait(1)

    body_type_click = driver.find_element(By.XPATH, value='//*[@id="bodyType-input"]')
    body_type_click.click()

    body_types = driver.find_elements(By.CSS_SELECTOR, value='.MultiSelect_dropdownItem__Sd_iV')
    filtered_body_types = [body.text for body in body_types if body.text.strip() != ""]

    for body in filtered_body_types:
        wait(1)

        while True:
            try:
                try:
                    b_type = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, f'//span[@class="MultiSelect_optionLabel__7DkSs" and text()="{body}"]')
                        )
                    )
                    b_type.click()
                    wait(1)
                except TimeoutException:
                    print(f"'{body}' türü bulunamadı, atlanıyor.")
                    break

                category = body

                while True:
                    html_content = driver.page_source
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Save to database: extract data from the page
                    title_elements = soup.find_all('h2')
                    price_elements = soup.find_all('p', class_=['Price_price__APlgs', 'PriceAndSeals_current_price__ykUpx'])
                    mileage_elements = soup.find_all(attrs={'aria-label': 'Mileage'})
                    gear_elements = soup.find_all(attrs={'aria-label': 'Gear'})
                    year_elements = soup.find_all(attrs={'aria-label': 'First registration'})
                    fuel_elements = soup.find_all(attrs={'aria-label': 'Fuel type'})
                    power_elements = soup.find_all(attrs={'aria-label': 'Power'})

                    for title, price, mileage, gear, year, fuel, power in zip(
                        title_elements, price_elements, mileage_elements, gear_elements, year_elements, fuel_elements, power_elements
                    ):
                        brand = title.get_text().split()[0] if title else ''
                        version_tag = title.find('span', class_='ListItem_version__5EWfi')
                        model = version_tag.text.strip() if version_tag else ''
                        price_text = price.text.strip().replace('€', '').replace(',', '').replace('.-', '').strip()
                        mileage_text = mileage.get_text().strip().replace('km', '').replace(',', '').strip()
                        mileage_val = int(mileage_text) if mileage_text.isdigit() else 0
                        gear_text = gear.get_text().strip()
                        year_text = year.get_text().strip()
                        fuel_text = fuel.get_text().strip()
                        power_text = power.get_text().strip()

                        # Prepare data for database insertion.
                        car_data = {
                            'vehicle_category': vehicle_category,
                            'category': category,
                            'brand': brand,
                            'model': model,
                            'price': float(price_text) if price_text.replace('.', '', 1).isdigit() else 0.0,
                            'mileage': mileage_val,
                            'gear': gear_text,
                            'year': year_text,
                            'fuel': fuel_text,
                            'power': power_text
                        }

                        # Save the car data to the database.
                        save_db(car_data)


                    try:
                        wait(2)
                        next_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Go to next page"]'))
                        )
                        next_button.click()
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, '//h2'))
                        )
                        wait(3)

                    except ElementClickInterceptedException:
                        driver.get(url)
                        wait(1)
                        body_type_click = driver.find_element(By.XPATH, value='//*[@id="bodyType-input"]')
                        body_type_click.click()
                        
                        break

                break

            except NoSuchWindowException:
                print("Tarayıcı penceresi kapandı, yeniden başlatılıyor...")
                wait(1)

    driver.quit()


# It can capture 400 vehicle data for all vehicle body types.
# Quickly select one or more categories and paste them into the code at the bottom.
# They can work independently of each other.

## Car List with all body types.
# car_url = "https://www.autoscout24.com/lst?atype=C&cy=D%2CA%2CI%2CB%2CNL%2CE%2CL%2CF&desc=0&page="
# get_car_details(car_url, "Car")


## Motorcycle List with all body types.
# motorcycle_url = "https://www.autoscout24.com/lst-moto?atype=B&cy=D%2CA%2CI%2CB%2CNL%2CE%2CL%2CF&desc=0&page="
# get_car_details(motorcycle_url, "Motorcycle")


## Caravan List with all body types.
# caravan_url = "https://www.autoscout24.com/lst-caravan?atype=N&cy=D%2CA%2CI%2CB%2CNL%2CE%2CL%2CF&desc=0&page="
# get_car_details(caravan_url, "Caravan")


## Transporter List with all body types.
# transporter_url = "https://www.autoscout24.com/lst-transporter?atype=X&cy=D%2CA%2CI%2CB%2CNL%2CE%2CL%2CF&desc=0&page="
# get_car_details(transporter_url, "Transporter")