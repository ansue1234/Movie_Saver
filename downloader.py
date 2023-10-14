import requests
import time
import re
import os
import yaml

from bs4 import BeautifulSoup
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService 
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Simulates the scrolling behavior
def scroll(driver):
    # Simulate scrolling
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);') 
    # wait for content to load 
    time.sleep(1) 
    new_height = driver.execute_script('return document.body.scrollHeight') 
    return driver, new_height
    

# gets the movie list with newest movie elements of the visible screen
def get_movie_list(driver, url, first_time=True, current_movie_num=0):
    list_name = ''
    num_movies = -1
    if first_time:
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
        descriptors = re.findall(pattern, movie_num_descriptor)
        num_movies, num_movies_with_review = descriptors[0], descriptors[-1]
        print("本影单名为：" + list_name)
        print('本影单共有：{0}部电影，{1}部电影附有解说'.format(num_movies, num_movies_with_review))
        print()
        
        # calculating total time it will take 
        num_movies = int(num_movies)
        num_movies_with_review = int(num_movies_with_review)
        total_secs = (num_movies - num_movies_with_review)*3.0 + num_movies_with_review*40
        total_hours = total_secs//3600
        remainder_mins = (total_secs % 3600) // 60
        remainder_secs = (total_secs % 3600) % 60
        print('***预计用时{0}小时{1}分钟{2}秒, 总共{3}秒***\n'.format(total_hours, remainder_mins, remainder_secs, total_secs))

    try:
        # adding new unseen elements into the movies list
        elements = driver.find_elements(By.CSS_SELECTOR, 'div[class*="rankMovieCard-content-"]')[current_movie_num:]
        movies= [element for element in elements] 
        # movies.extend(movie_titles) 
        # index += len(elements)
        current_movie_num += len(movies)
        return movies, current_movie_num, list_name, num_movies
    except:
        print('No movie in list')
        return None, current_movie_num, list_name, num_movies

def get_movie_general_data(movie):
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
    return movie_rank, movie_name, movie_premiere_date, movie_prod_loc, movie_genre, movie_duration

def get_cover_photo(movie, path, movie_name):
    soup = BeautifulSoup(movie.get_attribute("innerHTML"), "html.parser")
    cover_src = soup.find('img', {'class': re.compile(r'rankMovieCard-pic-')})['src']
    r = requests.get(cover_src, stream = True) 
    new_path = path + '/'+ movie_name
    # making directory for movie
    if not os.path.exists(new_path):
        os.makedirs(new_path)
        print('Creating directory for info associated with movie.')
        
    # making directory for images
    new_path += '/images'
    if not os.path.exists(new_path):
        os.makedirs(new_path)
        print('Creating directory for images associated with movie.')

    with open(new_path + '/海报.jpeg',"wb") as img: 
        print("Saving cover image...")
        for chunk in r.iter_content(chunk_size=1024): 
            # writing one chunk at a time to pdf file 
            if chunk: 
                img.write(chunk) 
        print("Cover image saved!")

