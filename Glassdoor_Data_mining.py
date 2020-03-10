from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import random
import pandas as pd
import sys

""""
In this program, we scrape Glassdoor site for job offers, using selenium.
We create a data frame of positions with info of the role and company
"""
PATH_OF_CHROME_DRIVER = 'chromedriver_linux64/chromedriver'


def set_up_connection():
    """This function creates a connection with chrome and creates a webdriver object"""
    driver = webdriver.Chrome(executable_path=PATH_OF_CHROME_DRIVER)  # TODO add check if path is not right
    return driver


def gather_job_links(driver, search_link):
    """
    This function get a search link, goes over all the job posts pages and gather the links for each job post
    :param driver: webdriver object
    :param search_link:a link to the first search page
    :return: list of links of all job posts
    """
    driver.get(search_link)  # TODO add check if link is not right
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
    print(f'{len(links)} links were gathered')
    return links


def gather_data_from_links(driver, links=[]):
    """
    This function goes over all links to job posts and creates a data frame out of the data pulled from each page
    :param driver: webdriver object
    :param links: list of links of job posts
    :return: data frame with data collected from all the links
    """
    if len(links) < 1:  # TODO test this scenario
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
            glassdoor_jobs.loc[i, 'title'] = driver.find_element_by_class_name(
                'mt-0.margBotXs.strong').text  # TODO ?put classes in constants?
        except NoSuchElementException:  # if page is rejected by glassdoor, reload.
            driver.get(link)
            glassdoor_jobs.loc[i, 'title'] = driver.find_element_by_class_name('mt-0.margBotXs.strong').text
        glassdoor_jobs.loc[i, 'company'] = driver.find_element_by_class_name('strong.ib').text
        glassdoor_jobs.loc[i, 'location'] = driver.find_element_by_class_name('subtle.ib').text[3:]
        glassdoor_jobs.loc[i, 'desc'] = driver.find_element_by_class_name('desc.css-58vpdc.ecgq1xb3').text.replace('\n',
                                                                                                                   ' ')
        try:
            driver.find_element_by_xpath("//span[@class='link' and text()='Company']").click()
            time.sleep(random.randint(2, 4))
            fields = driver.find_elements_by_xpath("//label[@for='InfoFields']")
            values = driver.find_elements_by_class_name("value")
            for field in zip(fields, values):
                field_name = field[0].text
                if field_name == 'Competitors':
                    field_value = ','.join(field[1].text.split(','))
                else:
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
    # TODO add several links and loop over them
    links = gather_job_links(driver, "https://www.glassdoor.com/Job/israel-jobs-SRCH_IL.0,6_IN119.htm")
    glassdoor_jobs = gather_data_from_links(driver, links)
    glassdoor_jobs.to_excel("glassdoor_jobs_df1.xlsx")


if __name__ == '__main__':
    main()

