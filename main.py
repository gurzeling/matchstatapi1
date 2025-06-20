import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RAPIDAPI_KEY")

TOURS = ["ATP", "WTA", "ITF"]
BASE_URL = "https://tennis-api-atp-wta-itf.p.rapidapi.com/results/{}"
HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "tennis-api-atp-wta-itf.p.rapidapi.com"
}

K = 8

def load_ratings():
    try:
        with open("ratings.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_ratings(ratings):
    with open("ratings.json", "w") as f:
        json.dump(ratings, f, indent=2)

def get_yesterday():
    return (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

def fetch_results(tour, date):
    url = BASE_URL.format(tour)
    response = requests.get(url, headers=HEADERS, params={"date": date})
    if response.status_code == 200:
        return response.json().get("results", [])
    else:
        print(f"Failed to fetch {tour} data: {response.status_code}")
        return []

def expected_score(r1, r2):
    return 1 / (1 + 10 ** ((r2 - r1) / 400))

def update_elo(r1, r2, result, k=K):
    e1 = expected_score(r1, r2)
    e2 = expected_score(r2, r1)
    new_r1 = r1 + k * (result - e1)
    new_r2 = r2 + k * ((1 - result) - e2)
    return round(new_r1, 2), round(new_r2, 2)

def process_matches(ratings, matches):
    for match in matches:
        p1 = match.get("player1_name")
        p2 = match.get("player2_name")
        winner = match.get("winner_name")

        if not (p1 and p2 and winner):
            continue

        ratings.setdefault(p1, 1000)
        ratings.setdefault(p2, 1000)

        if winner == p1:
            ratings[p1], ratings[p2] = update_elo(ratings[p1], ratings[p2], 1)
        elif winner == p2:
            ratings[p1], ratings[p2] = update_elo(ratings[p1], ratings[p2], 0)
        else:
            continue  # skip if winner unknown

        print(f"{p1} vs {p2} -> {winner}")
        print(f"Updated ratings: {p1}: {ratings[p1]}, {p2}: {ratings[p2]}\n")

def main():
    ratings = load_ratings()
    date = get_yesterday()

    for tour in TOURS:
        print(f"Fetching {tour} matches for {date}...")
        matches = fetch_results(tour, date)
        process_matches(ratings, matches)

    save_ratings(ratings)
    print("Ratings updated and saved.")

if __name__ == "__main__":
    main()
