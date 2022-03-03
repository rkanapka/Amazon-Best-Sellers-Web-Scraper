# Amazon Best Sellers WEB Scrape
# By Rimvydas Kanapka

import httplib2
import csv
import time

from bs4 import BeautifulSoup, SoupStrainer
from itertools import islice
from datetime import datetime

_amazon_url = 'https://www.amazon.com/Best-Sellers/zgbs'

def _get_categories_with_links(response):
    best_sellers_categories = {}
    for link in BeautifulSoup(response, parse_only=SoupStrainer('a')):
        if link.has_attr('href') and 'best-sellers-' in link['href'].lower():
            best_sellers_categories[link.get_text()] = f"https://www.amazon.com{link['href']}"
    return best_sellers_categories

def _parse_categories_data(http, best_sellers_categories):
    category_with_products = {}
    for category, url_link in best_sellers_categories.items():
        category_with_products[category] = []

        status, response = http.request(url_link)
        soup = BeautifulSoup(response, "html")
        all_product_divs = soup.findAll("div", {"id": "gridItemRoot"})

        _parse_product(category_with_products, category, all_product_divs)
            
    return category_with_products

def _parse_product(category_with_products, category, all_product_divs):
    for count, div in enumerate(islice(all_product_divs, 10), start=1):
        product_name = (
                div.find("div", {"class": "_p13n-zg-list-grid-desktop_truncationStyles_p13n-sc-css-line-clamp-4__2q2cc"}) or
                div.find("div", {"class": "_p13n-zg-list-grid-desktop_truncationStyles_p13n-sc-css-line-clamp-3__g3dy1"}) or
                div.find("div", {"class": "_p13n-zg-list-grid-desktop_truncationStyles_p13n-sc-css-line-clamp-2__EWgCb"}) or
                div.find("div", {"class": "_p13n-zg-list-grid-desktop_truncationStyles_p13n-sc-css-line-clamp-1__1Fn1y"})
            )
        product_name = product_name.get_text() if product_name else 'Missing'

        product_price = (
                div.find("span", {"class": "p13n-sc-price"}) or
                div.find("span", {"class": "_p13n-zg-list-grid-desktop_price_p13n-sc-price__3mJ9Z"}) or
                div.find("span", {'class": "a-size-base a-color-price"'})
            )
        product_price = product_price.get_text() if product_price else 'Missing'

        rating_row = div.find("div", {"class": "a-icon-row"})
        if rating_row:
            product_rating = rating_row.find("span", {"class": "a-icon-alt"})
            users_count = rating_row.find("span", {"class": "a-size-small"})
        else:
            product_rating = div.find("span", {"class": "a-icon-alt"})
            users_count = div.find("span", {"class": "a-size-small"})

            
        product_rating = product_rating.get_text()[:3] if product_rating else 'None'  # show only rating with *.*
        users_count = users_count.get_text().replace(",", ".") if users_count else 'None'
        # check if we parsed float number
        try:
            float(users_count)
        except ValueError:
            users_count = 'None'

        product_img = div.find("img", {"alt": product_name[:125]})  # img alt max length is 125 symbols
        product_img = product_img['src'] if product_img and product_img.has_attr('src') else 'Missing'

        category_with_products[category].append(
                {
                    "No": count,
                    "Name": product_name,
                    "Price": product_price,
                    "Rating": product_rating,
                    "Count of Users Rated": users_count,
                    "Image": product_img
                }
            )

def _create_best_sellers_csv(category_with_products, csv_file, csv_columns):
    try:
        with open(csv_file, 'w', newline="", encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            _write_data_to_csv(category_with_products, writer)
    except IOError as error_io:
        print(f"I/O error: {error_io}")

def _write_data_to_csv(category_with_products, writer):
    for category, products in category_with_products.items():
        writer.writerow({"No": "", "Name": category, "Price": "", "Rating": "", "Count of Users Rated": "", "Image": ""})
        for product in products:
            writer.writerow(product)

if __name__ == "__main__":
    start_time = time.time()

    http = httplib2.Http()
    status, response = http.request(_amazon_url)

    best_sellers_categories = _get_categories_with_links(response)
    print(f'Total categories count: {len(best_sellers_categories)}')

    category_with_products = _parse_categories_data(http, best_sellers_categories)

    current_date_time = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    csv_file = f"amazon_best_sellers_{current_date_time}.csv"
    csv_columns = ["No","Name","Price", "Rating", "Count of Users Rated", "Image"]

    _create_best_sellers_csv(category_with_products, csv_file, csv_columns)

    end_time = time.time()
    print(f"Total execution time: {end_time - start_time}")
