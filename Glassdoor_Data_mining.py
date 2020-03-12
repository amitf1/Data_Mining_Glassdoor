from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import random
import pandas as pd
import sys
import os
""""
In this program, we scrape Glassdoor site for job offers, using selenium and create a data frame with jobs data.

First each search link is loaded, then we gather all job posts links from the searches. 
After we have all job posts links, on each link we gather the data available.
Finally we create a data frame of positions with info of the role and company.
"""
PATH_OF_CHROME_DRIVER = 'chromedriver_linux64/chromedriver'
JOBS_IN_ISRAEL = 'https://www.glassdoor.com/Job/israel-jobs-SRCH_IL.0,6_IN119.htm'
DATA_SCIENTISTS_NEW_YORK = 'https://www.glassdoor.com/Job/new-york-data-science-jobs-SRCH_IL.0,8_IC1132348_KO9,21.htm'
INITIAL_LINKS = [JOBS_IN_ISRAEL, DATA_SCIENTISTS_NEW_YORK]
START_OF_LOCATION = 3


def set_up_connection():
    """This function creates a connection with chrome and creates a webdriver object"""

    if not os.path.exists(PATH_OF_CHROME_DRIVER):
        return None
    else:
        driver = webdriver.Chrome(executable_path=PATH_OF_CHROME_DRIVER)
        return driver


def gather_job_links(driver, search_link):
    """
    This function get a search link, goes over all the job posts pages and gather the links for each job post
    :param driver: webdriver object
    :param search_link:a link to the first search page
    :return: list of links of all job posts
    """
    driver.get(search_link)
    links = []
    while True:
        job_headers = driver.find_elements_by_class_name('jobHeader')
        for job in job_headers:
            links.append(job.find_element_by_css_selector('a').get_attribute('href'))
        try:
            driver.find_element_by_class_name('next').find_element_by_css_selector('a').click()  # close pop-up
            time.sleep(random.randint(2, 4))
        except NoSuchElementException:
            break
        try:
            driver.find_element_by_id("prefix__icon-close-1").click()
        except NoSuchElementException:
            pass
        print(links)
    print(f'{len(links)} links were gathered')
    return links


def gather_data_from_links(driver, links=None):
    """
    This function goes over all links to job posts and creates a data frame out of the data pulled from each page
    :param driver: webdriver object
    :param links: list of links of job posts
    :return: data frame with data collected from all the links
    """
    if links is None or len(links) < 1:
        print("No links passed to gather_data_from_links")
        sys.exit()
    glassdoor_jobs = pd.DataFrame()
    for i, link in enumerate(links):
        driver.get(link)
        time.sleep(random.randint(2, 4))
        try:
            driver.find_element_by_id("prefix__icon-close-1").click()  # If pop up appears, close it
        except NoSuchElementException:
            pass
        try:
            glassdoor_jobs.loc[i, 'title'] = driver.find_element_by_class_name('mt-0.margBotXs.strong').text
        except NoSuchElementException:  # if page is rejected by glassdoor, reload.
            time.sleep(random.randint(6, 8))
            driver.get(link)
            time.sleep(random.randint(2, 4))
            glassdoor_jobs.loc[i, 'title'] = driver.find_element_by_class_name('mt-0.margBotXs.strong').text

        glassdoor_jobs.loc[i, 'company'] = driver.find_element_by_class_name('strong.ib').text

        try:
            glassdoor_jobs.loc[i, 'location'] = driver.find_element_by_class_name('subtle.ib').text[START_OF_LOCATION:]
        except NoSuchElementException:
            pass
        try:
            glassdoor_jobs.loc[i, 'desc'] = driver.find_element_by_class_name('desc.css-58vpdc.ecgq1xb3').text.replace(
                '\n', ' ')

        except NoSuchElementException:
            pass

        try:
            driver.find_element_by_xpath("//span[@class='link' and text()='Company']").click()
            time.sleep(random.randint(2, 4))
            fields = driver.find_elements_by_xpath("//label[@for='InfoFields']")
            values = driver.find_elements_by_class_name("value")
            for field in zip(fields, values):
                field_name = field[0].text
                field_value = field[1].text
                glassdoor_jobs.loc[i, field_name] = field_value
        except NoSuchElementException:
            pass

        try:
            driver.find_element_by_xpath("//span[@class='link' and text()='Rating']").click()
            time.sleep(random.randint(2, 4))
            glassdoor_jobs.loc[i, 'company_rating'] = float(
                driver.find_element_by_class_name('margRtSm.css-16h0h8a.e1dyssh91').text)
        except NoSuchElementException:
            pass

    return glassdoor_jobs


def main():

    driver = set_up_connection()
    if driver is None:
        print('Add the correct path to the ChromeDriver in your machine')
        return

    job_links = []
    for search_link in INITIAL_LINKS:
        job_links.extend(gather_job_links(driver, search_link))
    glassdoor_jobs = gather_data_from_links(driver, job_links)
    glassdoor_jobs.to_excel("glassdoor_jobs_df1.xlsx")


if __name__ == '__main__':
    main()
