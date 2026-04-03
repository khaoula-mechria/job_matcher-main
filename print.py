#importing different libraries
from dataclasses import dataclass
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
import time
import random
import json
from urllib.parse import quote
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from flask import Flask, request, jsonify
from flask_cors import CORS

from datetime import datetime, timedelta

@dataclass
class JobData:
    title: str
    company: str
    location: str
    job_link: str
    posted_date: str
    logo: str
    description: str
    logo_tag: str = ""
    in_time_range: bool = True
    time_note: str = ""


class ScraperConfig:
    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    JOBS_PER_PAGE = 25
    MIN_DELAY = 2
    MAX_DELAY = 5
    RATE_LIMIT_DELAY = 30
    RATE_LIMIT_THRESHOLD = 10

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "DNT": "1",
        "Cache-Control": "no-cache",
    }


class LinkedInJobsScraper:
    def __init__(self):
        self.session = self._setup_session()

    def _setup_session(self) -> requests.Session:
        session = requests.Session()
        retries = Retry(
            total=5, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504]
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def _build_search_url(self, keywords: str, location: str, time_range: str = "", start: int = 0) -> str:
        # Base parameters
        params = {
            "keywords": keywords,
            "location": location,
            "start": start,
        }
        
        # Only add time range parameter if it's provided
        if time_range:
            params["r"] = time_range
        return f"{ScraperConfig.BASE_URL}?{'&'.join(f'{k}={quote(str(v))}' for k, v in params.items())}"

    def _clean_job_url(self, url: str) -> str:
        return url.split("?")[0] if "?" in url else url
    
    def get_job_description(self, job_link: str) -> str:
        """Fetch full job description from the job page."""
        try:
            response = requests.get(job_link, headers=ScraperConfig.HEADERS)
            if response.status_code != 200:
                return "N/A"
            soup = BeautifulSoup(response.text, "html.parser")
            desc_container = soup.find("div", class_="show-more-less-html__markup")
            return desc_container.get_text(strip=True) if desc_container else "N/A"
        except Exception:
            return "N/A"

    def _check_time_range(self, posted_date_str: str, time_range: str) -> tuple[bool, str]:
        if not time_range or posted_date_str == "N/A":
            return True, ""
        
        try:
            # Parse LinkedIn's relative date format
            if "hour" in posted_date_str:
                hours = int(posted_date_str.split()[0])
                post_time = datetime.now() - timedelta(hours=hours)
            elif "day" in posted_date_str:
                days = int(posted_date_str.split()[0])
                post_time = datetime.now() - timedelta(days=days)
            elif "week" in posted_date_str:
                weeks = int(posted_date_str.split()[0])
                post_time = datetime.now() - timedelta(weeks=weeks)
            elif "month" in posted_date_str:
                months = int(posted_date_str.split()[0])
                post_time = datetime.now() - timedelta(days=months*30)
            else:
                return True, ""

            # Convert time_range from seconds to timedelta
            range_seconds = int(time_range)
            time_limit = datetime.now() - timedelta(seconds=range_seconds)

            if post_time > time_limit:
                return True, ""
            else:
                return False, "This job is not in your time range"
        except (ValueError, IndexError):
            return True, ""

    def _extract_job_data(self, job_card: BeautifulSoup, time_range: str = "") -> Optional[JobData]:
        try:
            #title
            title = job_card.find("h3", class_="base-search-card__title").text.strip()
            company = job_card.find(
                "h4", class_="base-search-card__subtitle"
            ).text.strip()
            # logo (small card logo) and logo_tag (fallback/company image)
            # Use a helper to find any likely logo URL inside the card (robust to attribute/class changes)
            def _find_logo_url(card: BeautifulSoup) -> str:
                attrs = ["src", "data-delayed-url", "data-src", "data-original", "data-img-src"]
                selectors = ["img.base-search-card__logo", "img.ivm-image-view_model", "img"]
                for sel in selectors:
                    el = card.select_one(sel)
                    if el:
                        for a in attrs:
                            v = el.get(a)
                            if v and v.strip():
                                return v
                # fallback: check any img inside the card and return first absolute URL found
                for img in card.find_all("img"):
                    for a in attrs:
                        v = img.get(a)
                        if v and v.strip() and (v.startswith("http") or v.startswith("//")):
                            # normalize protocol-relative URLs
                            return v if v.startswith("http") else f"https:{v}"
                return ""

            logo = _find_logo_url(job_card)
            #location
            location = job_card.find(
                "span", class_="job-search-card__location"
            ).text.strip()
            job_link = self._clean_job_url(
                job_card.find("a", class_="base-card__full-link")["href"]
            )
            #date
            posted_date = job_card.find("time", class_="job-search-card__listdate")
            posted_date = posted_date.text.strip() if posted_date else "N/A"
            
            # Check if the job is within the requested time range
            in_range, time_note = self._check_time_range(posted_date, time_range)
             # Description
            description = self.get_job_description(job_link) if job_link != "N/A" else "N/A"

            # prefer logo (already found) as logo_tag
            logo_tag = logo or ""

            # If we still don't have a logo URL, try fetching the job page and look for og:image/twitter:image
            if not logo_tag and job_link and job_link != "N/A":
                try:
                    resp = self.session.get(job_link, headers=ScraperConfig.HEADERS, timeout=8)
                    if resp.status_code == 200:
                        soup_job = BeautifulSoup(resp.text, "html.parser")
                        meta = soup_job.find("meta", property="og:image") or soup_job.find("meta", attrs={"name": "twitter:image"})
                        if meta and meta.get("content"):
                            candidate = meta.get("content").strip()
                            if candidate.startswith("//"):
                                candidate = f"https:{candidate}"
                            logo_tag = candidate
                except Exception:
                    # ignore fetch errors and continue without logo
                    pass

            return JobData(
                title=title,
                company=company,
                location=location,
                job_link=job_link,
                posted_date=posted_date,
                description=description,
                logo=logo,
                logo_tag=logo_tag,
                in_time_range=in_range,
                time_note=time_note
            )
        except Exception as e:
            print(f"Failed to extract job data: {str(e)}")
            return None

    def _fetch_job_page(self, url: str) -> BeautifulSoup:
        try:
            response = self.session.get(url, headers=ScraperConfig.HEADERS)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to fetch data: Status code {response.status_code}"
                )
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            raise RuntimeError(f"Request failed: {str(e)}")

    def scrape_jobs(
        self, keywords: str, location: str, max_jobs: int = 50, time_range: str = "3600") -> List[JobData]:
        max_jobs = int(max_jobs)
        all_jobs = []
        start = 0

        while len(all_jobs) < max_jobs:
            try:
                url = self._build_search_url(keywords, location, time_range, start)
                soup = self._fetch_job_page(url)
                job_cards = soup.find_all("div", class_="base-card")

                if not job_cards:
                    break
                for card in job_cards:
                    job_data = self._extract_job_data(card, time_range)
                    if job_data:
                        all_jobs.append(job_data)
                        if len(all_jobs) >= max_jobs:
                            break
                print(f"Scraped {len(all_jobs)} jobs...")
                start += ScraperConfig.JOBS_PER_PAGE
                time.sleep(
                    random.uniform(ScraperConfig.MIN_DELAY, ScraperConfig.MAX_DELAY)
                )
            except Exception as e:
                print(f"Scraping error: {str(e)}")
                break
        return all_jobs[:max_jobs]

    def save_results(
        self, jobs: List[JobData], filename: str = "linkedin_jobs.json"
    ) -> None:
        if not jobs:
            return
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([vars(job) for job in jobs], f, indent=2, ensure_ascii=False)
        print(f"Saved {len(jobs)} jobs to {filename}")

