# import pytest
# import threading
# import time
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service as ChromeService
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options
# from src.app import app  # Adjust the path to app.py in src/

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
from src.app import empty_figure
from src.app import update_heatmap
import plotly.graph_objects as go

# Path to the ChromeDriver executable
CHROME_DRIVER_PATH = './tests/chromedriver'

@pytest.fixture(scope="module")
def driver():
    options = Options()
    options.add_argument("--headless")  # Run Chrome in headless mode
    service = ChromeService(executable_path=CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    yield driver
    driver.quit()

#  Test 1 - does the heatmap load?
def test_load_heatmap(driver):
    driver.get("http://127.0.0.1:8050")

    # Wait until the heatmap is loaded
    heatmap = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "crime-heatmap"))
    )
    assert heatmap is not None

# Test 2 - does the dropdown populate correctly?
def test_dropdown_populates_correctly(driver):
    driver.get("http://127.0.0.1:8050")      # All are usng the same driver.get

    # Wait until the dropdown options are loaded
    dropdown = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "borough-selection"))
    )

    # Click to open the dropdown
    dropdown.click()

    # Wait for options to be visible
    options = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'Select-menu')]//div"))
    )

    # Extract text from options
    borough_names = [option.text for option in options]
    print("Dropdown options:", borough_names)

    # Ensure options exist
    assert len(borough_names) > 0, "Dropdown options did not load correctly."

# Test 3 - how does the app handle an empty borough selection? (edge case)
def test_empty_borough_selection(driver):
    driver.get("http://127.0.0.1:8050")

    # Wait for the dropdown to load and leave it unselected
    dropdown = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "borough-selection"))
    )

    # Click on the dropdown but do not select any borough
    dropdown.click()

    # Ensure that graphs are not shown (hidden by default)
    graph_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "graph-container"))
    )
    assert "display: none" in graph_container.get_attribute("style"), "Graph container should be hidden if no borough is selected."

# Test 4 - does the dashboard button work and show the graph?
def test_navigation_button(driver):
    driver.get("http://127.0.0.1:8050")

    # Wait for the dropdown to load
    dropdown = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "borough-selection"))
    )
    dropdown.click()

    # Wait for options to be visible
    options = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'Select-menu')]//div"))
    )

    # Select the first available option
    first_option = options[0]
    driver.execute_script("arguments[0].scrollIntoView(true);", first_option)
    WebDriverWait(driver, 10).until(EC.visibility_of(first_option))
    driver.execute_script("arguments[0].click();", first_option)

    # Wait for 'Go to Dashboard' button to be clickable
    navigate_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "navigate-button"))
    )

    # Ensure the button is in view
    driver.execute_script("arguments[0].scrollIntoView(true);", navigate_button)

    # Small delay to ensure the button is fully rendered
    time.sleep(1)

    # Click the button directly using ActionChains
    actions = ActionChains(driver)
    actions.move_to_element(navigate_button).click().perform()

    # Wait for the graph container to load
    graph_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "graph-container"))
    )

    # Scroll to the graph container (if needed)
    driver.execute_script("arguments[0].scrollIntoView();", graph_container)

    # Wait for the actual graph to appear inside the container
    graph_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "js-plotly-plot"))
    )

    # Confirm the graph is displayed
    assert graph_element.is_displayed(), "Graph is not visible on the dashboard."

# Unit Test to check what happens if there is no data
def test_empty_figure():
    # Call the function
    fig = empty_figure("No data available")
    
    # Check if the figure is an instance of go.Figure
    assert isinstance(fig, go.Figure), "The return value is not a Plotly Figure."
    
    # Check if the figure has the correct layout title
    assert fig.layout.title.text == "No data available", "The title of the figure is incorrect."
    
    # Check if there are annotations (for the message)
    assert len(fig.layout.annotations) == 1, "The figure should have exactly one annotation."
    assert fig.layout.annotations[0]['text'] == "No data available", "The annotation text is incorrect."


if __name__ == "__main__":
    pytest.main()
