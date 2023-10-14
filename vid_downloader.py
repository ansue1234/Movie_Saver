import argparse
import os
import requests
import pandas as pd
import time

def download_video(path, movie_name, url):
    start_time = time.time()
    print("Current movie: " + movie_name)
    try:
        print("Getting vid...")
        r = requests.get(url)
        new_path = path + '/' + movie_name
        if not os.path.exists(new_path):
            os.makedirs(new_path)
            print('Creating directory for vid associated with movie.')

        with open(new_path + '/' + movie_name + '_解说.mp4', "wb") as vid: 
            print("Saving vid...")
            for chunk in r.iter_content(chunk_size=1024): 
                # writing one chunk at a time to vid file 
                if chunk: 
                    vid.write(chunk) 
            print("Video saved!")
            print('-----{0:.4f}s-----'.format(time.time()-start_time))
    except:
        print("can't download video")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("movie_list", help="影单名")
    args = parser.parse_args()
    movie_list = args.movie_list

    try:
        path = './movies/'+ movie_list 
        movie_info_df = pd.read_csv(path + '/'+ movie_list +'.csv')
        movie_info_df = movie_info_df[['电影名称', '解说URL']]
        movie_info_df = movie_info_df[movie_info_df['解说URL'].notna()]
        for index, row in movie_info_df.iterrows():
            movie_name = row['电影名称']
            movie_review_url = row['解说URL']
            download_video(path, movie_name, movie_review_url)
    except:
        print('无法获取解说链接，请先运行downloader.py获取影单资源！')
