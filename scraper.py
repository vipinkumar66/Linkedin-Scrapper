from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime
from getpass import getpass
import json
import time
import csv
import re

#trying to open custom config on exception using default config
try:
    with open("./config.json", "r") as file:
        config = json.loads(file.read())
except FileNotFoundError:
    config = {
        "pages": 2,
        "maximum_profiles": 100,
        "maximum_expereince": 3,
        "ignore": "/people/headless",
        "location": "United Kingdom",
        "uri": "https://www.linkedin.com/login",
        "driver_path": "C:/Program Files (x86)/Google/Chrome/Application/chromedriver.exe"
    }

fetch_time = datetime.now().strftime('%d_%m_%Y_%H_%M')

#Taking the user input for username and password (hiding password using the get pass)
username = input("Please provide your linkedin username : ")
password = getpass("Please provide your linkedin password : ")

#initializing chrome web driver
web_driver = webdriver.Chrome(ChromeDriverManager().install())
web_driver.get(config["uri"])

#logging into linkedin with the credentials provided
username_field = web_driver.find_element("id", "username")
username_field.send_keys(username)
password_field = web_driver.find_element("id", "password")
password_field.send_keys(password)
password_field.submit()

page = 1
shortlisted_profiles = []

#creating a csv file to add the scraped profiles
with open(f"./linkedin_profiles_{fetch_time}.csv", "w") as csv_file:
    profile_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    profile_writer.writerow(["Username", "Title", "Profile link", "Approx. years of experience"])
    
    #using while loop to loop through profiles untill we reach the 100th profile
    while len(shortlisted_profiles) < config["maximum_profiles"]:
        web_driver.get(f"https://www.linkedin.com/search/results/people/?geoUrn=%5B%22101165590%22%5D&keywords=UK&origin=FACETED_SEARCH&page={page}&sid=EUy")
        source = web_driver.page_source
        page += 1

        #with the help of beautifulsoup getting the links of the profiles 
        soup = BeautifulSoup(source, "html.parser")
        results = soup.find_all("li", class_="reusable-search__result-container")
        for result in results:
            profile_link = result.find("a", class_="app-aware-link")["href"]
            
            if config["ignore"] in profile_link:
                continue
            
            #Getting the profile page 
            web_driver.get(profile_link)
            time.sleep(2)
            profile_source = web_driver.page_source
            
            #Getting the experience and location from the profile
            soup = BeautifulSoup(profile_source, "html.parser")
            profile_experience = soup.find("div", id="experience")
            location_span = soup.find("span", class_="text-body-small inline t-black--light break-words")
            
            #if location of the profile didn't matched the given location going to next one
            if (not location_span) and (config["location"] not in location_span.text):
                continue
            
            if profile_experience:
                profile_experience = profile_experience.find_parent("section")
                experiences_list = profile_experience.find("ul", "pvs-list")
                if experiences_list:
                    expereinces = experiences_list.find_all("li", class_="artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column")
                    if expereinces:
                        
                        years_of_expereince = []
                        for id, experience in enumerate(expereinces):
                            found_details = experience.find_all("span", class_="visually-hidden", recursive=True)
                            
                            try:
                                found_details_str = "".join([str(ele) for ele in found_details])
                                if config["location"] in found_details_str:
                                    years = sorted(set(re.findall(r"[1-3][0-9]{3}", found_details_str)))
                                    years_of_expereince += years
                                    years_of_expereince = sorted(set(years_of_expereince))
                            except IndexError:
                                continue
                            
                        #Getting the details of the profile whose experience is less than 3 years
                        if len(years_of_expereince) < 3:
                            
                            profile_username = soup.find("h1", class_="text-heading-xlarge inline t-24 v-align-middle break-words")
                            
                            if profile_username:
                                profile_username = profile_username.text
                            profile_current_title = soup.find("div", class_="text-body-medium break-words")

                            #Adding the profiles which we scarped to the csv file we created
                            if profile_current_title:
                                profile_current_title = profile_current_title.text
                            try:    
                                profile_writer.writerow([
                                    profile_username,
                                    profile_current_title.strip(),
                                    profile_link,
                                    len(years_of_expereince),
                                ])
                                shortlisted_profiles.append(profile_link)
                            except UnicodeEncodeError:
                                continue