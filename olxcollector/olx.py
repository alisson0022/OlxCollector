from requests import get
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import pytz

# Ad class to centralize informations
class Ad:
    def __init__(self, url: str, title: str, image_url: str, price: float, date: "datetime.datetime", professional: bool):
        self.url = url
        self.title = title
        self.image_url = image_url
        self.price = price
        self.date = date
        self.professional = professional

class Page:
    def __init__(self, html: str, number: int, ads: list):
        self.html = html
        self.number = number
        self.ads = ads

class Search:
    def __init__(self, last_page_number: int, pages: list):
        self.last_page_number = last_page_number
        self.pages = pages

def __get_page_html(url: str) -> str:
    
    customHeaders = {
        # The generic headers were taken from a Mozilla FireFox's request
        "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection" : "close",
        "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"
    }
    res = get(url, headers = customHeaders) # Response
    return res.text #html code

def __get_brazils_current_date():
    GMT_3 = pytz.timezone('Brazil/East') # Brasília's date time (UTC-3)
    dt_gmt_3 = datetime.now(GMT_3)
    return dt_gmt_3

def __convert_olx_date_to_datetime(olx_date: str, olx_hour: str) -> "datetime.datetime":
    hour_slices = olx_hour.split(":")
    post_hour = int(hour_slices[0])
    post_minute = int(hour_slices[1])

    brazil_date = __get_brazils_current_date()

    if(olx_date == "Ontem"):
        yesterday = brazil_date - timedelta(days=1)
        return datetime(yesterday.year, yesterday.month, yesterday.day, hour=post_hour, minute=post_minute, second=0)
    elif(olx_date == "Hoje"):
        return datetime(brazil_date.year, brazil_date.month, brazil_date.day, hour=post_hour, minute=post_minute, second=0)

    date_slices = olx_date.split(" ")

    post_day = int(date_slices[0])
    post_month = date_slices[1]

    #ugly code for now but that will do :/
    formattedMonth = None
    if post_month == "jan":
        formattedMonth = 1
    elif post_month == "fev":
        formattedMonth = 2
    elif post_month == "mar":
        formattedMonth = 3
    elif post_month == "abr":
        formattedMonth = 4
    elif post_month == "mai":
        formattedMonth = 5
    elif post_month == "jun":
        formattedMonth = 6
    elif post_month == "jul":
        formattedMonth = 7
    elif post_month == "ago":
        formattedMonth = 8
    elif post_month == "set":
        formattedMonth = 9
    elif post_month == "out":
        formattedMonth = 10
    elif post_month == "nov":
        formattedMonth = 11
    elif post_month == "dez":
        formattedMonth = 12
    
    return datetime(brazil_date.year, formattedMonth, post_day, hour=post_hour, minute=post_minute, second=0)

def __get_page_number_by_url(page_url: str) -> int:
    match = re.search(r'o=\d*', page_url, re.IGNORECASE)
    if bool(match) == False:
        print("Page number not found by url")
        return -1
    
    pattern = re.compile("o=", re.IGNORECASE)
        
    return int(pattern.sub("", match[0]))

def __get_page_number_by_html(page_html: str) -> int:
    bs = BeautifulSoup(page_html, features='html.parser')

    found_div = bs.select("div[selected]")
    if len(found_div) == 0:
        print("Page number not found by html")
        return -1
    
    return int(found_div[0].string)

def __get_last_page_number(html: str) -> int:
    try:
        bs = BeautifulSoup(html, features="html.parser")
        last_page_url = str(bs.find("span", string="Última pagina").find_parent("a")["href"])
        return __get_page_number_by_url(last_page_url)
    except:
        print("Error to find the last page number")
        return -1

#TODO Ajust this shit :/
def __convert_string_to_money(money_string: str):
    if money_string == None:
        return -1
    without_dollar_sign = re.sub(r"R\$ ", "", money_string)
    return int(re.sub(r"\.", "", without_dollar_sign))

def __scrap_page(page_url: str) -> Page:
    page_html = __get_page_html(page_url)

    bs = BeautifulSoup(page_html, features="html.parser")

    page_number = __get_page_number_by_html(page_html)

    ad_list = bs.find("ul", id="ad-list").find_all("li")

    ads = []
    for ad in ad_list:
        ad_base = ad.find_next("a")

        # Ad url
        ad_url = ad_base["href"]

        # Ad title
        ad_title = ad_base["title"]

        ad_main_div = ad_base.find_next("div")

        # Display image url
        ad_image_url = ad_main_div.contents[0].find_all_next("img")[0]["src"]
        
        # Informations such as: price, date and hour of post
        ad_info_div = ad_main_div.contents[1]

        # We'll jump straight to the second div because we already have the ad's name
        ad_top_info = ad_info_div.contents[0].contents[1]
        
        ad_price = __convert_string_to_money(ad_top_info.contents[1].find_next("span").string)

        ad_date_and_hour = ad_top_info.contents[3].find_all("span")

        ad_date = __convert_olx_date_to_datetime(ad_date_and_hour[0].string, ad_date_and_hour[1].string)

        ad_bottom_info = ad_info_div.contents[1].find_all("span")

        ad_location = ad_bottom_info[0].string

        ad_is_professional = False
        if(len(ad_bottom_info) > 1 and re.search('Profissional', ad_bottom_info[1].string, re.IGNORECASE)):
            ad_is_professional = True

        ads.append(Ad(ad_url, ad_title, ad_image_url, ad_price, ad_date, ad_is_professional))
    return Page(page_html, page_number, ads)

def __sub_page_url_number(url: str, new_number: int):
    if bool(re.search(r'o=\d*', url)) == False:
        return re.sub(r'\?q=', f'?o={new_number}&q=', url)
    
    return re.sub(r'o=\d*', f'o={new_number}', url)

# Get informations from pages
def search(url: str, number_of_pages: int = -1) -> Search:
    main_page = __scrap_page(url)

    print("\nFirst page scrapped successfully.")

    if number_of_pages == -1:
        return Search(number_of_pages, [main_page])

    last_page_number = __get_last_page_number(main_page.html)
    if last_page_number == -1:
        print("\nInvalid page or url")
        return Search(0, [])

    if number_of_pages > last_page_number:
        print("\nThe number of pages exceeds the max number of pages so it'll be modified to the max number of pages.")
        number_of_pages = last_page_number  
        
    print("\nLast page number found.")

    pages = [main_page]

    for page_number in range(main_page.number+1, main_page.number+number_of_pages):
        print(f"Scrapping page: {page_number}.")
        pages.append(__scrap_page(__sub_page_url_number(url, page_number)))
    
    print(f'Scrapped pages: {number_of_pages}')
    
    return Search(last_page_number, pages)