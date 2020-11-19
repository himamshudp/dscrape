import bs4
# import requests
# import shutil
import time
import os
#import json
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import re
from selenium import webdriver


def dmart():
    product_list = pd.read_csv(r'dmart_link.csv')
    product_url = product_list['link'].tolist()
    dmart_df = pd.DataFrame(
        columns=['Product_category', 'product_name', 'Product_o_price', 'product_d_price', 'p_brand'])
    product_url_try = product_url[:3]
    # headless chorme
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")

    # options.add_argument('window-size=1200x600') # optional
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

    for url in product_url_try:
        driver.get(url)
        time.sleep(8)  # 2 Sec for ssh
        html = driver.execute_script("return document.documentElement.outerHTML")
        soup = BeautifulSoup(html, 'html.parser')
        # print(soup)
        #print(url)
        pname = soup.findAll("div", {
            "class": "src-client-components-pdp-text-label-component-__text-label-component-module___title-container"})
        dprice = soup.findAll("span", {
            "class": "src-client-components-pdp-price-details-component-__price-details-component-module___sp"})
        mrps = soup.findAll("span", {
            "class": "src-client-components-pdp-price-details-component-__price-details-component-module___value"})
        pbrand = soup.findAll("a", {"class": "src-client-app-product-details-styles-__common-module___brand-link"})
        p_cat = soup.findAll("li", {"class": "MuiBreadcrumbs-li"})
        p_name = []
        d_price = []
        o_price = []
        p_category = []
        p_brand = []

        for ppoints, dpoints, mpoints, cpoints, pb in zip(pname, dprice, mrps, p_cat, pbrand):
            p_name.append(str(ppoints.text))
            d_price.append(str(dpoints.text))
            o_price.append(str(mpoints.text))
            p_category.append(str(cpoints.text))
            p_brand.append(str(pb.text))

        # crete dictionary

        keys = ['Product_category', 'p_brand', 'product_name', 'Product_o_price', 'product_d_price']
        values = [p_category, p_brand, p_name, o_price, d_price]
        dmart = dict(zip(keys, values))
        df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in dmart.items()]))
        result = dmart_df.append(df)
        dmart_df = result
    df_copy = dmart_df
    # remove extra front and back space from all colms
    df_copy = df_copy.select_dtypes(['object'])
    df_copy[df_copy.columns] = df_copy.apply(lambda x: x.astype(str).str.strip())
    # convert all colms to lower case
    df_copy[df_copy.columns] = df_copy.apply(lambda x: x.astype(str).str.lower())
    # replace new line with space
    df_copy = df_copy.replace('\n', '', regex=True)

    # extract product name from the product name

    df_copy['test_Product_name'] = df_copy['product_name'].str.split(' : ').str[0]
    df_copy['test_Product_name'] = df_copy['test_Product_name'].str.split(': ').str[0]
    df_copy['test_Product_name'] = df_copy['test_Product_name'].str.strip()
    df_copy['test_Product_name'] = df_copy['test_Product_name'].str.split(' - ').str[0]
    df_copy['test_Product_name'] = df_copy['test_Product_name'].map(lambda x: re.sub(r'\W+', ' ', x))
    # create weight col from product name col
    df_copy['weight'] = df_copy['product_name'].str.split(': ').str[1]
    df_copy['weight'] = df_copy['product_name'].str.split(' : ').str[1]
    df_copy['weight'] = df_copy['product_name'].str.split(':').str[1]
    #df_copy['app_Weight'] = df_copy['weight'].str.split('').str[1]
    df_copy['app_Weight'] = df_copy['weight'].str.split(' ').str[1]
    df_copy['app_Weight'] = df_copy['app_Weight'].replace({'x': '*'}, regex=True)
    # create scale col from product name col
    df_copy['app_Scale'] = df_copy['weight'].str.split(' ').str[2]
    df_copy["app_organic"] = pd.np.where(df_copy['test_Product_name'].str.contains('organic'), 'organic', 'non_organic')
    df_copy['app_brand'] = df_copy['p_brand']
    df_copy['app_Scale'] = df_copy['app_Scale'].replace({'gms|gm': 'g'}, regex=True)
    df_copy['app_Scale'] = df_copy['app_Scale'].replace(
        {'bags|tea-bags|pcs|pellets|drops|sachets|cubes|unit|pcnit|u': 'pc'}, regex=True)
    df_copy['app_Scale'] = df_copy['app_Scale'].replace({'litres': 'l'}, regex=True)
    df = df_copy
    # Reading the standard ingredient list
    df_col = pd.read_excel("dmart and bb combine data.xlsx", sheet_name='sorted list')
    # lowering the data to maintaing uniformity of dataset
    df_col = df_col.apply(lambda x: x.astype(str).str.lower())
    # connverting data  columns to list for further processing
    prod_name_list_dmart = df["test_Product_name"].tolist()
    sorted_name_list = df_col["sorted name"].tolist()
    product_category_list = df_col["Product_category"].tolist()
    # create app name from product names
    app_name = []
    for j in prod_name_list_dmart:
        list1 = []
        for i in sorted_name_list:
            try:
                if i in j:
                    list1.append(i)
            except:
                list1 = []
        app_name.append(list1)
        # fill [] with null keyword
    index = [i for i, x in enumerate(app_name) if x == []]
    for i in range(len(app_name)):
        for j in index:
            if i == j:
                app_name[i] = 'Null'
    # take max length words from list
    app_name1 = []
    for name in app_name:
        name1 = max((name for name in name if name), key=len)
        app_name1.append(name1)
    df['app_name_dmart'] = app_name1

    app_name_dmart = df["app_name_dmart"].tolist()
    # create app category  from product category and app name
    app_cat = []
    for i in range(len(app_name_dmart)):
        list2 = []
        for j in range(len(sorted_name_list)):
            try:
                if app_name_dmart[i] == sorted_name_list[j]:
                    list2.append(product_category_list[j])
            except:
                list2 = []
        app_cat.append(list2)
        # fill [] with null keyword
    index = [i for i, x in enumerate(app_cat) if x == []]
    for i in range(len(app_cat)):
        for j in index:
            if i == j:
                app_cat[i] = 'Null'
    # take max length words from list
    app_cat1 = []
    for name in app_cat:
        name1 = max((name for name in name if name), key=len)
        app_cat1.append(name1)
    df['app_cat_dmart'] = app_cat1
    df['App_Original_price'] = df.Product_o_price.str.extract('(\d+)')
    df['App_dmart_price'] = df.product_d_price.str.extract('(\d+)')
    df['app_Weight'] = df.app_Weight.str.extract('(\d+)')
    df1 = df[['app_cat_dmart', 'app_brand', 'app_name_dmart', 'app_organic', 'App_Original_price', 'App_dmart_price',
              'app_Weight', 'app_Scale']]
    df1.to_csv(r'Dmart_3.csv', index=False)
    #print("Dmart_3 created please check")
