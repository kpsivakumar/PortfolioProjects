"""
This code is created by siva, any questions/comments share at kpsivakumar@gmail.com
"""
import datetime
import random
import time
import os.path

import pandas as pd
from urllib.parse import urlparse
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys


def get_selsoup(url, query=None):
    """
    Receive a url and query string, scrap through selenium and return soup object
    :param url: input URL
    :param query: optional query fof Google search
    :return: soup object of the search result page
    """
    options = Options()
    options.headless = True

    #if this code is executed in AWS linux use the one with 'options' only
    browser = webdriver.Chrome(options=options) # for AWS Linux

    try:
        browser.get(url)
        time.sleep(1)
        if query is not None:
            search = browser.find_element_by_name('q')
            search.send_keys(query)
            search.send_keys(Keys.RETURN)
            time.sleep(1)

        html_page = browser.page_source
        soup = BeautifulSoup(html_page, 'lxml')
    except:
        soup = None

    browser.close()
    return soup


def get_next_page_url(soup):
    """
    Search for next page URL in the supplied soup object and return as string

    :param soup: soup object
    :return: URL string
    """
    next_page = None
    try:
        for tag in soup.find_all('a', class_='pn'):
            if tag.text.strip() == "Next":
                next_page = str('http://www.google.com' + str(tag.get('href', None).strip()))
                break
    except:
        next_page = None

    return next_page


def scrap_pages(soup, page_num, query, last_num):
    """
    Scrap pages for the soup provided for the search lists, links, rank and return a list of scrapped outputs
    :param soup: soup object of html page
    :param page_num: page number of soup object
    :param last_num: last count of previous scrapped list if any
    :return: list of scrapped values
    """
    page_search_results_list = []
    page_rank = last_num
    scrap_date_time = datetime.datetime.today().strftime('%Y%m%d %H%M')

    for search_results in soup.find_all('div', id='rso'):
        for search_item in search_results.findAll('div', class_='rc'):
            item_title = ""
            item_link = ""
            item_meta = ""
            for itemtitle in search_item.findAll('div', class_='r'):
                item_title = itemtitle.find('h3').get_text().strip()
                item_link = itemtitle.find('a').get('href', None).strip()
                item_host = urlparse(item_link).hostname

            for itemmeta in search_item.findAll('div', class_='s'):
                for meta in itemmeta.find_all('span', class_='st'):
                    item_meta = ' '.join(meta.text.split())  # + meta.next_sibling
            page_rank += 1
            page_search_results_list.append([query,
                                             item_host,
                                             page_rank,
                                             page_num,
                                             scrap_date_time,
                                             item_title,
                                             item_link,
                                             item_meta])
    return page_search_results_list


if __name__ == '__main__':
    # Main function of web scrapping python program
    base_url = "http://www.google.com"
    print(f"Search Engine: {base_url}\n------------------------------------")

    # Search keywords imported from predefined file
    search_keywords = pd.read_csv("./SearchKeywords.csv")
    queries = list(search_keywords['Keywords'])
    pg_num = 10

    scrap_date_time = datetime.datetime.today().strftime('%Y%m%d %H%M')
    timestamp = str('_'.join(scrap_date_time.split()))

    # default file names
    csv_file_name = './google_page_rank_' + timestamp.split('_')[0] +'.csv'
    log_file_name = './Google_Page_rank_' + timestamp + 'Log.txt'

    if os.path.isfile(csv_file_name):
        new_file = False
    else:
        new_file = True

    # log file content
    header = "Search Keyword                          Page      Status         "
    log_file = open('./' + log_file_name, "a")
    log_file.write(header)

    total_kwords = len(queries)
    isearch_count = 0


    for query in queries:

        scraped_search_list = []
        query = query.strip()
        isearch_count +=1

        if len(query) != 0:
            for page in range(pg_num):
                current_page = page + 1
                print(f"Scrapping Search for: {query} ({isearch_count:2}/{total_kwords})", end='')
                print(f": Pages ({current_page:2}/{pg_num})...", end='')

                if current_page == 1:
                    soup = get_selsoup(base_url, query)
                else:
                    time.sleep(random.randint(4, 10))
                    soup = get_selsoup(next_page_url)

                if soup is not None:  # if selenium scrap is not successful soup will be None
                    current_page_results = scrap_pages(soup, current_page, query, len(scraped_search_list))
                    scraped_search_list += current_page_results
                    print(" Done")

                    next_page_url = get_next_page_url(soup)
                    log_file.write("\n{0:40}{1:6}    {2}".format(query, current_page, 'Success'))
                    if next_page_url is None:
                        print(f"Search results are available for {current_page} pages only.")
                        break
                else:
                    log_file.write("\n{0:40}{1:6}    {2}".format(query, current_page, 'Failed'))
                    break
        else:
            continue

        current_scraped_list_df = pd.DataFrame(scraped_search_list,
                                               columns=['SearchKeyword',
                                                        'HostName',
                                                        'PageRank',
                                                        'SearchPageNo',
                                                        'DateTime',
                                                        'LinkTitle',
                                                        'URL',
                                                        'MetaContent'])
        if new_file is True:
            current_scraped_list_df.to_csv(csv_file_name, sep=',', encoding='utf-8', index=False)
            new_file = False
        else:
            current_scraped_list_df.to_csv(csv_file_name, mode='a', sep=',', encoding='utf-8', header=False,
                                           index=False)

        time.sleep(random.randint(5, 10))  # random wait time between search sets


    log_file.close()

    print(f"Saving logs into {log_file_name}... Done")


    print(f"Done\n\nOpen {log_file_name} and {csv_file_name} for more details")

    print("\nScrapping completed successfully!")

