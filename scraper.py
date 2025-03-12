import requests
from bs4 import BeautifulSoup
import json
import csv
import matplotlib.pyplot as plt

def get_product_reviews(product_id):
    """Fetches all reviews for a given product ID from Ceneo.pl."""
    base_url = f"https://www.ceneo.pl/{product_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    all_reviews = []

    # Fetch the first page to determine the total number of pages
    response = requests.get(base_url + "#tab=reviews", headers=headers)
    if response.status_code != 200:
        print("Error loading the page")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    page_numbers = [int(a.text) for a in soup.select(".pagination__item") if a.text.isdigit()]
    max_page = max(page_numbers) if page_numbers else 1

    # Loop through all pages
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
                "score": float(review.select_one(".user-post__score-count").text.replace(",", ".").replace("/5", "").strip()) if review.select_one(".user-post__score-count") else 0.0,
                "content": review.select_one(".user-post__text").text.strip() if review.select_one(".user-post__text") else "",
                "advantages": ", ".join([li.text.strip() for li in review.select(".review-feature__title--positives ~ .review-feature__item")]) if review.select(".review-feature__title--positives ~ .review-feature__item") else "",
                "disadvantages": ", ".join([li.text.strip() for li in review.select(".review-feature__title--negatives ~ .review-feature__item")]) if review.select(".review-feature__title--negatives ~ .review-feature__item") else "",
                "helpful": int(review.select_one(".vote-yes .js_product-review-vote")['data-total-vote']) if review.select_one(".vote-yes .js_product-review-vote") else 0,
                "unhelpful": int(review.select_one(".vote-no .js_product-review-vote")['data-total-vote']) if review.select_one(".vote-no .js_product-review-vote") else 0,
                "publish_date": review.select_one(".user-post__published > time:nth-of-type(1)")['datetime'] if review.select_one(".user-post__published > time:nth-of-type(1)") else "",
                "purchase_date": review.select_one(".user-post__published > time:nth-of-type(2)")['datetime'] if review.select_one(".user-post__published > time:nth-of-type(2)") else ""
            }
            all_reviews.append(review_data)
    
    return all_reviews

def generate_charts(stats, product_id):
    """Generates and saves statistical charts."""
    labels = ["Positive (4-5 stars)", "Negative (1-2 stars)", "Neutral (3 stars)"]
    values = [stats["Positive reviews (4-5 stars)"], stats["Negative reviews (1-2 stars)"], stats["Total reviews"] - stats["Positive reviews (4-5 stars)"] - stats["Negative reviews (1-2 stars)"]]
    
    plt.figure(figsize=(8, 5))
    plt.pie(values, labels=labels, autopct='%1.1f%%', colors=['green', 'red', 'gray'], startangle=140)
    plt.title("Review Sentiment Distribution")
    plt.savefig(f"review_sentiment_{product_id}.png")
    plt.close()
    
    plt.figure(figsize=(8, 5))
    plt.bar(["1★", "2★", "3★", "4★", "5★"], [
        sum(1 for r in reviews if r['score'] == 1),
        sum(1 for r in reviews if r['score'] == 2),
        sum(1 for r in reviews if r['score'] == 3),
        sum(1 for r in reviews if r['score'] == 4),
        sum(1 for r in reviews if r['score'] == 5)
    ], color=['red', 'orange', 'gray', 'lightgreen', 'green'])
    plt.title("Star Ratings Distribution")
    plt.xlabel("Rating")
    plt.ylabel("Number of Reviews")
    plt.savefig(f"star_distribution_{product_id}.png")
    plt.close()

if __name__ == "__main__":
    product_id = input("Enter the product ID from Ceneo.pl: ")
    reviews = get_product_reviews(product_id)
    
    if reviews:
        stats = {
            "Total reviews": len(reviews),
            "Positive reviews (4-5 stars)": sum(1 for r in reviews if r['score'] >= 4),
            "Negative reviews (1-2 stars)": sum(1 for r in reviews if r['score'] <= 2)
        }
        generate_charts(stats, product_id)
        print(f"Charts saved as 'review_sentiment_{product_id}.png' and 'star_distribution_{product_id}.png'")
    else:
        print("No reviews found.")
