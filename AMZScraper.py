from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from pathlib import Path
from dotenv import dotenv_values
import pyotp
import requests
import tempfile
from PIL import Image
import math
import os

class Order:
    """
    Represents a single order with delivery date, product names, and product URLs.
    """
    def __init__(self, driver, delivery_date, product_names, product_urls):
        self.driver         = driver
        self.delivery_date  = delivery_date
        self.product_names  = product_names
        self.product_urls   = product_urls

    def __str__(self):
        return f"Products: {self.product_names}, Delivery Date: {self.delivery_date}, URLs: {self.product_urls}"

def read_env_variables():
    """
    Reads environment variables from a .env file for credentials and settings.
    Returns:
        dict: Dictionary of environment variables.
    """
    env_path = Path(__file__)                       # Get the path of the current script
    env_file = f"{env_path.parent}/config.env"     # Path to the .env file
    return dotenv_values(env_file)                  # Load environment variables

base_url = "https://www.amazon.de"                  # Base URL for Amazon.de (adjust if you're in a different region)
env_variables = read_env_variables()                # Load credentials/settings

def page_load_complete(driver):
    """
    Checks if the page has completely loaded.
    Args:
        driver (webdriver): Selenium WebDriver instance.
    Returns:
        bool: True if page is fully loaded, False otherwise.
    """
    # Use JavaScript to check if document is ready
    return driver.execute_script("return document.readyState") == "complete"

def generate_otp(otp_secret):
    """
    Generates a one-time password (OTP) using the provided secret.
    Args:
        otp_secret (str): The OTP secret.
    Returns:
        str: The generated OTP code.
    """
    totp = pyotp.TOTP(otp_secret)   # Create TOTP object
    return totp.now()               # Generate current OTP and return it

def get_delivery_dates(driver):
    """
    Executes a JS script to extract delivery date elements from the page.
    Args:
        driver (webdriver): Selenium WebDriver instance.
    Returns:
        list: Sorted list of delivery date elements.
    """
    with open("getDeliveryDates.js", "r") as file:
        script = file.read()  # Read the JS script
        
    delivery_elements = driver.execute_script(script)                       # Execute JS in browser
    
    return sorted(delivery_elements, key=lambda x: x['y'], reverse=True)    # Sort delivery elements by their y-position (descending)

def get_products(driver):
    """
    Executes a JS script to extract product elements from the page.
    Args:
        driver (webdriver): Selenium WebDriver instance.
    Returns:
        list: Sorted list of product elements.
    """
    with open("getProducts.js", "r") as file:
        script = file.read()
        
    products = driver.execute_script(script)
    
    for product in products:
        product['text'] = product['text'].split('\n')[0]        # Only keep the first line of the product title

    return sorted(products, key=lambda x: x['y'], reverse=True) # Sort products by their y-position (descending)

def get_product_urls(driver):
    """
    Executes a JS script to extract product image URLs from the page.
    Args:
        driver (webdriver): Selenium WebDriver instance.
    Returns:
        list: List of product URL elements.
    """
    with open('getProductUrls.js', 'r') as file:
        script = file.read()
        
    url_elements = driver.execute_script(script)
    
    for url_element in url_elements:                    # Extract the image URL from the HTML string which also contains other attributes we don't need
        current_image_url   = url_element['html'].split('src="')[1].split('"')[0]
        url_element['html'] = current_image_url
        
    return url_elements

def login(driver):
    """
    Logs into Amazon using credentials and OTP from environment variables.
    Args:
        driver (webdriver): Selenium WebDriver instance.
    """
    try:
        driver.get(f"{base_url}/gp/css/order-history?ref_=nav_orders_first")    # Open Amazon order history
        WebDriverWait(driver, 10).until(page_load_complete)                     # Wait for page to load
        
        email = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ap_email")))
        email.send_keys(env_variables["EMAIL"])                                 # Enter email
        
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "continue"))).click()            # Click continue to proceed to the password page
        
        password = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ap_password")))
        password.send_keys(env_variables["PASSWORD"])                           # Enter password
        
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "signInSubmit"))).click()        # Click sign in button
        
        otp_input   = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "auth-mfa-otpcode")))
        otp_code    = generate_otp(env_variables["OTP_SECRET"])                 # Generate OTP code
        otp_input.send_keys(otp_code)                                           # Enter OTP in the input field
        
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "auth-signin-button"))).click()  # Click sign in button
        print("--> Login successful!")
    except Exception as e:
        print(f"--> Login process failed: {e}. Closing driver.")
        driver.quit()

def get_orders(driver):
    """
    Retrieves all orders from the user's Amazon order history.
    Args:
        driver (webdriver): Selenium WebDriver instance.
    Returns:
        list: List of Order objects.
    """
    orders          = []
    number_of_pages = int(env_variables["NUMBER_OF_PAGES"])  # How many pages to process (depends on how many orders you usually have)
    
    for page in range(number_of_pages):
        driver.get(f"{base_url}/your-orders/orders?startIndex={page*10}&ref_=ppx_yo2ov_dt_b_pagination_1_{page+1}") # Load each order page one by one
        WebDriverWait(driver, 10).until(page_load_complete)                                                         # Wait for page to load
        
        delivery_dates  = get_delivery_dates(driver)    # Extract delivery date elements
        products        = get_products(driver)          # Extract product elements
        product_urls    = get_product_urls(driver)      # Extract product image URLs
        
        combined_products = []
        
        for product in products:
            # Try to find the matching image URL for each product (by y-position)
            matching_url = next((url for url in product_urls if url['y'] == product['y']), None)
            combined_products.append({
                'text': product['text'],
                'y': product['y'],
                'url': matching_url['html'] if matching_url else None
            })
            
        combined_products.sort(key=lambda x: x['y'], reverse=True) # Sort products by their y-position (descending)
        
        # Group products by delivery date within the same order
        for delivery_date in delivery_dates:
            
            product_list = []
            
            for product in combined_products:
                if product['y'] > delivery_date['y']:
                    product_list.append(product)
                else:
                    break
                
            if product_list:
                # Create Order object for each group
                orders.append(Order(
                    driver=driver,
                    delivery_date=delivery_date['text'],
                    product_names=[p['text'] for p in product_list],
                    product_urls=[p['url'] for p in product_list],
                ))
                
            combined_products = [p for p in combined_products if p not in product_list] # Remove products that have already been grouped
        print(f"Page {page+1} of {number_of_pages} processed.")
        
    return orders

