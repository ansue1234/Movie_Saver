import requests
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService 
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

download_cover = True
download_accessories = True

chrome_options = Options()
chrome_options.add_argument("user-agent=Chrome/80.0.3987.132")
chrome_options.add_argument("--window-size=1920,1080")
url = 'https://app.kplanet.vip/m/share/movie-group?groupID=0&fansID=261154&type=703' 
 
driver = webdriver.Chrome(service=ChromeService( 
	ChromeDriverManager().install()), options=chrome_options) 
try:
    driver.get(url) 
except:
    print("faulty URL!")
# print(driver.page_source)
try:
    print("Loading Web Page...")
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="rankMovieCard-content-"]')) #This is a dummy element
        )
    print()
except:
    print('Timed Out')


# getting total number of movies in list
pattern = r'\d+'
movie_num_descriptor = driver.find_element(By.CSS_SELECTOR, 'div[class*="movieGroup-numInfo-"]').text
list_name = driver.find_element(By.CSS_SELECTOR, 'div[class*="movieGroup-name-"]').text
num_movies, num_movies_with_review = re.findall(pattern, movie_num_descriptor)
print("本影单名为：" + list_name)
print('本影单共有：{0}部电影，{1}部电影附有解说'.format(num_movies, num_movies_with_review))
# print(num_movies, num_movies_with_review)
num_movies = int(num_movies)
# getting the movies from the list
# num_movies = 10
movies = []
last_height = driver.execute_script('return document.body.scrollHeight') 
index = 0
while num_movies > len(movies): 
    # Simulate scrolling
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);') 
	# wait for content to load 
    time.sleep(1) 
    new_height = driver.execute_script('return document.body.scrollHeight') 
    if new_height == last_height: 
        break 
    last_height = new_height 

    # adding new unseen elements into the movies list
    elements = driver.find_elements(By.CSS_SELECTOR, 'div[class*="rankMovieCard-content-"]')[index:]
    movie_titles = [element for element in elements] 
    movies.extend(movie_titles) 
    index += len(elements)

# working on movies list
with open('./movies/' + list_name + '.csv', 'w', encoding='utf-8') as file:
    # Write file header
    header = '编号,电影名称,上映时间,制片地区,类型,时长(分钟）\n'
    file.write(header)
    for movie in movies:
        soup = BeautifulSoup(movie.get_attribute('innerHTML'), "html.parser")
        movie_rank = soup.find('div', {'class': re.compile(r'rankMovieCard-rank-')}).text
        movie_name = soup.find('div', {'class': re.compile(r'rankMovieCard-main-')}).text
        metadata, genre = soup.find_all('div', {'class': re.compile(r'rankMovieCard-item-')})
        # Define regular expressions to extract country, date, duration, and genre
        country_pattern = r'([\u4e00-\u9fa5]+)\s+'  # Matches Chinese characters (country)
        date_pattern = r'(\d{4}-\d{2}-\d{2})'  # Matches YYYY-MM-DD format (date)
        duration_pattern = r'(\d+)\s*分钟'  # Matches numbers followed by "分钟" (duration)
        
        movie_metadata = metadata.text
        movie_genre = genre.text
        movie_duration = ''
        movie_prod_loc = ''
        movie_premiere_date = ''

        # Extract information
        duration = re.search(duration_pattern, movie_metadata)
        if duration:
            movie_duration = duration.group(1)
            movie_metadata = re.sub(duration_pattern, '', movie_metadata)
        
        countries = re.findall(country_pattern, movie_metadata)
        date = re.search(date_pattern, movie_metadata)
        if date:
            movie_premiere_date = date.group(1)
        if countries:
            movie_prod_loc = '/'.join(countries)

        # write information to csv file
        file_line = ','.join([movie_rank, movie_name, movie_premiere_date, movie_prod_loc, movie_genre, movie_duration])
        file_line += '\n'
        print(file_line)
        file.write(file_line)


	# print title 
# print(movies, len(movies))
# URL = "https://app.kplanet.vip/m/share/movie-group?groupID=0&fansID=261154&type=701"
# page = requests.get(URL)
# movies = driver.find_elements(By.CLASS_NAME, "rankMovieCard-content-3gOsD_0")
# print(movies)
# soup = BeautifulSoup(driver.page_source, "html.parser")

