from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait as wait
from selenium.webdriver.support.expected_conditions import presence_of_element_located as located
from pandas import DataFrame

def add_sub_categories(parents, children, browser, parent, child, level):
    child_text = child.text
    parents.append(parent)
    children.append(child_text)
    browser.get(child.get_attribute("href"))
    wait(browser, 20).until(located((By.CSS_SELECTOR, "#zg-left-col")))
    selector = "#zg-left-col > div > div > div > div > div" + " > div" * level + " > a"
    for index in range(len(browser.find_elements(By.CSS_SELECTOR, selector))):
        add_sub_categories(
            parents,
            children,
            browser,
            child_text,
            browser.find_elements(By.CSS_SELECTOR, selector)[index],
            level + 1
        )
        wait(browser, 20).until(located((By.CSS_SELECTOR, "#zg-left-col")))
    browser.back()

def get_category_tree(browser):
    browser.get("https://www.amazon.co.uk/Best-Sellers/zgbs")
    main_selector = "#zg_left_col2 a"
    wait(browser, 20).until(located((By.CSS_SELECTOR, main_selector)))
    parents = []
    children = []
    for index in range(len(browser.find_elements(By.CSS_SELECTOR, main_selector))):
        add_sub_categories(
            parents,
            children,
            browser,
            "",
            browser.find_elements(By.CSS_SELECTOR, main_selector)[index],
            0
        )
        wait(browser, 20).until(located((By.CSS_SELECTOR, main_selector)))
    return DataFrame({"parent": parents, "child": children})

browser = webdriver.Firefox()
tree = get_category_tree(browser)
tree.to_csv("category_tree.csv", index = False)
browser.quit()
