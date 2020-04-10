from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import pandas as pd
import os
from datetime import datetime
import config as CFG
from collections import defaultdict
import click
import requests


""""
In this program, we scrape Glassdoor site for job offers, using selenium and create a data frame with jobs data.

First each search link is loaded, then we gather all job posts links from the searches. 
After we have all job posts links, on each link we gather the data available.
Finally we create a data frame of positions with info of the role and company.
"""


class GDScraper:
    """
    Class for scraping glassdoor job posts out of search links
    Attributes:
        path: path to chrome driver
        search_links: Glassdoor search links for different job searches
        job_links: links to job posts collected from search links
    """

    def __init__(self, path, search_links=None):
        """
        This function initializes a GDScraper object with search links and creates
         a webdriver object to establish a connection to chrome.
        """
        if not os.path.exists(path):
            raise FileNotFoundError("'ChromeDriver' executable needs to be in path."
                                    "Please see https://sites.google.com/a/chromium.org/chromedriver/home")
        self._driver = webdriver.Chrome(executable_path=path)
        self.search_links = search_links
        self.job_links = []

    def _close_popup(self):
        """This function closes pop-ups in search links, in they appear"""
        try:
            self._driver.find_element_by_id("prefix__icon-close-1").click()
        except NoSuchElementException:
            CFG.logger.info("No pop-up")

    def gather_job_links(self, limit_page_per_search=None):
        """
        This function go over the instance's search links, for each search
         gathers all the links of job posts and returns them
        :limit_page_per_search: limit of pages to search per search link
        :return: list of links of all job posts
        """
        links = []
        for search_link in self.search_links:
            self._driver.get(search_link)
            i = 0
            while True:
                job_headers = self._driver.find_elements_by_class_name('jobHeader')
                for job in job_headers:
                    links.append(job.find_element_by_css_selector('a').get_attribute('href'))
                i += 1
                print(f'Page {i} of {search_link} is done')
                if limit_page_per_search is not None and i == limit_page_per_search:
                    break
                try:
                    WebDriverWait(self._driver, 20).until(EC.element_to_be_clickable((By.XPATH,
                                                                                      "//li[@class='next']/a"))).click()
                    time.sleep(random.randint(2, 4))
                except NoSuchElementException:
                    CFG.logger.warning("Next page couldn't be clicked, last page assumed")
                self._close_popup()
        CFG.logger.info(f'Total of {len(links)} links were gathered')
        self.job_links = links
        return links

    def gather_data_from_links(self, limit=None):
        """
        This function goes over all object's job links and creates a data frame out of the data pulled from each page
        :return: data frame with data collected from all the links
        """
        if self.job_links is None or len(self.job_links) < 1:
            CFG.logger.warning("No links passed to gather_data_from_links")
            return []
        glassdoor_jobs = pd.DataFrame(columns=['Job_ID', 'Title', 'Company', 'Location', 'Desc', 'Headquarters',
                                               'Size', 'Type', 'Revenue', 'Industry', 'Sector',
                                               'Company_Rating', 'Founded', 'Competitors', 'Scrape_Date'])

        if limit is not None:
            job_links = self.job_links[:limit]
        else:
            job_links = self.job_links
        num_of_links = len(job_links)
        for i, link in enumerate(job_links):
            CFG.logger.info(f'link {i + 1} out of {num_of_links}, {num_of_links - i - 1} left')
            job_post = JobPost(self._driver, link)
            job_post.go_to_page()
            time.sleep(random.randint(2, 4))
            self._close_popup()
            glassdoor_jobs.loc[i, 'Scrape_Date'] = datetime.now()
            glassdoor_jobs.loc[i, ['Job_ID', 'Title', 'Company', 'Location', 'Desc']] = job_post.get_main_tab()
            for col, val in job_post.get_company_tab().items():
                glassdoor_jobs.loc[i, col] = val
            glassdoor_jobs.loc[i, 'Company_Rating'] = job_post.get_rating()
        glassdoor_jobs['Country'] = glassdoor_jobs['Location'].apply(find_country)
        glassdoor_jobs['HQ Country'] = glassdoor_jobs['Headquarters'].apply(find_country)
        return glassdoor_jobs


