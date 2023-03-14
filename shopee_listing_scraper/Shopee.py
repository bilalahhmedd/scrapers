#!/usr/bin/env python
# coding: utf-8



import argparse

# Initiate the parser
parser = argparse.ArgumentParser()

# Add long and short argument
parser.add_argument("--output", "-o", help="set output file name")
parser.add_argument("--numberOfProducts", "-p", help="Set Number of Scraped Products")
parser.add_argument("--site", "-s", help="Set Domain of Shopee")
parser.add_argument("--keyword", "-k", help="Search keyword")



# Read arguments from the command line
args = parser.parse_args()
Output="Output.csv"
EndCounter=200
site="sg"

search=""
# Check for --width
if args.output:
    Output=args.output

if args.numberOfProducts:
    try:
        EndCounter=int(args.numberOfProducts)
    except:
        print("Number of scraped Product Should be number")
        exit()


if args.keyword:
    search=args.keyword
else:
    print("Search keyword must be given")
    exit()






if args.site:
    if args.site=="indonesia" or args.site=="co.id":
        site="co.id"
    elif args.site=="vietnam" or args.site=="vn":
        site="vn"
    elif args.site=="singapore" or args.site=="sg":
        site="sg"
    else:
        print("Invalid site name \n")
        print("Correct Inputs are:")
        print("indonesia|co.id")
        print("vietnam|vn")
        print("singapore|sg")






import requests
import random
import time
import pandas as pd
import re
import csv
from getpass import getpass
from time import sleep
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
import os
import chromedriver_autoinstaller
from selenium import webdriver

opt = webdriver.ChromeOptions()
opt.add_argument("--start-maximized")

chromedriver_autoinstaller.install()



def get_header():
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
        'content-type': 'text'
    }

def retry_with_backoff(retries=3, backoff_in_seconds=1):
    def rwb(func):
        def wrapper(url):
            x = 0
            while True:
                try:
                    return func(url)
                except:
                    if x == retries:
                        raise
                    else:
                        sleep = (backoff_in_seconds * 2 ** x +
                                 random.uniform(0, 1))
                        time.sleep(sleep)
                        x += 1
        return wrapper
    return rwb


@retry_with_backoff()
def curl(url: str, timeout: int=10) -> dict:
    return requests.get(
        url,
        headers=get_header(),
        timeout=timeout
    ).json()



from datetime import datetime
import concurrent.futures


import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_total(keyword):
    url = "https://shopee."+site+"/api/v4/search/search_items?by=relevancy&keyword={}&limit=60&newest=0&order=desc&page_type=search&scenario=PAGE_GLOBAL_SEARCH&version=2".format(keyword)

    return curl(url)['total_count']

def get_keyword_encoded(keyword):
    return "%20".join(key for key in keyword.split())

def get_all_data(url: str) -> list:
    data = curl(url)
    results = []
    try:
        for d in data['items']:
            results.append(d['item_basic'])
    except Exception as e:
        # logger.error(e)
        pass

    return results

def get_neccesary_data(data: list) -> list:
    results = []
    try:
        for item in data:
            results.append(
                {
                    'product_id': item['itemid'],
                    'product_name': item['name'],
                    'product_image': r'https://cf.shopee.'+site+'/file/{}_tn'.format(item['image']),
                    'product_link': r'https://shopee.'+site+'/{}-i.{}.{}'.format(item['name'], item['shopid'], item['itemid']),
                    'category_id': item['catid'],
                    'label_ids': item['label_ids'],
                    'product_brand': item['brand'],
                    'product_price': item['price'] if item['raw_discount'] == 0 else item['price_before_discount'],
                    'product_discount': item['raw_discount'],
                    'currency': item['currency'],
                    'stock': item['stock'],
                    'sold': item['sold'],
                    'is_on_flash_sale': item['is_on_flash_sale'],
                    'rating_star': item['item_rating']['rating_star'],
                    'rating_count': item['item_rating']['rating_count'],
                    'rating_with_context': item['item_rating']['rcount_with_context'],
                    'rating_with_image': item['item_rating']['rcount_with_image'],
                    'is_freeship': item['show_free_shipping'],
                    'feedback_count': item['cmt_count'],
                    'liked_count': item['liked_count'],
                    'view_count': item['view_count'],
                    'shop_id': item['shopid'],
                    'shop_location': item['shop_location'],
                    'shopee_verified': item['shopee_verified'],
                    'is_official_shop': item['is_official_shop'],
                    'updated_at': item['ctime'],
                    'fetched_time': datetime.timestamp(datetime.utcnow())
                }
            )
    except Exception as e:
        logger.error(e)

    return results

