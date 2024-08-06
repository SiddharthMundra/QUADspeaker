import os
import requests
import schedule
import tweepy
import logging
from bs4 import BeautifulSoup
import openai
import time
from pytrends.request import TrendReq
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


# Custom Constant API Keys (From X Developer Website and OpenAI)
API_KEY = "x"
API_SECRET_KEY = "x"
BEARER_TOKEN = "x
ACCESS_TOKEN = "x"
ACCESS_TOKEN_SECRET = "x
OPENAI_API_KEY = "x"

# Initialize OpenAI API
openai.api_key = OPENAI_API_KEY

# Last tweet file to ensure no 2 tweets for the same topic, keep track of images
LAST_TWEET_FILE = "last_tweet_file.txt"
LAST_TWEET_IMAGE = "last_tweet_image.txt"

# List to store tweets made during the day
daily_tweets = []


def read_posted_titles_newsapi():
    with open("existing.txt", "r") as file:
        titles = {line.strip() for line in file}
    return titles


def write_posted_title_newsapi(title):
    with open("existing.txt", "a") as file:
        file.write(f"{title}\n")


def get_top_headlines(api_key, category="politics", country="us", language="en"):
    url = f"https://newsapi.org/v2/top-headlines?category={category}&country={country}&language={language}&apiKey={api_key}"
    response = requests.get(url)
    articles = response.json().get("articles", [])

    top_3_articles = articles[:10]
    return top_3_articles


def create_twitter_api():
    auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    client_v1 = tweepy.API(auth, wait_on_rate_limit=True)
    # Need 2 for images
    client_v2 = tweepy.Client(
        bearer_token=BEARER_TOKEN,
        consumer_key=API_KEY,
        consumer_secret=API_SECRET_KEY,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET,
    )
    return client_v1, client_v2


def get_chatgpt_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7,
        )
        message = response.choices[0]["message"]["content"].strip()
        message.strip('"')
        return message
    except Exception as e:
        logger.error("Error getting response from ChatGPT", exc_info=True)
        return None


def scrape_latest_news_title_and_image():
    try:
        url = "https://edition.cnn.com/politics"
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the latest news article title and image based on the provided HTML structure
        headlines = soup.find_all("span", class_="container__headline-text")
        image_divs = soup.find_all("div", class_="container__item-media")

        if headlines and len(headlines) > 1 and image_divs and len(image_divs) > 1:
            primary_title = headlines[0].get_text().strip()
            secondary_title = headlines[1].get_text().strip()
            primary_image_url = (
                image_divs[0].find("img")["src"] if image_divs[0].find("img") else None
            )
            secondary_image_url = (
                image_divs[1].find("img")["src"] if image_divs[1].find("img") else None
            )

            # Logging all the extracted information
            logger.info(f"Scraped primary title: {primary_title}")
            logger.info(f"Scraped secondary title: {secondary_title}")
            logger.info(f"Scraped primary image URL: {primary_image_url}")
            logger.info(f"Scraped secondary image URL: {secondary_image_url}")

            return (
                primary_title,
                secondary_title,
                primary_image_url,
                secondary_image_url,
            )
        else:
            logger.warning("No latest news title or image found in the section")
            return None, None, None, None
    except requests.RequestException as e:
        logger.error("Error scraping the web page", exc_info=True)
        return None, None, None, None