# Get movie comments, dirctors, award won, background pics
def get_movie_accessories(driver, movie_name, path):
    try:
            # driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            # elem = WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div[class*="'+class_name+'"]')))
        class_name = "kstarOriginal-movieName-"
        elem = WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div[class*="'+class_name+'"]')))
        js_code = "arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'center'});"
        driver.execute_script(js_code, elem)
        elem.click()
    except Exception as error:
        print(error, ' Unable to click button to get accessories for ' + movie_name)

    driver.maximize_window()
    time.sleep(1)
    try:
        print("Loading Movie Info Page for " + movie_name)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'div[class*="movieDetail-content-"]'))
            )
        time.sleep(2)
        # print("Details Page Loaded for "  + movie_name)
    except Exception as error:
        print(error, ' Unable to load info page on ' + movie_name)
    
    # making directory for movie
    new_path = path + '/'+ movie_name
    if not os.path.exists(new_path):
        os.makedirs(new_path)
        print('Creating directory for info associated with movie.')
    
    if download_accessories:
        # making directory for images
        img_path = new_path + '/images'
        if not os.path.exists(img_path):
            os.makedirs(img_path)
            print('Creating directory for images associated with movie.')

    # getting info for movie details page
    movie_summary = ''
    movie_awards = []
    movie_creators = {}
    movie_comments = []
    movie_stills = []
    movie_calendar_pics = []

    # get summary
    try:
        print("Getting summary")
        summary = driver.find_element(By.CSS_SELECTOR, 'div[class*="movieDetail-summary-"]')
        summary_text  = summary.find_element(By.CSS_SELECTOR,'div[class*="movieDetail-text-"]').text
        if summary_text:
            movie_summary = summary_text
    except Exception as error:
        print(error, 'Not able to get summary!')
    
    # get awards
    try:
        print("Getting awards")
        awards_wrapper = driver.find_element(By.CSS_SELECTOR, 'div[class*="movieDetail-awardWrapper-"]')
        awards = awards_wrapper.find_elements(By.CSS_SELECTOR,'span[class*="movieDetail-text-"]')
        if awards:
            for award in awards:
                movie_awards += [award.text]
    except Exception as error:
        print(error, 'Not able to get awards!')
    
    # get comments
    try:
        print("Getting comments")
        comments_wrapper = driver.find_element(By.CSS_SELECTOR, 'div[class*="movieDetail-commentWrapper-"]')
        comments = comments_wrapper.find_elements(By.CSS_SELECTOR,'li[class*="commentItem-commentSection-"]')
        if comments:
            for comment in comments:
                comment_soup = BeautifulSoup(comment.get_attribute("innerHTML"), "html.parser")
                comment_header = comment_soup.find('div', {'class': re.compile(r'commentItem-nickNameTime-')}).get_text().strip()
                comment_content = comment_soup.find('div', {'class': re.compile(r'commentItem-commentText-')}).get_text().strip()
                comment_info = comment_header.split()
                commenter = comment_info[0]
                comment_time_nickname = "("+ ' '.join(comment_info[1:]) +")"
                line = "**" + commenter + "**" + " *"+ comment_time_nickname +"*:\n\n" + comment_content.strip() + '\n\n'
                movie_comments += [line]
    except Exception as error:
        print(error, 'Not able to get comments!')
    # get creators
    try:
        print("Getting creators")
        creators_wrapper = driver.find_element(By.CSS_SELECTOR, 'div[class*="movieDetail-actorWrapper-"]')
        creators = creators_wrapper.find_elements(By.CSS_SELECTOR,'li[class*="movieDetail-item-"]')
        if creators:
            for creator in creators:
                creator_soup = BeautifulSoup(creator.get_attribute("innerHTML"), "html.parser")
                creator_info = creator_soup.find_all('div', {'class': re.compile(r'movieDetail-text-')})
                creator_position, creator_name = creator_info[0].get_text().strip(), creator_info[1].get_text().strip()
                # print(creator_position, creator_name)
                if creator_position not in movie_creators.keys():
                    movie_creators[creator_position] = []
                movie_creators[creator_position].append(creator_name)
    except Exception as error:
        print(error, 'Not able to get creators!')

    if download_accessories:
        # getting stills
        try:
            print("Getting stills")
            stills_wrapper = driver.find_element(By.CSS_SELECTOR, 'div[class*="movieDetail-stillWrapper-"]')
            stills_soup = BeautifulSoup(stills_wrapper.get_attribute("innerHTML"), "html.parser")
            stills = stills_soup.find_all('img', {'class': re.compile(r'movieDetail-still-')})
            for still in stills:
                movie_stills += [still['src']]
        except Exception as error:
            print(error, 'Not able to get stills!')

        # get calendar backgrounds (1st movie detail relative wrapper)
        try:
            print("Getting calendar background ...")
            calendars_wrapper = driver.find_element(By.CSS_SELECTOR, 'div[class*="movieDetail-relativeWrapper-"]')
            calendars_soup = BeautifulSoup(calendars_wrapper.get_attribute("innerHTML"), "html.parser")
            calendars = calendars_soup.find_all('img', {'class': re.compile(r'movieDetail-calendar-')})
            for calendar in calendars:
                movie_calendar_pics += [calendar['src']]
        except Exception as error:
            print(error, 'Not able to get calendar!')
    
    # writing info for movie details page
    with open(new_path + '/' + movie_name +'.md', 'w', encoding='utf-8') as file:
        file.write('# ' + movie_name +"\n")
        file.write('## 电影简介\n')
        file.write(movie_summary + '\n')

        file.write("## 主创\n")
        for k in movie_creators.keys():
            file.write("\n**" + k + "**\n")
            for creator in movie_creators[k]:
                file.write("- " + creator + "\n")
        
        file.write("## 奖项\n")
        file.write(' ,'.join(movie_awards) + '\n')
        
        file.write("## 评论\n")
        for c in movie_comments:
            file.write(c)
    
    if download_accessories:
        # Downloading stills
        for i in range(len(movie_stills)):
            with open(img_path + '/剧照{0}.jpeg'.format(i + 1),"wb") as img: 
                print("Saving stills {0} ...".format(i + 1))
                r = requests.get(movie_stills[i], stream = True)
                for chunk in r.iter_content(chunk_size=1024): 
                    # writing one chunk at a time to jpeg file 
                    if chunk: 
                        img.write(chunk) 

        # Saving calendar backgrounds
        for j in range(len(movie_calendar_pics)):
            with open(img_path + '/日历背景{0}.jpeg'.format(j + 1),"wb") as img: 
                print("Saving calendar bg {0}...".format(j + 1))
                r = requests.get(movie_calendar_pics[j], stream = True)
                for chunk in r.iter_content(chunk_size=1024): 
                    # writing one chunk at a time to jpeg file 
                    if chunk: 
                        img.write(chunk) 
        print("All Accessories saved for " + movie_name + "!")
    driver.back()

