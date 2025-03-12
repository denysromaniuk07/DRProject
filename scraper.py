import requests
from bs4 import BeautifulSoup
import json
import csv

def get_product_reviews(product_id):
    """Fetches all reviews for a given product ID from Ceneo.pl."""
    base_url = f"https://www.ceneo.pl/{product_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    all_reviews = []

    response = requests.get(base_url + "#tab=reviews", headers=headers)
    if response.status_code != 200:
        print("Error loading the page")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    page_numbers = [int(a.text) for a in soup.select(".pagination__item") if a.text.isdigit()]
    max_page = max(page_numbers) if page_numbers else 1

    for page in range(1, max_page + 1):
        url = f"{base_url}/opinie-{page}"
        print(f"Fetching: {url}")
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("Error loading the page")
            break
        
        soup = BeautifulSoup(response.text, "html.parser")
        reviews = soup.select(".js_product-review")
        if not reviews:
            print("No more reviews found, stopping.")
            break
        
        for review in reviews:
            review_data = {
                "opinion_id": review.get("data-entry-id", ""),
                "author": review.select_one(".user-post__author-name").text.strip() if review.select_one(".user-post__author-name") else "",
                "score": review.select_one(".user-post__score-count").text.strip() if review.select_one(".user-post__score-count") else "",
                "content": review.select_one(".user-post__text").text.strip() if review.select_one(".user-post__text") else "",
                "advantages": ", ".join([li.text.strip() for li in review.select(".review-feature__title--positives ~ .review-feature__item")]) if review.select(".review-feature__title--positives ~ .review-feature__item") else "",
                "disadvantages": ", ".join([li.text.strip() for li in review.select(".review-feature__title--negatives ~ .review-feature__item")]) if review.select(".review-feature__title--negatives ~ .review-feature__item") else "",
                "helpful": review.select_one(".vote-yes .js_product-review-vote")['data-total-vote'] if review.select_one(".vote-yes .js_product-review-vote") else "0",
                "unhelpful": review.select_one(".vote-no .js_product-review-vote")['data-total-vote'] if review.select_one(".vote-no .js_product-review-vote") else "0",
                "publish_date": review.select_one(".user-post__published > time:nth-of-type(1)")['datetime'] if review.select_one(".user-post__published > time:nth-of-type(1)") else "",
                "purchase_date": review.select_one(".user-post__published > time:nth-of-type(2)")['datetime'] if review.select_one(".user-post__published > time:nth-of-type(2)") else ""
            }
            all_reviews.append(review_data)
    
    return all_reviews

def save_to_csv(data, filename):
    """Saves reviews to a CSV file."""
    keys = data[0].keys() if data else []
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    product_id = input("Enter the product ID from Ceneo.pl: ")
    reviews = get_product_reviews(product_id)
    
    if reviews:
        json_filename = f"reviews_{product_id}.json"
        csv_filename = f"reviews_{product_id}.csv"
        
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(reviews, f, ensure_ascii=False, indent=4)
        print(f"All reviews have been saved to '{json_filename}'")
        
        save_to_csv(reviews, csv_filename)
        print(f"All reviews have been saved to '{csv_filename}'")
    else:
        print("No reviews found.")