def download_image(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        image_path = "latest_image.jpg"
        with open(image_path, "wb") as file:
            file.write(response.content)
        return image_path
    except Exception as e:
        logger.error("Error downloading image", exc_info=True)
        return None


# Read the last news fetched
def read_posted_titles():
    with open(LAST_TWEET_FILE, "r") as file:
        titles = {line.strip() for line in file}
    return titles


def read_posted_images():
    with open(LAST_TWEET_IMAGE, "r") as file:
        titles = {line.strip() for line in file}
    return titles


def write_posted_title(title):
    with open(LAST_TWEET_FILE, "a") as file:
        file.write(f"{title}\n")


def write_posted_image(url):
    with open(LAST_TWEET_IMAGE, "a") as file:
        file.write(f"{url}\n")


def tweet(api_v1, api_v2, message, image_path=None):
    formatted_message = f"BREAKING:\n\n{message}"
    # Ensure the tweet is within the character limit
    if len(formatted_message) > 280:
        formatted_message = formatted_message[:277] + "..."
    try:
        if image_path:
            media = api_v1.media_upload(image_path)
            media_id = media.media_id
            api_v2.create_tweet(text=formatted_message, media_ids=[media_id])
            daily_tweets.append(message)  # Save the tweet for the daily summary
        else:
            api_v2.create_tweet(text=formatted_message)
            daily_tweets.append(message)  # Save the tweet for the daily summary
        print("Tweet posted successfully")
    except Exception as e:
        print("Error posting tweet")


def post_daily_summary(api_v2):
    print("METHOD IS BEING CALLED")
    if daily_tweets:
        summary = "Daily Summary of Political News:\n\n" + "\n".join(daily_tweets)
        api_v2.create_tweet(text=summary)
        logger.info("Daily summary posted successfully")
        daily_tweets.clear()  # Clear the list for the next day


def script1():
    api_v1, api_v2 = create_twitter_api()
    api_key = "a94f9f67149c474a92f7e6232f7b7d3c"  # Replace with your News API key
    articles = get_top_headlines(
        api_key, category="politics", country="us", language="en"
    )

    print("Top Headlines in Politics:")
    for i, article in enumerate(articles):
        title = article["title"]
        description = article.get("description")
        content = article.get("content")
        url = article.get("urlToImage")
        posted_titles = read_posted_titles_newsapi()
        if title not in posted_titles:
            # Print the headline
            x = get_chatgpt_response(
                f"Is the following news related to US news politics? Give a one word YES/NO answer: {title}"
            )
            if x != "NO":
                y = get_chatgpt_response(
                    f'Research the latest news related to: {title}, give me a \25-30 word summary of it, if it is political news, rephrase it to be right wing but do not specifically write right-wring in the output. write tailored, engaging content, with a focus on quality and relevance. this is directly going on twitter so do not write arbitrary output, be mindful. Remove the " from the front and back of the output. add relevant twitter hashtags as well'
                )
                print(y)
                write_posted_title_newsapi(title)
                tweet(api_v1, api_v2, y, url)
        else:
            print("Tweet already exists")


def script2():
    api_v1, api_v2 = create_twitter_api()
    primary_title, secondary_title, primary_image_url, secondary_image_url = (
        scrape_latest_news_title_and_image()
    )
    posted_titles = read_posted_titles()
    tweeted_images = read_posted_images()
    if primary_title not in posted_titles:
        # Check if primary title is tweeted
        if primary_title not in posted_titles:
            if primary_image_url not in tweeted_images:
                prompt = f'Research the latest news related to: {primary_title}, give me a \25-30 word summary of it, if it is political news, rephrase it to be right wing but do not specifically write right-wring in the output. write tailored, engaging content, with a focus on quality and relevance. this is directly going on twitter so do not write arbitrary output, be mindful. Remove the " from the front and back of the output'
                response = get_chatgpt_response(prompt)
                if response:
                    image_path = (
                        download_image(primary_image_url) if primary_image_url else None
                    )
                    tweet(api_v1, api_v2, response, image_path)
                    tweeted_images.add(primary_image_url)
                    write_posted_title(primary_title)
                    write_posted_image(primary_image_url)
                else:
                    logger.info("No response to tweet")
            else:
                logger.info("duplicate image")

        # Check if secondary title is tweeted
        if secondary_title not in posted_titles:
            if secondary_image_url not in tweeted_images:
                prompt = f'Research the latest news related to: {secondary_title}, give me a \25-30 word summary of it, if it is political news, rephrase it to be right wing but do not specifically write right-wring in the output. write tailored, engaging content, with a focus on quality and relevance. this is directly going on twitter so do not write arbitrary output, be mindful. Remove the " from the front and back of the output. add relevant twitter hashtags as well'
                response = get_chatgpt_response(prompt)
                if response:
                    image_path = (
                        download_image(secondary_image_url)
                        if secondary_image_url
                        else None
                    )
                    tweet(api_v1, api_v2, response, image_path)
                    tweeted_images.add(secondary_image_url)
                    write_posted_title(secondary_title)
                    write_posted_image(secondary_image_url)
                else:
                    logger.info("No response to tweet")
            else:
                logger.info("duplicate image")
        else:
            logger.info("Primary and Secondary tweet already exist \n")
    else:
        logger.info("No title to tweet")

    schedule.every().day.at("23:14").do(post_daily_summary, api_v2)


def main():
    script1()
    print("\n\n")
    script2()
    print("Iteration Complete\n\n\n")


if __name__ == "__main__":
    schedule.every(30).seconds.do(main)
    while True:
        schedule.run_pending()
        time.sleep(30)
