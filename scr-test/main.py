from bs4 import BeautifulSoup
import requests
import time
import pandas as pd


def main():
    target_link = "https://ponapalt.hatenablog.com/archive/category/CHANGELOG"

    components = []
    current_target = target_link
    while True:
        print("processing " + current_target + "...")
        responce = requests.get(current_target)
        html_doc = responce.text
        soup = BeautifulSoup(html_doc, 'html.parser')
        articles = soup.find_all("section", class_="archive-entry")

        for article in articles:
            title = article.h1.text.strip()
            description = article.find(
                "p", class_="entry-description").text.strip()
            link = article.find("a", class_="entry-title-link").get("href")
            components.append([title, description, link])

        next_page = soup.find("a", class_="test-pager-next")
        if bool(next_page):
            current_target = next_page.get("href")
        else:
            break

        time.sleep(5)

    for component in components:
        print(component)

    df = pd.DataFrame(data=components, columns=["Title", "Description", "Url"])
    df.to_csv("df.csv")


if __name__ == "__main__":
    main()
