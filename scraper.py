import bs4
import json
import os
import requests
import time
from dotenv import load_dotenv
from newsapi import NewsApiClient
from urllib.parse import urlparse

# load the API key from the .env file
load_dotenv()
# Initialize the client with an API key
API_KEY = os.getenv("NEWSAPI_KEY")
newsapi = NewsApiClient(api_key=API_KEY)


def add_domain(domains, url):
    """
    Check for dublicates and add to the sources list
    Parameters:
        domains (list[str]): list of domains to add the URL to
        url (str): url to add
    """
    if url not in domains:
        domains.append(url)


def get_domain_list(articles):
    """
    Retrieve news source URLs from NewsAPI data
    Parameters:
        articles (dict): newsapi.get_top_headlines(*args, **kwargs)["articles"]
    Returns:
        list[str]: List of the URLs for RSS feed scraping
    """
    domain_list = []
    for article in articles:
        source_url = urlparse(article["url"]).netloc
        add_domain(domain_list, "http://{}".format(source_url))
    return domain_list


def scrap_feed(domain):
    """
    Scraps the given news source RSS feed
    Parameters:
        domain (str): news source to crawl
    Returns:
        None | bs4.BeautifulSoup: None if 404 or XML response for parsing
    """
    try:
        response = requests.get("{}/rss".format(domain))
    except Exception as e:
        print("Source <{0}> : {1}".format(domain, e))
    else:
        if response.status_code == 404:
            print(
                "Source <{}>: RSS feed not found by default URL".format(domain)
            )
            return None
        else:
            return bs4.BeautifulSoup(response.content, "lxml")


def retrieve_headlines(soup):
    """
    Parses the XML data and retrieves headlines
    Parameters:
        soup (bs4.BeautifulSoup): XML input
    Returns:
        list[str]: List of headlines from the XML response
    """
    source_delimiter = "–"
    invalid_titles = ["\n", ""]
    articles = soup.findAll("item")
    result = []
    for a in articles:
        title = a.find("title").text
        if source_delimiter in title:
            result.append(title.split(source_delimiter)[0].strip())
        elif title in invalid_titles:
            continue
        elif title in result:
            continue
        else:
            result.append(title)
    return result


def main():
    all_titles = []
    start = time.process_time()
    print("Commencing scraping...")
    # fetch top headlines from NewsAPI to retrieve news sources
    # change language and country according to your desired
    top_headlines = newsapi.get_top_headlines(language="ru", country="ru")
    # Retrieve news source URLs from the fetched news
    domains = get_domain_list(top_headlines["articles"])
    # Using the retrieved URLs scrap their RSS feeds
    for domain in domains:
        # Scrap each listed resource
        rss_feed = scrap_feed(domain)
        # If result is not None (not found)
        # parse XML response and retrieve the headlines
        if rss_feed:
            titles = retrieve_headlines(rss_feed)
            all_titles.extend(titles)
    end = time.process_time()
    print("Scraping complete!")
    print("Time elapsed: {}".format(end - start))
    # Write the result to a json file to feed it to Markov chain
    with open("output.json", "w", encoding="utf-8") as output:
        json.dump({"titles": all_titles}, output, ensure_ascii=False)


if __name__ == '__main__':
    main()
