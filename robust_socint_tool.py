#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import time
import argparse
import sys
from urllib.parse import quote
import instaloader
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class SocialMediaOSINT:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def get_instagram_profile(self, username):
        """Extract public Instagram profile data using instaloader"""
        try:
            L = instaloader.Instaloader(download_video_thumbnails=False, 
                                      download_geotags=False, 
                                      download_comments=False)
            
            profile = instaloader.Profile.from_username(L.context, username)
            
            data = {
                'username': profile.username,
                'full_name': profile.full_name,
                'biography': profile.biography,
                'followers': profile.followers,
                'following': profile.followees,
                'posts': profile.mediacount,
                'is_private': profile.is_private,
                'is_verified': profile.is_verified,
                'profile_pic_url': profile.profile_pic_url,
                'external_url': profile.external_url
            }
            return data
        except Exception as e:
            return {'error': f'Instagram lookup failed: {str(e)}'}

    def get_instagram_web(self, username):
        """Fallback web scraping for Instagram profile"""
        url = f"https://www.instagram.com/{username}/"
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract JSON data from page
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and 'window._sharedData' in script.string:
                    # Parse the JSON (modern Instagram uses different structure)
                    pass
            
            # Basic scraping
            title = soup.find('title').text if soup.find('title') else 'N/A'
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            desc = meta_desc['content'] if meta_desc else 'N/A'
            
            return {
                'title': title,
                'description': desc,
                'status': 'Public profile detected' if 'not found' not in title.lower() else 'Not found or private'
            }
        except:
            return {'error': 'Web scraping failed'}

    def get_facebook_profile(self, username_or_id):
        """Scrape public Facebook profile information"""
        url = f"https://www.facebook.com/{username_or_id}"
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            data = {
                'url': url,
                'title': soup.title.text if soup.title else 'N/A',
                'public_visibility': 'Detected' if 'profile' in response.text.lower() else 'Not public or not found'
            }
            
            # Look for bio/about info in public sections
            bio_selectors = ['div[data-pagelet="ProfileTimeline"]', '[data-testid="profile_bio"]']
            for selector in bio_selectors:
                bio_elem = soup.select_one(selector)
                if bio_elem:
                    data['bio_snippet'] = bio_elem.get_text(strip=True)[:200]
                    break
            
            return data
        except Exception as e:
            return {'error': f'Facebook lookup failed: {str(e)}'}

    def get_tiktok_profile(self, username):
        """Extract TikTok profile data via web scraping"""
        url = f"https://www.tiktok.com/@{username}"
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(options=options)
            
            driver.get(url)
            time.sleep(3)
            
            data = {
                'username': username,
                'url': url,
                'title': driver.title,
                'bio': 'N/A'
            }
            
            # Extract stats
            try:
                stats = driver.find_elements(By.CSS_SELECTOR, '[data-e2e="followers-count"], [data-e2e="following-count"], [data-e2e="likes-count"]')
                if stats:
                    data['stats'] = [stat.text for stat in stats]
            except:
                pass
            
            try:
                bio_elem = driver.find_element(By.CSS_SELECTOR, '[data-e2e="user-bio"]')
                data['bio'] = bio_elem.text
            except NoSuchElementException:
                pass
            
            driver.quit()
            return data
        except Exception as e:
            return {'error': f'TikTok lookup failed: {str(e)}'}

    def search_linkedin_mentions(self, name):
        """Search for LinkedIn profiles (useful for correlation)"""
        query = quote(f'"{name}" site:linkedin.com')
        url = f"https://www.google.com/search?q={query}"
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            for g in soup.find_all('div', class_='g'):
                a = g.find('a')
                if a and 'linkedin.com/in/' in a.get('href', ''):
                    links.append(a.get('href'))
            return {'linkedin_profiles': links[:3]}
        except:
            return {'linkedin_profiles': []}

def main():
    parser = argparse.ArgumentParser(description='Social Media OSINT Tool for Kali Linux')
    parser.add_argument('target', help='Username, name, or profile identifier')
    parser.add_argument('-p', '--platforms', choices=['facebook', 'instagram', 'tiktok', 'all'], 
                       default='all', help='Platform to query')
    parser.add_argument('-o', '--output', help='Output JSON file')
    
    args = parser.parse_args()
    
    osint = SocialMediaOSINT()
    results = {}
    
    if args.platforms in ['all', 'instagram']:
        print(f"[+] Querying Instagram: {args.target}")
        results['instagram'] = osint.get_instagram_profile(args.target)
        if 'error' in results['instagram']:
            results['instagram_web'] = osint.get_instagram_web(args.target)
    
    if args.platforms in ['all', 'facebook']:
        print(f"[+] Querying Facebook: {args.target}")
        results['facebook'] = osint.get_facebook_profile(args.target)
    
    if args.platforms in ['all', 'tiktok']:
        print(f"[+] Querying TikTok: {args.target}")
        results['tiktok'] = osint.get_tiktok_profile(args.target)
    
    print(f"[+] LinkedIn correlation search for: {args.target}")
    results['linkedin_mentions'] = osint.search_linkedin_mentions(args.target)
    
    # Output results
    print("\n" + "="*60)
    print(json.dumps(results, indent=2))
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"[+] Results saved to {args.output}")

if __name__ == "__main__":
    main()
