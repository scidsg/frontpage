import requests
import time
import sys
import textwrap
import qrcode
from waveshare_epd import epd2in13_V3
from PIL import Image, ImageDraw, ImageFont


def fetch_article_count():
    try:
        response = requests.get("https://ddosecrets.local/api/article_count")
        if response.status_code == 200:
            return response.json().get("count")
        else:
            print(f"Error fetching article count: Status Code {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Error in request: {e}")
        return None


def display_article_count(epd, count):
    print("Displaying article count...")
    image = Image.new("1", (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)

    # Fonts and texts
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 11)
    count_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 10)
    instruction_font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 10
    )
    title_text = "Distributed Denial\nof Secrets"
    count_text = f"Articles: {count}"
    instruction_text = "Scan the QR code for your addresses"

    # vCard data
    vcard = (
        "BEGIN:VCARD\n"
        "VERSION:3.0\n"
        "ORG:Distributed Denial of Secrets\n"
        "EMAIL;TYPE=PREF,INTERNET:info@ddosecrets.com\n"
        "URL:https://ddosecrets.local\n"
        "URL:https://ddosecrets.com\n"
        "URL:http://ONION_ADDRESS\n"
        "END:VCARD"
    )

    # Generate QR code
    qr = qrcode.QRCode(
        version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=1
    )
    qr.add_data(vcard)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((epd.width, epd.width), Image.NEAREST)
    image.paste(qr_img, (0, 0))

    # Calculate text positions and widths
    text_x = epd.width + 10
    max_text_width = epd.height - text_x - 5

    # Function to calculate the height of wrapped text
    def calc_wrapped_text_height(text, font, max_width):
        wrapped_text = textwrap.fill(text, width=max_width // font.getsize("A")[0])
        return draw.multiline_textsize(wrapped_text, font=font)[1]

    # Calculate the total height of all text blocks
    total_text_height = (
        calc_wrapped_text_height(title_text, title_font, max_text_width)
        + calc_wrapped_text_height(count_text, count_font, max_text_width)
        + calc_wrapped_text_height(instruction_text, instruction_font, max_text_width)
        + 20
    )  # 20 for spacing between lines

    # Calculate the starting Y position for vertical centering
    start_y = (epd.width - total_text_height) // 2

    # Function to draw wrapped text
    def draw_wrapped_text(text, font, x, y, max_width):
        wrapped_text = textwrap.fill(text, width=max_width // font.getsize("A")[0])
        draw.multiline_text((x, y), wrapped_text, font=font, fill=0)
        return y + draw.multiline_textsize(wrapped_text, font=font)[1] + 10

    # Draw the texts
    current_y = start_y
    current_y = draw_wrapped_text(title_text, title_font, text_x, current_y, max_text_width)
    current_y = draw_wrapped_text(count_text, count_font, text_x, current_y, max_text_width)
    draw_wrapped_text(instruction_text, instruction_font, text_x, current_y, max_text_width)

    # Display the image
    epd.display(epd.getbuffer(image.rotate(90, expand=True)))


def display_splash_screen(epd, image_path, display_time):
    print("Displaying splash screen...")
    image = Image.open(image_path)
    image = image.convert("1")  # Convert image to black and white
    image = image.resize((epd.height, epd.width), Image.BICUBIC)  # Resize to fit the screen
    epd.display(epd.getbuffer(image))
    time.sleep(display_time)


def main():
    print("Starting blog display script")
    epd = epd2in13_V3.EPD()
    epd.init()
    print("EPD initialized")

    # Display splash screen for 3 seconds
    display_splash_screen(epd, "static/splash.png", 3)

    try:
        while True:
            article_count = fetch_article_count()
            if article_count is not None:
                display_article_count(epd, article_count)
            else:
                print("Unable to fetch article count.")
            time.sleep(3600)  # Update interval
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
