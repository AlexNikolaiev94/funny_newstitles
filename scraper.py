import argparse
import bs4
import csv
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
    domain_list = domains
    """
    Check for duplicates and add to the sources list

    Parameters:
        domains (list[str]): list of domains to add the URL to
        url (str): url to add
    """
    if url not in domain_list:
        domain_list.append(url)
    return domain_list


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
        domain_list = add_domain(domain_list, "http://{}".format(source_url))
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
    """
    Crawl RSS feed of several news resources of a given country and language.
    News resources URLs are fetched from NewsAPI

    Parameters:
        api_key (str): An API key to initialize NewsAPI client and fetch data

    Returns:
        list[str]: List of news headlines
    """
    headlines = []
    # Initialize the NewsAPI client with an API key
    newsapi = NewsApiClient(api_key=api_key)
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
            headlines.extend(titles)
    return headlines


@benchmark
def crawl_given_website(url):
    """
    Crawl RSS feed of a given website

    Parameters:
        url (str): News website to scrap

    Returns:
        list[str]: List of news headlines
    """
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
    # Make sure either website or NewsAPI key is given
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-u", "--url", nargs=1, dest="site_url",
                        help="pass news website")
    source.add_argument("-k", "--key", nargs=1, dest="api_key",
                        help="pass NewsAPI key")
    # Make sure one of the available output formats is specified
    output_format = parser.add_mutually_exclusive_group(required=True)
    output_format.add_argument("--csv", action="store_true",
                        help="generate input file in CSV")
    output_format.add_argument("--json", action="store_true",
                        help="generate input file in JSON")
    args = parser.parse_args()
    if args.site_url:
        headlines = crawl_given_website(args.site_url[0])
    elif args.api_key:
        headlines = crawl_newsapi_resources(args.api_key[0])
    # Write the result to a file to feed it to Markov chain
    if args.csv:
        with open("input.csv", "w", newline="", encoding="utf-8") as _file:
            fieldnames = ["headline", ]
            writer = csv.DictWriter(_file, fieldnames)
            writer.writeheader()
            for h in headlines:
                writer.writerow({"headline": h})
        sys.exit(0)
    elif args.json:
        with open("input.json", "w", encoding="utf-8") as _file:
            json.dump({"headlines": headlines}, _file, ensure_ascii=False)
        sys.exit(0)


if __name__ == '__main__':
    main(sys.argv[1:])
