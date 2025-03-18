import requests
from bs4 import BeautifulSoup


class Opinion:
    """Represents a single product review."""
    def __init__(self, opinion_id, author, recommendation, score, content, pros, cons, helpful, unhelpful, publish_date, purchase_date):
        self.opinion_id = opinion_id
        self.author = author
        self.recommendation = recommendation
        self.score = score
        self.content = content
        self.pros = pros
        self.cons = cons
        self.helpful = helpful
        self.unhelpful = unhelpful
        self.publish_date = publish_date
        self.purchase_date = purchase_date

    def to_dict(self):
        """Convert object to dictionary for JSON storage."""
        return self.__dict__
    


class Product:
    """Represents a product with its reviews."""
    def __init__(self, product_id, name=None, reviews=None):
        self.product_id = product_id
        self.name = name
        self.reviews = reviews if reviews else []

    def number_of_opinions(self):
        """Returns the total number of opinions."""
        return len(self.reviews)

    def fetch_reviews(self):
        from utils import save_products
        from routes import products
        """Fetches reviews from Ceneo.pl"""
        base_url = f"https://www.ceneo.pl/{self.product_id}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}
        response = requests.get(base_url + "#tab=reviews", headers=headers)
        if response.status_code != 200:
            print("Error: Unable to fetch reviews")
            return
        
        soup = BeautifulSoup(response.text, "html.parser")


        product_name_tag = soup.select_one("h1.product-top__product-info__name, h1.long-name")
        self.name = product_name_tag.text.strip() if product_name_tag else "Unknown Product"

        page_numbers = [int(a.text) for a in soup.select(".pagination__item") if a.text.isdigit()]
        max_page = max(page_numbers) if page_numbers else 1

        for page in range(1, max_page + 1):
            url = f"{base_url}/opinie-{page}"
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                break
            
            soup = BeautifulSoup(response.text, "html.parser")
            reviews = soup.select(".js_product-review")
            if not reviews:
                break
            
            for review in reviews:
                recommendation_tag = review.select_one(".user-post__author-recomendation em")
                recommendation = recommendation_tag.text.strip() if recommendation_tag else "No recommendation"

                opinion = Opinion(
                    opinion_id=review.get("data-entry-id", ""),
                    author=review.select_one(".user-post__author-name").text.strip() if review.select_one(".user-post__author-name") else "Unknown",
                    recommendation=recommendation,  
                    score=float(review.select_one(".user-post__score-count").text.replace(",", ".").replace("/5", "").strip()) if review.select_one(".user-post__score-count") else 0.0,
                    content=review.select_one(".user-post__text").text.strip() if review.select_one(".user-post__text") else "No content",
                    pros=", ".join([item.text.strip() for item in review.find_all("div", class_="review-feature__item") 
                                    if item.find_previous_sibling("div", class_="review-feature__title") 
                                    and "Zalety" in item.find_previous_sibling("div", class_="review-feature__title").text]) or "None",

                    cons=", ".join([item.text.strip() for item in review.find_all("div", class_="review-feature__item") 
                                    if item.find_previous_sibling("div", class_="review-feature__title") 
                                    and "Wady" in item.find_previous_sibling("div", class_="review-feature__title").text]) or "None",

                    helpful=int(review.select_one(".vote-yes .js_product-review-vote").text.strip()) if review.select_one(".vote-yes .js_product-review-vote") else 0,
                    unhelpful=int(review.select_one(".vote-no .js_product-review-vote").text.strip()) if review.select_one(".vote-no .js_product-review-vote") else 0,
                    publish_date=review.select_one(".user-post__published > time:nth-of-type(1)")["datetime"] if review.select_one(".user-post__published > time:nth-of-type(1)") else "",
                    purchase_date=review.select_one(".user-post__published > time:nth-of-type(2)")["datetime"] if review.select_one(".user-post__published > time:nth-of-type(2)") else ""
                )

                
                self.reviews.append(opinion)
        
        print(f"Total reviews fetched: {len(self.reviews)}")
        save_products(products)

    def advantages_count(self):
        """Returns the number of reviews that mention advantages (pros)."""
        return sum(1 for review in self.reviews if review.pros and review.pros != "None")

    def disadvantages_count(self):
        """Returns the number of reviews that mention disadvantages (cons)."""
        return sum(1 for review in self.reviews if review.cons and review.cons != "None")

    def average_score(self):
        """Returns the average score of the product or 0 if no reviews."""
        if not self.reviews:
            return 0
        return round(sum(review.score for review in self.reviews) / len(self.reviews), 1)