# Get movie foriegn name, review url
def get_movie_details(movie, movie_name, path, driver):
    movie_foriegn_name, movie_review_title, movie_review_url, movie_summary = '', '', '', ''
    # Check whether more details of movie is available
    soup = BeautifulSoup(movie.get_attribute('outerHTML'), "html.parser")
    more_details = soup.find('div', {'class': re.compile(r'rankMovieCard-original-')})
    if more_details:
        class_name = more_details['class'][0]

        try:
            elem = movie.find_element(By.CSS_SELECTOR,'div[class*="'+class_name+'"]')
            js_code = "arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'center'});"
            driver.execute_script(js_code, elem)
            elem.click()
            time.sleep(1)
        except Exception as error:
            print(error, ' Unable to click button to get more info on ' + movie_name)
            return None, movie_foriegn_name, movie_review_title, movie_review_url, movie_summary 
        
        try:
            print("Loading Movie Review Page for " + movie_name)
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, 'player-container-id_html5_api'))
                )
            driver.set_window_size(200, 660)
            time.sleep(1)
            # print("Review Page Loaded for "  + movie_name)
        except Exception as error:
            print(error, ' Unable to load details page on ' + movie_name)
            return None, movie_foriegn_name, movie_review_title, movie_review_url, movie_summary 
        
        # getting the movie review URL, review title and foriegn name
        try:
            review_url = driver.find_element(By.ID, 'player-container-id_html5_api').get_attribute('src')
            if review_url:
                movie_review_url = review_url
            else:
                print("Review URL not found!")
        except:
            print('No review url found')

        try:
            foriegn_name = driver.find_element(By.CSS_SELECTOR, 'div[class*="kstarOriginal-foreignName-"]')
            movie_foriegn_name = foriegn_name.get_attribute('innerHTML')
        except:
            print("No Foriegn Name")
        try:
            summary = driver.find_element(By.CSS_SELECTOR, 'div[class*="kstarOriginal-summary-"]')
            summary_soup = BeautifulSoup(summary.get_attribute('innerHTML'), 'html.parser')
            summary_text = summary_soup.find('div', class_='one-line-ellipsis').text.strip('\n')
            if summary_text:
                movie_summary = summary_text
        except:
            print('No Summary found')

        # if review_title:
        #     movie_review_title = review_title
        try:
            abstract = driver.find_element(By.CSS_SELECTOR, 'div[class*="kstarOriginal-abstract-"]')
            abstract_soup = BeautifulSoup(abstract.get_attribute('innerHTML'), 'html.parser')
            review_title = abstract_soup.find('span', {'class': re.compile(r'kstarOriginal-topic-')}).text.strip('\n')
            if review_title:
                movie_review_title = review_title
        except:
            print('No abstract found')
        print('Download accessories')
        if download_details or download_accessories:
            get_movie_accessories(driver, movie_name, path)
        driver.back()
        time.sleep(1)
        # print(movie_foriegn_name)
        # print(movie_review_title)
        print("Details Acquired!")
    return more_details, movie_foriegn_name, movie_review_title, movie_review_url, movie_summary