def get_deliveries_today(orders):
    """
    Filters orders scheduled for delivery today.
    Args:
        orders (list): List of Order objects.
    Returns:
        list: Orders with delivery today.
    """
    # Check for "Zustellung heute" or "Ankunft heute" in delivery date
    return [order for order in orders if ("Zustellung heute" in order.delivery_date or "Ankunft heute" in order.delivery_date)]

def get_deliveries_tomorrow(orders):
    """
    Filters orders scheduled for delivery tomorrow.
    Args:
        orders (list): List of Order objects.
    Returns:
        list: Orders with delivery tomorrow.
    """
    # Check for "Zustellung morgen" or "Ankunft morgen" in delivery date
    return [order for order in orders if ("Zustellung morgen" in order.delivery_date or "Ankunft morgen" in order.delivery_date)]

def get_deliveries_total(orders):
    """
    Filters all orders with a delivery date.
    Args:
        orders (list): List of Order objects.
    Returns:
        list: All orders with any delivery date.
    """
    # Check for any "Zustellung" or "Ankunft" in delivery date
    return [order for order in orders if ("Zustellung" in order.delivery_date or "Ankunft" in order.delivery_date)]

def download_image(url):
    """
    Downloads an image from a URL and saves it as a temporary file.
    Args:
        url (str): Image URL.
    Returns:
        str: Path to the temporary image file.
    """
    response = requests.get(url, stream=True)   # Download image data using the URL and the requests library
    if response.status_code == 200:             # Check if the request was successful
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')    # Create temp file for the image
        for chunk in response.iter_content(1024):
            temp_file.write(chunk)                                              # Write image data in chunks
        temp_file.close()
        return temp_file.name                                                   # Return path to temp file
    else:
        raise Exception("Image could not be downloaded.")

def get_images(orders):
    """
    Downloads the first product image for each order.
    Args:
        orders (list): List of Order objects.
    Returns:
        list: List of file paths to downloaded images.
    """
    files = []
    for order in orders:
        # Only try to download if a product image URL exists
        if order.product_urls and order.product_urls[0]:
            file_name = download_image(order.product_urls[0])
            files.append(file_name)
    return files

def create_dynamic_collage(image_paths, output_path="collage.png", tile_size=(300, 300)):
    """
    Creates a collage from a list of image file paths, arranges them in a grid, and deletes the temp files.
    Args:
        image_paths (list): List of image file paths.
        output_path (str): Path to save the collage image.
        tile_size (tuple): Size (width, height) of each image tile.
    """
    if not image_paths:
        print("No images provided for the collage.")
        return

    n       = len(image_paths)          # Number of images
    cols    = math.ceil(math.sqrt(n))   # Number of columns for grid (square-like)
    rows    = math.ceil(n / cols)       # Number of rows
    
    collage_width = cols * tile_size[0]    # Collage total width
    collage_height = rows * tile_size[1]   # Collage total height
    
    collage = Image.new('RGBA', (collage_width, collage_height), (255, 255, 255, 255))  # New blank image

    for idx, img_path in enumerate(image_paths):
        try:
            img = Image.open(img_path).convert('RGBA')      # Open and convert image
            img = img.resize(tile_size)                     # Resize to tile size
            x   = (idx % cols) * tile_size[0]               # X position in grid
            y   = (idx // cols) * tile_size[1]              # Y position in grid
            collage.paste(img, (x, y))                      # Paste image into collage
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

    collage.save(output_path)                               # Save the final collage image
    print(f"Collage saved to {output_path}")

    # Delete all temporary image files (remove this if you want to process them later)
    for img_path in image_paths:
        try:
            os.remove(img_path)
        except Exception as e:
            print(f"Could not delete temporary file {img_path}: {e}")

def main():
    driver = webdriver.Chrome()  # Start Chrome browser
    try:
        login(driver)            # Perform login
        while True:
            orders          = get_orders(driver)            # Retrieve all orders
            
            orders_today    = get_deliveries_today(orders)      # Orders for today
            orders_tomorrow = get_deliveries_tomorrow(orders)   # Orders for tomorrow
            orders_total    = get_deliveries_total(orders)      # All orders with delivery

            # Print pending orders
            for order in orders_today:
                print(f"Pending order (today): {order.product_names}, Delivery Date: {order.delivery_date}, URLs: {order.product_urls}")
            for order in orders_tomorrow:
                print(f"Pending order (tomorrow): {order.product_names}, Delivery Date: {order.delivery_date}, URLs: {order.product_urls}")
            for order in orders_total:
                print(f"Pending order (general): {order.product_names}, Delivery Date: {order.delivery_date}, URLs: {order.product_urls}")

            # Download images for all orders and create a collage
            tmp_images = get_images(orders_today)
            create_dynamic_collage(tmp_images, output_path="collage.png", tile_size=(300, 300))

            time.sleep(120)  # Wait for 2 minutes before repeating

    finally:
        driver.quit()  # Always close the browser when done

if __name__ == "__main__":
    main()