def crawl_by_search(keyword:str, limit:int=60, max_workers:int=32) -> list:

    temp = get_keyword_encoded(keyword=keyword)

    total_count = get_total(temp)
    logger.info(f"There are {total_count} products in \"{keyword}\"")
    futures = []
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for newest in range(0, total_count, limit):
            url = "https://shopee."+site+"/api/v4/search/search_items?by=relevancy&keyword={}&limit={}&newest={}&order=desc&page_type=search&scenario=PAGE_GLOBAL_SEARCH&version=2".format(temp, limit, newest)
            futures.append(executor.submit(get_all_data, url))

    for future in concurrent.futures.as_completed(futures):
        results.extend(future.result())
        
    all_data = get_neccesary_data(results)
    length = len(all_data)
    if length == total_count:
        logger.info(f"Successfully crawl all {total_count} products from \"{keyword}\"")
    elif length < total_count:
        logger.info(f"Successfully crawl {length} products from \"{keyword}\"")

    return all_data



data=crawl_by_search(search)



df=pd.DataFrame(data)
df



driver = webdriver.Chrome(options=opt)
number =1
Break=False
for index, row in df.iterrows():
    link=row['product_link']
    driver.get(link)
    sleep(1)
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        
    curr_position = driver.execute_script("return window.pageYOffset;")
    
    try:
        try:
            shopname = driver.find_element_by_xpath('.//div[@class="_3uf2ae"]').text
        except:
            shopname=""

        df.at[index,'shopname']=shopname

        handle = driver.find_element_by_xpath('.//a[@class="btn btn-light btn--s btn--inline btn-light--link _3IQTrY"]')
        shoplink=handle.get_attribute('href')
        shopdetails = driver.find_elements_by_xpath('.//span[@class="zw2E3N _2fK6RA"]')

        shoprating=shopdetails[0].text
        shoprating
        shopProducts=shopdetails[1].text
        shopProducts
        shopResponseRate=shopdetails[2].text
        shopResponseRate
        shopdetails = driver.find_elements_by_xpath('.//span[@class="zw2E3N"]')
        shopResponseTime=shopdetails[0].text
        shopResponseTime
        shopResponseTime=shopdetails[0].text
        shopJoined=shopdetails[1].text
        shopJoined
        shopFollowers=shopdetails[2].text
        shopFollowers
        try:

            catName = driver.find_elements_by_xpath('.//div[@class="flex items-center _1J-ojb page-product__breadcrumb"]')[0].text
            catName=catName.replace("\n"," > ")
            df.at[index,'catName']=catName
        except:
            pass



        df.at[index,'shoplink']=shoplink
        df.at[index,'shoprating']=shoprating

        df.at[index,'shopProducts']=shopProducts

        df.at[index,'shopResponseRate']=shopResponseRate
        df.at[index,'shopResponseTime']=shopResponseTime

        df.at[index,'shopJoined']=shopJoined
        df.at[index,'shopFollowers']=shopFollowers

        description = driver.find_elements_by_xpath('.//div[@class="_1afiLm"]')[1].text



        df.at[index,'description']=description
    except:
        pass
    if EndCounter == number:
        Break=True
        break
    number+=1



driver.close()



if Break:
    df=df.head(EndCounter)



df.to_csv(Output)