# Main function get movie info and write in a csv
def parse_movie_data(list_name, movies, driver, current_movie_num, num_movies):
    # working on movies list
    path = './movies/'+ list_name
    if not os.path.exists(path):
        os.makedirs(path)
        print('Creating directory for info associated with movie list.')
    else:
        c = 0
        while os.path.exists(path):
            path = path + str(c)
            c += 1
        os.makedirs(path)
        print('Creating directory for info associated with movie list.')
        
    with open(path + '/' + list_name + '.csv', 'w', encoding='utf-8') as file:
        # Write file header
        if not download_details:
            header = '编号,电影名称,上映时间,制片地区,类型,时长(分钟）\n'
        else:
            header = '编号,电影名称,上映时间,制片地区,类型,时长(分钟）,外文名,解说名,解说URL\n'
        file.write(header)

        num_scroll = 0
        movie_num_at_current_scroll = 0
        current_movie_num = 0
        while current_movie_num < num_movies:
            ind = 0
            while ind < len(movies):
                start_time = time.time()
                movie = movies[ind]
                try:
                    movie_data = get_movie_general_data(movie)
                except:
                    # scroll to previous position before page switch
                    for _ in range(num_scroll):
                        driver, _ = scroll(driver)
                    # reattach movie elements 
                    reattached_movies, _, _, _ = get_movie_list(driver, 
                                                    "",
                                                    first_time=False,
                                                    current_movie_num=movie_num_at_current_scroll)
                    if reattached_movies:
                        movies = reattached_movies
                    try:
                        movie_data = get_movie_general_data(movie)
                    except:
                        print("Can't get data for this movie, skip")
                        current_movie_num += 1
                        ind += 1
                        continue

                movie_rank, movie_name, movie_premiere_date, movie_prod_loc, movie_genre, movie_duration = movie_data
                line_info = [movie_rank, movie_name, movie_premiere_date, movie_prod_loc, movie_genre, movie_duration]
                print("Getting info for " + movie_name + " ...")

                # downloading cover photo
                if download_cover:
                    get_cover_photo(movie, path, movie_name)
                        
                if download_details or download_accessories:
                    details = get_movie_details(movie, movie_name, path, driver)
                    details_acquired, movie_foriegn_name, movie_review_title, movie_review_url, movie_summary = details
                    line_info += [movie_foriegn_name, movie_review_title, movie_review_url]
                    # If there was a page change
                    if details_acquired:
                        # scroll to previous position before page switch
                        for _ in range(num_scroll):
                            driver, _ = scroll(driver)
                        # reattach movie elements 
                        movies, _, _, _ = get_movie_list(driver, 
                                                        "",
                                                        first_time=False,
                                                        current_movie_num=movie_num_at_current_scroll)
                current_movie_num += 1
                # write information to csv file
                file_line = ','.join(line_info)
                file_line += '\n'
                print(file_line)
                file.write(file_line)
                ind += 1
                print("--- %s seconds ---\n\n" % (time.time() - start_time))
            # scroll to get info on more movies
            driver, _ = scroll(driver)
            # last_movie_num = current_movie_num
            new_movies, _, _, _ = get_movie_list(driver, 
                                             "",
                                             first_time=False,
                                             current_movie_num=current_movie_num)
            if new_movies:
                movies = new_movies
            movie_num_at_current_scroll = current_movie_num
            num_scroll += 1
        print("Finished 完成！！！")


def parse_arg():
    with open("params.yaml", "r", encoding='utf-8') as stream:
        try:
            params = yaml.safe_load(stream)
            print(params)
            return params
        except yaml.YAMLError as exc:
            print(exc)
            return None

if __name__ == "__main__":

    # Parsing parameters from yaml
    params = parse_arg()
    if params:
        download_cover = params['download_cover']
        download_details = params['download_details']
        download_accessories = params['download_accessories']
        url = params['url']

        chrome_options = Options()
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.47")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--allow-insecure-localhost')
        
        driver = webdriver.Chrome(service=ChromeService( 
            ChromeDriverManager().install()), options=chrome_options) 
        driver.maximize_window()

        begin_time = time.time()
        movies, current_movie_num, list_name, num_movies = get_movie_list(driver, url)
        parse_movie_data(list_name, movies, driver, current_movie_num, num_movies)
        secs_used = (time.time() - begin_time)
        hours_used = secs_used//3600
        remain_mins = (secs_used % 3600) // 60
        remain_secs = (secs_used % 3600) % 60
        print("---用时 {0}小时 {1}分钟 {2}秒， 共{3}秒---\n\n".format(hours_used, remain_mins, remain_secs, secs_used))
    else:
        print("Invalid Params, 请检查 params.yaml 的参数格式！")
