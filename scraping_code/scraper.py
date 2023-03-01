from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import praw
import datetime
import pandas as pd
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException, ElementClickInterceptedException, NoSuchWindowException, StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from praw.exceptions import InvalidURL


reddit = praw.Reddit(client_id='8y1pAV6ILIGM-qFHoDpwyA', client_secret='x5ggjG-_hKk9kjdH9H-RpKpakWdhAw', user_agent='bootcamp_review')


def search_keywords_in_reddit(keywords):
    result = {}

    reddit = praw.Reddit(client_id='8y1pAV6ILIGM-qFHoDpwyA',
                         client_secret='x5ggjG-_hKk9kjdH9H-RpKpakWdhAw',
                         user_agent='bootcamp_review')

    # open a new window and open reddit
    chrome_options = Options()
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--start-fullscreen")
    chrome_options.add_argument("--no-proxy-server")
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.get("https://www.reddit.com/?feed=home")
    driver.maximize_window()
    time.sleep(1)

    driver.get("https://www.reddit.com/search/?q={0}".format(str(keywords)))
    idx = 1

    while True:
        try:
            post = driver.find_element('xpath',
                                       '//*[@id="AppRouter-main-content"]/div/div/div[2]/div/div/div[2]/div[1]/div[2]/div/div/div[{0}]'.format(
                                           str(idx)))
            actions = ActionChains(driver)
            actions.move_to_element(post).perform()
            time.sleep(1)
            post.click()

            post_url = driver.current_url
            if post_url != None:
                url_list = post_url.split('/')
            if "comments" not in url_list:
                driver.execute_script("window.history.go(-1)")
                driver.get("https://www.reddit.com/search/?q={0}".format(str(keywords)))
                idx += 1
                continue

            submission = reddit.submission(url=post_url)

            print(idx, " -- ", submission.title, " -- ", submission.subreddit)

            result[submission.id] = [keywords,
                                     submission.title,
                                     str(submission.subreddit),
                                     str(submission.author),
                                     str(datetime.datetime.fromtimestamp(submission.created_utc)),
                                     submission.score, submission.selftext,
                                     {}]

            submission.comments.replace_more(limit=0)
            for comment in submission.comments.list():
                author = str(comment.author)
                created_at = str(datetime.datetime.fromtimestamp(comment.created_utc))
                upvotes = comment.score
                body = comment.body
                result[submission.id][7][comment.id] = {'author': author,
                                                        'date': created_at,
                                                        'upvotes': upvotes,
                                                        'content': body}

            # driver.get("https://www.reddit.com/search/?q={0}".format(str(keywords)))
            cross = driver.find_element('xpath', '//*[@id="overlayScrollContainer"]/div[1]/div/div[2]/button')
            cross.click()
            cross.click()

            current_url = driver.current_url
            print(current_url)
            url_list = current_url.split('/')

            if "comments" in url_list:
                driver.execute_script("window.history.go(-1)")
                # driver.get("https://www.reddit.com/search/?q={0}".format(str(keywords)))

            time.sleep(0.5)
            idx += 1

        except (ElementNotInteractableException, ElementClickInterceptedException, NoSuchWindowException):
            print("Element is Not Interactable!")
            idx += 1
            continue
        except InvalidURL:
            print("Invalid URL! This post is either removed or is an AD.")
            idx += 1
            continue
        except NoSuchElementException:
            print("Reached to the end, no more post!")
            idx += 1
            driver.quit()
            break
        except TimeoutException:
            print("Element is not visible")
            idx += 1
            continue
        except StaleElementReferenceException:
            idx += 1
            continue
    return result


def scrape_keyword_from_reddit(keywords_list):
    # df_post = pd.DataFrame(data=[], columns=['post_id', 'query', 'post_title', 'post_subreddit', 'post_author', 'post_date', 'post_upvotes', 'post_desc'])
    # df_comment = pd.DataFrame(data=[], columns=['post_id', 'comment_id', 'comment_author', 'comment_date', 'comment_upvotes', 'comment_content'])

    for cmp in keywords_list:
        print(" -------------------- {} --------------------".format(cmp))
        result = search_keywords_in_reddit(cmp)
        comment = {}

        post_list = []
        comment_list = []



        for k, v in result.items():
            comment[k] = v[7]

        for post_id, detail in result.items():
            post_list.append([post_id, detail[0], detail[1], detail[2], detail[3], detail[4], detail[5], detail[6]])

        for post_id, dict in comment.items():
            for comment_id, cmt in dict.items():
                comment_list.append([post_id, comment_id, cmt['author'], cmt['date'], cmt['upvotes'], cmt['content']])

        df_post = pd.DataFrame(post_list, columns=['post_id', 'post_query', 'title', 'subreddit', 'author', 'date', 'upvotes', 'content'])
        df_comment = pd.DataFrame(comment_list, columns=['post_id', 'comment_id', 'author', 'date', 'upvotes', 'content'])

        df_post.to_csv("{}_posts.csv".format(str(cmp)))
        df_comment.to_csv("{}_comments.csv".format(str(cmp)))