app = Flask(__name__)
CORS(app)  # Enable CORS for the app

@app.route('/search_jobs', methods=['POST'])
def search_jobs():
    data = request.get_json()
    keywords = data.get('keywords', '')
    location = data.get('location', '')
    max_jobs = data.get('max_jobs', 10)
    time_range = data.get('timeRange', '')  # Default to no time range filter

    scraper = LinkedInJobsScraper()
    jobs = scraper.scrape_jobs(keywords, location, max_jobs, time_range)
    scraper.save_results(jobs)

    return jsonify({'message': f'{len(jobs)} jobs found and saved.', 'jobs': [vars(job) for job in jobs]}), 200
#get jobs from saved file
@app.route('/get_jobs', methods=['GET'])
def get_jobs():
    try:
        with open("linkedin_jobs.json", "r", encoding="utf-8") as f:
            jobs = json.load(f)
        return jsonify({'jobs': jobs}), 200
    except FileNotFoundError:
        return jsonify({'error': 'No jobs file found. Please run the job scraper first.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def main():
    params = {"keywords": "project manager", "location": "Tunis", "max_jobs": 10}

    scraper = LinkedInJobsScraper()
    jobs = scraper.scrape_jobs(**params)
    scraper.save_results(jobs)


if __name__ == "__main__":
    app.run(debug=True)