class JobPost:
    """
    Class for holding a job post and getting it's information
    Attributes:
        driver:  webdriver object
        job_link: links to job posts collected from search links
    """

    def __init__(self, driver, job_link):
        """Initialize a JobPost object with webdriver and link"""
        self.job_link = job_link
        self._driver = driver

    def go_to_page(self):
        """
        This function opens up the page of the link in the driver of the object
        """
        self._driver.get(self.job_link)

    def get_main_tab(self):
        """
        This function goes to the main tab of a job post links and returns title, company, location, desc
        :return: tuple with title, company, location, desc
        """
        jid = self._get_job_id()
        title = self._get_title()
        company = self._get_company()
        location = self._get_location()
        desc = self._get_desc()
        CFG.logger.debug("Main tab fetched")
        return jid, title, company, location, desc

    def _get_title(self):
        """
        This method gets the title of the JobPost within the main tab.
        :return: title of the job
        """
        title = None
        collected = False
        i = 0
        while not collected and i < CFG.RELOAD_TRIALS:
            try:
                title = self._driver.find_element_by_class_name('mt-0.mb-xsm.strong').text
                collected = True
            except NoSuchElementException:
                CFG.logger.warning(f'Title not collected on {i} trial')
                time.sleep(random.randint(6, 8))
                self.go_to_page()
                time.sleep(random.randint(2, 4))
            i += 1
        return title

    def _get_job_id(self):
        """
        This method gets the id of the JobPost from the main tab.
        :return: id of the job
        """
        jid = None
        collected = False
        i = 0
        while not collected and i < CFG.RELOAD_TRIALS:
            try:
                jid = self._driver.find_element_by_xpath("//div[@id='JobView']/div[@class='jobViewNodeContainer']"
                                                         ).get_attribute('id').split('_')[1]
                collected = True
            except NoSuchElementException:
                CFG.logger.warning(f'ID not collected on {i} trial')
                time.sleep(random.randint(6, 8))
                self.go_to_page()
                time.sleep(random.randint(2, 4))
            i += 1
        return jid

    def _get_company(self):
        """
        This method gets the company of the JobPost within main tab.
        :return: hiring company
        """
        try:
            company = self._driver.find_element_by_class_name('strong.ib').text
        except NoSuchElementException:
            company = None
            CFG.logger.warning("Company was not collected")
        return company

    def _get_location(self):
        """
        This method gets the location of the JobPost within main tab.
        :return: job location
        """
        try:
            location = self._driver.find_element_by_class_name('subtle.ib').text[CFG.START_OF_LOCATION:]
        except NoSuchElementException:
            location = None
            CFG.logger.warning("Location was not collected")
        return location

    def _get_desc(self):
        """
        This method gets the description of the JobPost within main tab.
        :return: job description
        """
        try:
            desc = self._driver.find_element_by_class_name('desc.css-58vpdc.ecgq1xb3').text.replace('\n', ' ')
        except NoSuchElementException:
            desc = None
            CFG.logger.warning("Description was not collected")
        return desc

    def get_company_tab(self):
        """
        This method navigates to company tab and fetches information available
        :return: dictionary with al fields available in the company tab
        """
        # Headquarters, Size, Type, Revenue, Industry, Sector, Founded, Competitors
        data = defaultdict()
        try:
            self._driver.find_element_by_xpath("//span[@class='link' and text()='Company']").click()
            time.sleep(random.randint(2, 4))
            fields = self._driver.find_elements_by_xpath("//label[@for='InfoFields']")
            values = self._driver.find_elements_by_class_name("value")
            for field in zip(fields, values):
                field_name = field[0].text
                field_value = field[1].text
                data[field_name] = field_value
        except NoSuchElementException:
            CFG.logger.info('Partial data collected from company tab')
        CFG.logger.debug("Company tab fetched")
        return data

    def get_rating(self):
        """
        This method navigates to rating tab and gets the rating of the company
        :return: the rating of the company
        """
        try:
            self._driver.find_element_by_xpath("//span[@class='link' and text()='Rating']").click()
            time.sleep(random.randint(2, 4))
            rating = float(
                self._driver.find_element_by_class_name('mr-sm.css-16h0h8a.e1dyssh91').text)
        except NoSuchElementException:
            rating = None
            CFG.logger.warning("Rating was not found on page, and not collected")
        CFG.logger.debug("Rating tab fetched")
        return rating


def find_country(location):
    """
    This function finds the country of the location using an API
    :param location: the location to find it's countery
    :return: The country of the given location if found, None otherwise
    """
    response = requests.request("GET", CFG.API_URL, headers=CFG.HEADERS, params={'location': location})
    if len(eval(response.text)['Results']) == 0 and len(location) > 2:
        response = requests.request("GET", CFG.API_URL, headers=CFG.HEADERS, params={'location': location[:-2]})
        if len(eval(response.text)['Results']) == 0:
            if len(location.split(',')) > 1:
                country = location.split(',')[-1].strip()
            else:
                country = None
        else:
            # country = eval(response.text)['Results'][0]['c']
            country = eval(response.text)['Results'][0]['name'].split(',')[-1].strip()

    else:
        # country = eval(response.text)['Results'][0]['c']
        country = eval(response.text)['Results'][0]['name'].split(',')[-1].strip()
    print(country)
    return country


@click.command()
@click.option('--limit_search_pages', type=click.IntRange(1, 30), default=None,
              help='limit the number of pages in the search to gather job posts from 1-30')
@click.option('--limit_job_posts', default=None, type=click.IntRange(1, 1000),
              help='limit the number of job posts to gather data from 1-1000')
@click.option('--IL', 'search_option', flag_value=0, help='searches to gather job posts IL - Israel')
@click.option('--DSUS', 'search_option', flag_value=1, help='searches to gather job posts DSUS - DATA_SCIENTISTS_USA')
@click.option('--UK', 'search_option', flag_value=2, help='searches to gather job posts UK - United Kingdom')
@click.option('--ALL', 'search_option', flag_value=3, default=3, help='searches to gather job posts: Israel,'
                                                                      'Data Scientists USA, UK')
def scrape_glassdoor(limit_search_pages, limit_job_posts, search_option):
    """
    Scraping Glassdoor site for job offers, and create a data frame with jobs data.
    Using search links chosen, and up to a limit of pages in the search links and a limit of total job offers.
    :param limit_search_pages: limit the number of pages in the search to gather job posts from
    :param limit_job_posts: limit the number of job posts to gather data from
    :param search_option: searches to gather job posts from, few options provided
    """
    print(limit_search_pages, limit_job_posts, search_option)
    if search_option == 3:
        search_links = CFG.INITIAL_LINKS
    else:
        search_links = [CFG.INITIAL_LINKS[search_option]]
    gd_scraper = GDScraper(CFG.PATH_OF_CHROME_DRIVER, search_links)
    gd_scraper.gather_job_links(limit_search_pages)
    glassdoor_jobs = gd_scraper.gather_data_from_links(limit_job_posts)
    glassdoor_jobs.to_csv(f"glassdoor_jobs{datetime.now()}.csv")


def main():
    CFG.logger.info(f'Started at {datetime.now()}')
    scrape_glassdoor()
    CFG.logger.info(f'Ended at {datetime.now()}')


if __name__ == '__main__':
    main()
