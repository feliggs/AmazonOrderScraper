# AmazonOrderScraper

This project automates the retrieval of your Amazon orders, downloads product images, and creates a dynamic collage of your recent purchases using Python and JavaScript.
Since I am based in Germany, this project uses amazon.de as the default. If you want to use it with another Amazon site (like amazon.com or amazon.co.uk), you need to adjust the base URL accordingly. Also, the detection of delivery dates (like "today" or "tomorrow") currently relies on German strings (e.g., "Zustellung heute" for "Delivery today"). Since I don't have a UK/US Amazon account, I couldn't test this-so you'll need to make these adjustments yourself for other languages and marketplaces.

## Features

- **Automated Login:** Secure login to your Amazon account using credentials and OTP (2FA).
- **Order Scraping:** Retrieves product names, delivery dates, and product images from your order history.
- **Image Collage:** Downloads product images and arranges them into a dynamic grid collage to display them nicely (e.g. in HomeAssistant).
- **Temporary Files:** Images are stored as temporary files that are removed after collage creation.
- **Configurable:** Easily adjust the number of order pages to process, depending on how much you usually order.

## Configuration

Edit the `config.env` in the project directory with the following content. You need to add pyotp as an authenticator method in your Amazon account first to retrieve your token!

| Variable         | Description                                                    | Example Value                |
|------------------|----------------------------------------------------------------|------------------------------|
| `EMAIL`          | Your Amazon account email address                              | `your-email@example.com`     |
| `PASSWORD`       | Your Amazon account password                                   | `yourpassword123`            |
| `OTP_SECRET`     | TOTP secret for 2-factor authentication (from pyotp        )   | `ABCDEFGHIJKLMNOP`           |
| `NUMBER_OF_PAGES`| Number of order pages to process                               | `2`                          |

## Installation

1. **Clone this repository**
2. **Install dependencies** `pip install -r requirements.txt`
3. **Download ChromeDriver** Make sure you have [ChromeDriver](https://chromedriver.chromium.org/downloads) installed and in your `PATH`.

## Usage

1. **Adjust config & code** Fill in your credentials, OTP etc. --> In addition adjust the images for the collage (normally it generates it using orders for today)
2. **Run the script** Run the script and it will scrape your orders every 2 minutes, extract Orders and generate a current collage image.

## Requirements

See [`requirements.txt`](./requirements.txt) for all dependencies:

- selenium
- python-dotenv
- pyotp
- requests
- pillow

## Notes

- This script is for personal use only on your own Amazon account.
- Your credentials and OTP secret are stored locally in the `.env` file and should never be shared.
- **Use at your own risk:** This script is provided for demonstration and educational purposes only, to show what is technically possible.  
- I do not accept any liability for any direct, indirect, incidental, or consequential damages resulting from the use or misuse of this script.  
- There is no warranty of any kind, express or implied.  
- By using this script, you acknowledge and agree that you do so entirely at your own risk and responsibility.
