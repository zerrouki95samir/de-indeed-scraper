from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import time
from bs4 import BeautifulSoup as bs
from webdriver_manager.chrome import ChromeDriverManager
import random
from tqdm import tqdm
from selenium.webdriver.chrome.service import Service
from random import shuffle
import pandas as pd 


def random_mouse_movement(driver, element):
    action = ActionChains(driver)

    # First, ensure the element is in the viewport by scrolling to it
    driver.execute_script("arguments[0].scrollIntoView();", element)
    time.sleep(0.5)  # Allow a brief moment for the scroll action to complete

    el_width = element.size["width"]
    el_height = element.size["height"]

    # Reduce the random range to just 70% of the element's dimensions to play safe
    offset_x = random.randint(int(0.15 * el_width), int(0.85 * el_width))
    offset_y = random.randint(int(0.15 * el_height), int(0.85 * el_height))

    action.move_to_element_with_offset(element, offset_x, offset_y).perform()
    time.sleep(random.uniform(0.5, 1.5))

def human_like_scroll(driver):
    actions = [
        lambda: driver.execute_script("window.scrollBy(0, arguments[0]);", random.randint(100, 400)),
        lambda: driver.execute_script("window.scrollBy(0, -arguments[0]);", random.randint(50, 200)),
        lambda: ActionChains(driver).send_keys(Keys.PAGE_DOWN).perform(),
        lambda: ActionChains(driver).send_keys(Keys.ARROW_DOWN).perform(),
        lambda: ActionChains(driver).send_keys(Keys.ARROW_UP).perform()
    ]
    random.choice(actions)()
    time.sleep(random.uniform(0.5, 2.5))

def init_driver(user_agent):
    chrome_service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={user_agent}")
    driver = webdriver.Chrome(service=chrome_service, options=options)
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.maximize_window()
    return driver

def agree_to_cookies(driver):
    agree_button_xp = '//*[@id="onetrust-accept-btn-handler"]'
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, agree_button_xp))).click()
    except Exception as e:
        print(f"Could not agree to cookies: {e}")

def set_search_term(driver, term):
    search_box_xp = '//*[@id="text-input-what"]'
    text_search = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, search_box_xp)))
    text_search.send_keys(term)
    time.sleep(2)
    text_search.send_keys(Keys.RETURN)

def get_next_page_button(driver):
    try:
        nav_buttons = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "nav div a")))
        return nav_buttons[-1] if not nav_buttons[-1].text.strip().isdigit() else None
    
    except Exception:
        return None

def main():
    SEARCH_WORDS = 'Teilzeit'
    URL = "https://de.indeed.com/"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    CLEAR_COOKIE_INTERVAL = 10

    job_data = []
    iteration_counter = 0
    driver = init_driver(USER_AGENT)
    driver.get(URL)
    time.sleep(2)
    
    set_search_term(driver, SEARCH_WORDS)
    # time.sleep(2)

    last_page = False
    page = 1
    while not last_page:
        agree_to_cookies(driver)
        try:
            popup_button = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, '//*[@id="mosaic-desktopserpjapopup"]/div[1]/button')))
            popup_button.click()
            print("Popup closed.")
        except:
            print("No popup found.")

        to_click = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h2 > a")))
        
        # Shuffle the the job offers to avoid the predictable behavior that may be identified as bot actions.
        shuffle(to_click)
        location_elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.companyLocation")))
        for index, button in tqdm(enumerate(to_click), desc=f"Page {page} - Scraping job listings", total=len(to_click), leave=True):
            try:
                
                random_mouse_movement(driver, button)
                if random.random() < 0.5:
                    human_like_scroll(driver)
                    
                iteration_counter += 1
                if iteration_counter % CLEAR_COOKIE_INTERVAL == 0:
                    driver.delete_all_cookies()
                
                job_location = location_elements[index].text
                
                time.sleep(random.uniform(.5, 1))
                
                ActionChains(driver).move_to_element(button).click().perform()
                
                time.sleep(random.uniform(.5, 1))
                
                soup = bs(driver.page_source, "lxml")
                key = "div.jobsearch-JobComponent-description"
                
                description = " ".join([tag.text for tag in soup.select(key)]) if soup.select(key) else "Not provided"
                job_data.append({"description": description, "location": job_location})
                
                data = pd.DataFrame(job_data)
                data.to_csv('job_listing.csv', index=False)
                
            except Exception as e:
                print(f"Error scraping listing {index}: {e}")
                
        next_button = get_next_page_button(driver)
        if next_button:
            ActionChains(driver).move_to_element(next_button).click().perform()
            page+=1
            time.sleep(random.uniform(1, 2))
        else:
            print("Reached the last page or encountered an error.")
            last_page = True

    driver.quit()
    print("Program ended.")

if __name__ == "__main__":
    main()
