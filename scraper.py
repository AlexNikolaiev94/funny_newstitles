import argparse
import bs4
import json
import requests
import sys
import time
from newsapi import NewsApiClient
from urllib.parse import urlparse


def benchmark(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        print("Commencing scraping...")
        result = func(*args, **kwargs)
        end = time.time()
        print("Scraping complete!")
        print("Time elapsed: {} seconds.".format(end - start))
        return result
    return wrapper


def add_domain(domains, url):
    """
    Check for duplicates and add to the sources list
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


@benchmark
def crawl_newsapi_resources(api_key):
    headlines = []
    # Initialize the NewsAPI client with an API key
    newsapi = NewsApiClient(api_key=api_key)
    # fetch top headlines from NewsAPI to retrieve news sources
    # change language and country according to your desired
    top_headlines = newsapi.get_top_headlines(language="ru", country="ua")
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
            headlines.extend(titles)
    return headlines


@benchmark
def crawl_given_website(url):
    headlines = []
    rss_feed = scrap_feed(url)
    # If result is not None (not found)
    # parse XML response and retrieve the headlines
    if rss_feed:
        headlines = retrieve_headlines(rss_feed)
    return headlines


def main(argv):
    headlines = []
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", help="pass news website")
    parser.add_argument("-k", "--key", help="pass NewsAPI key")
    args = parser.parse_args()
    if args.url:
        headlines = crawl_given_website(args.url)
    elif args.key:
        headlines = crawl_newsapi_resources(args.key)
    else:
        print("Please provide either a website to crawl or a NewsAPI key")
    # Write the result to a json file to feed it to Markov chain
    with open("output.json", "w", encoding="utf-8") as output:
        json.dump({"headlines": headlines}, output, ensure_ascii=False)
    sys.exit(0)


if __name__ == '__main__':
    main(sys.argv[1:])
