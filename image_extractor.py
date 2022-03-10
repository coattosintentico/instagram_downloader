#!/usr/bin/env python3

# Runs a selenium web driver, and gets input to start extracting
# images from an instagram profile to a specific folder.

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
# To handle the exception for not finding some element:
from selenium.common.exceptions import NoSuchElementException
import os, wget # to download the images from their source links
from time import sleep

def login(driver):
	# Start instagram
	driver.get('http://www.instagram.com')

	# Prompt for cookies: click on 'Accept all'
	accept_all_cookies = WebDriverWait(driver, 10).until(
		EC.element_to_be_clickable(
			(By.XPATH, "//button[contains(text(), 'Only allow essential cookies')]"))
		)
	accept_all_cookies.click()
	# locates it by xpath: finds a tag that contains specific text

	# Target username and password fields
	username = WebDriverWait(driver, 10).until(
		EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']"))
		)
	password = WebDriverWait(driver, 10).until(
		EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']"))
		)

	# Wait until the cookies prompt has disappeared. This can be long sometimes,
	# so it's better to establish a waiting time relative to its disappearing
	WebDriverWait(driver, 20).until(
		EC.invisibility_of_element(accept_all_cookies)
		)
	# Enter username and password
	# sleep(5)
	username.clear()
	username.send_keys("luislurker")
	sleep(1)
	password.clear()
	password.send_keys("nothingtodo")

	# Target the login button and click it
	sleep(2)
	sign_in = WebDriverWait(driver, 10).until(
		EC.element_to_be_clickable(
			(By.CSS_SELECTOR, "button[type='submit']"))
		).click()

	# Note: the sleep's are needed to avoid that other div obscures the login button.
	# I think that if instagram sees that typing is too fast, it blocks the user

def handle_alerts(driver):
	'''
	Handles the 2 alerts that are displayed by instagram (save login info and
	show notifications). The webdriverwait method assures that if the 2nd
	notification is not displayed after some time the programs continues to run
	smoothly. (TODO: I would have to add a try: except: clause with the timeout
	error handled properly)
	'''
	sleep(5)
	alert = WebDriverWait(driver, 15).until(
		EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Not Now")]'))
		).click()
	alert_2nd = WebDriverWait(driver, 15).until(
		EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Not Now")]'))
		).click()

def search_user(driver):
	'''
	Searchs for a user and clicks in its profile from the instagram main page. 
	'''

	sleep(2)
	# Target the search input field
	searchbox = WebDriverWait(driver, 10).until(
		EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Search']")))
	searchbox.clear()

	# Search for the user
	searchbox.send_keys(user_to_search)

	sleep(2)
	user_link = WebDriverWait(driver, 10).until(
		EC.element_to_be_clickable((By.XPATH, "//a[@href='/{}/']".format(user_to_search)))
		).click()

def get_publication_links(driver):
	'''
	Searchs for publication links from within an instagram profile page. Returns
	a list with all the publication links.
	'''
	sleep(2)
	# Get all links from the profile page. We don't know yet if they are publications or not
	links_in_profile_page = driver.find_elements(By.TAG_NAME, 'a')
	print('Found {:d} links in the profile page.'.format(len(links_in_profile_page)))
	# Filter them to get only the publications
	publications = [p for p in links_in_profile_page
		if p.get_attribute('href').startswith('https://www.instagram.com/p/')]
	print('{:d} of them are publications.'.format(len(publications)))
	publication_links = [a.get_attribute('href') for a in publications]
	return publication_links

def get_files_from_publication(driver, link):
	# First get the current focus, to return to it afterwards
	original_window = driver.current_window_handle
	# Open a new empty tab and focus there
	driver.switch_to.new_window('tab')
	# Go to the publication
	driver.get(link)
	
	# Get images displayed in the page
	# (TODO: maybe add wait clause to wait till they're finished loading?)
	images = driver.find_elements(By.XPATH,
		"//img[starts-with(@alt, 'Photo by')]")
	# and extract their src links to later download them
	source_links = [image.get_attribute('src') for image in images]
	# Assume that it's a multiple post and try to search for more images
	there_are_more_images = True
	while there_are_more_images:
		# Wait one second
		sleep(1)
		try:
			# Click on the "next image" button
			next_image_button = driver.find_element(By.XPATH,
				"//button[contains(concat(' ',normalize-space(@class),' '),' _6CZji ')]"
				).click()
			# Get images again
			new_images = driver.find_elements(By.XPATH,
				"//img[contains(@class, 'FFVAD')]")
			# and the new src attributes
			new_source_links = [new_image.get_attribute('src') 
				for new_image in new_images]
			# Finally, update the source links list to add the ones that were 
			# not in the list
			source_links += [link for link in new_source_links 
				if link not in source_links]
		except NoSuchElementException:
			# If there are no more images in the publication, the button
			# goes missing. This handles the exception to stop the searching.
			print('Found {:d} images at this publication.'.format(len(source_links)))
			there_are_more_images = False

	# Create folder for the user's files if not existent
	cwd = os.getcwd()
	user_folder = os.path.join(cwd, user_to_search)
	os.makedirs(user_folder, exist_ok = True)

	# Declare that we are going to use the global variable "image_number",
	# because we are going to modify it later
	global image_number
	# and cycle through the links downloading them and saving them in the folder created
	for source_link in source_links:
		path = os.path.join(user_folder, '{}{:03d}.jpg'.format(
			user_to_search, image_number)
		)
		wget.download(source_link, path)
		image_number += 1
	# TODO: add publication number??
	print('Images downloaded succesfully from publication ###')

	# Close current tab
	driver.close()
	# And ensures we are focusing the original tab:
	driver.switch_to.window(original_window)

def main():
	# Initialize the driver
	driver = webdriver.Firefox()
	# Login into our account
	login(driver)
	# Click on the "Not Now" for saving login info, and the "Not Now" for notifications
	handle_alerts(driver)
	# Declare the user to extract information from
	global user_to_search
	user_to_search = 'mabelolea_'
	# and search for it, going to its profile page
	search_user(driver)
	# TODO: check if account is private
	# Get the publication links from its profile page
	publication_links = get_publication_links(driver)
	global image_number
	image_number = 1
	for link in publication_links:
		# TODO: download files as the machine views the images
		get_files_from_publication(driver, link)
		sleep(2.5)	

if __name__ == '__main__':
	main()
