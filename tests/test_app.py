import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
from webdriver_manager.chrome import ChromeDriverManager
from src.app import update_heatmap, geojson_data, crime_df

# # # Path to the ChromeDriver executable
# CHROME_DRIVER_PATH = './tests/chromedriver'     # For local testing only

# Keep url as a fixture so that it can be reused across all tests
@pytest.fixture(scope="module")
def app_url():
    """Fixture to store the app URL, which can be used across all tests."""
    return "http://127.0.0.1:8050"  

@pytest.fixture(scope="module")
def driver(app_url):
    """Fixture to initialise the Chrome WebDriver."""

    options = Options()
    options.add_argument("--headless")  # Run Chrome in headless mode
    # Use webdriver-manager to automatically manage the ChromeDriver
    service = ChromeService(executable_path=ChromeDriverManager().install())  # This will download and return the path to the latest chromedriver
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(app_url)  # Use the app URL from the fixture
    yield driver
    driver.quit()

#  Test 1 - does the heatmap load?
def test_load_heatmap(driver):
    """Test if the heatmap is loaded on the page."""

    # Wait until the heatmap is loaded
    heatmap = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "crime-heatmap"))
    )
    assert heatmap is not None

def test_dropdown_works(driver):
    """Test if the dropdown is clickable and shows options."""
    # Ensure dropdown is clickable
    dropdown = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "borough-selection"))
    )

    # Scroll into view
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)

    # Wait for potential overlay to disappear
    WebDriverWait(driver, 5).until(
        EC.invisibility_of_element_located((By.CLASS_NAME, "loading-spinner"))
)
    # Click using JavaScript to avoid interception
    driver.execute_script("arguments[0].click();", dropdown)

    assert dropdown.is_displayed(), "Dropdown should be visible and clickable."


# Test 3 - does the dashboard button work and show the graph?
def test_navigation_button(driver):
    """Test if the 'Go to Dashboard' button works and shows the graph."""

    dropdown = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.ID, "borough-selection"))
    )
    # Scroll to the dropdown to ensure it's in view
    driver.execute_script("arguments[0].scrollIntoView(true);", dropdown)
    time.sleep(0.5)  
    dropdown.click()

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

    # Scroll to the graph container 
    driver.execute_script("arguments[0].scrollIntoView();", graph_container)

    # Wait for the actual graph to appear inside the container
    graph_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "js-plotly-plot"))
    )

    # Confirm the graph is displayed
    assert graph_element.is_displayed(), "Graph is not visible on the dashboard."


# Test 4 - how does the app handle an empty borough selection? (edge case)
def test_empty_borough_selection(driver):
    """Test if the app handles an empty borough selection correctly."""

    dropdown = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "borough-selection"))
    )

    # Scroll to the dropdown to ensure it's in view
    driver.execute_script("arguments[0].scrollIntoView(true);", dropdown)

    # Wait a little to ensure no blocking element (like a spinner) is present
    time.sleep(0.5)  

    dropdown.click()

    # Wait for the 'Go to Dashboard' button to be clickable
    navigate_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "navigate-button"))
    )

    # Click the button directly using ActionChains
    actions = ActionChains(driver)  
    actions.move_to_element(navigate_button).click().perform()  # Click the button  

    # Ensure that graphs are not shown (hidden by default)
    graph_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "graph-container"))
    )
    assert "display: none" in graph_container.get_attribute("style"), "Graph container should be hidden if no borough is selected."



# Unit test for the update_heatmap callback
@pytest.fixture
def restore_data(monkeypatch):
    """Fixture to store and restore original crime_df and geojson_data."""      
    original_crime_df = crime_df
    original_geojson = geojson_data

    yield 

    # Restore the data after test execution
    monkeypatch.setattr("src.app.crime_df", original_crime_df)
    monkeypatch.setattr("src.app.geojson_data", original_geojson)


def test_update_heatmap_no_data(monkeypatch, restore_data):
    """
    Test update_heatmap callback when data is missing.
    It should return an empty figure with an error message.
    """

    # Simulate missing data
    monkeypatch.setattr("src.app.crime_df", None)
    monkeypatch.setattr("src.app.geojson_data", None)

    # Call the update_heatmap callback
    result = update_heatmap(1)  

    # # Debug output - internal check
    # print("DEBUG: ", result["layout"])

    assert "layout" in result, "Expected figure output with layout"
    assert "annotations" in result["layout"], "Expected annotations in layout"
    assert len(result["layout"]["annotations"]) > 0, "Expected at least one annotation"
    assert result["layout"]["annotations"][0]["text"] in ["No data available", "Error: No data available"], "Unexpected annotation text"

if __name__ == "__main__":
    pytest.main()
