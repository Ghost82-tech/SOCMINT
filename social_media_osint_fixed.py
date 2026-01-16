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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class SocialMediaOSINT:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def get_instagram_profile(self, username):
        """Primary Instagram scraper using instaloader"""
        try:
            L = instaloader.Instaloader(
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                compress_json=False
            )
            profile = instaloader.Profile.from_username(L.context, username)
            
            return {
                'username': profile.username,
                'full_name': profile.full_name or 'N/A',
                'biography': profile.biography or 'N/A',
                'followers': profile.followers,
                'following': profile.followees,
                'posts': profile.mediacount,
                'is_private': profile.is_private,
                'is_verified': profile.is_verified,
                'profile_pic_url': str(profile.profile_pic_url),
                'external_url': profile.external_url or 'N/A',
                'status': 'success'
            }
        except instaloader.exceptions.ProfileNotExistsException:
            return {'error': 'Profile does not exist or is private', 'status': 'not_found'}
        except Exception as e:
            return {'error': f'{str(e)}', 'status': 'error'}

    def get_facebook_profile(self, identifier):
        """Facebook public profile scraper"""
        urls = [
            f"https://www.facebook.com/{identifier}",
            f"https://www.facebook.com/profile.php?id={identifier}"
        ]
        
        for url in urls:
            try:
                response = self.session.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                title = soup.title.text.strip() if soup.title else 'N/A'
                
                if 'facebook' not in title.lower():
                    continue
                    
                data = {
                    'url': url,
                    'title': title,
                    'public': 'Yes' if 'timeline' in title.lower() or 'profile' in title.lower() else 'Limited/No public data'
                }
                
                # Extract any visible bio text
                intro_selectors = [
                    '[data-pagelet="ProfileTimeline"]',
                    'div[role="main"] div[dir="auto"]',
                    '.x1yztbdb'
                ]
                for selector in intro_selectors:
                    elem = soup.select_one(selector)
                    if elem and len(elem.get_text(strip=True)) > 10:
                        data['bio_snippet'] = elem.get_text(strip=True)[:300]
                        break
                
                return data
            except:
                continue
        
        return {'error': 'Facebook profile not found or fully private', 'url': urls[0]}

    def get_tiktok_profile(self, username):
        """TikTok profile scraper with Selenium"""
        url = f"https://www.tiktok.com/@{username}"
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(15)
            driver.get(url)
            
            wait = WebDriverWait(driver, 10)
            
            data = {
                'username': username,
                'url': url,
                'title': driver.title,
                'platform': 'TikTok'
            }
            
            # Wait for profile elements
            try:
                # Bio
                bio_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-e2e="user-bio"], .tiktok-1soki0-DivBioSection'))) 
                data['bio'] = bio_elem.text.strip()
            except TimeoutException:
                data['bio'] = 'N/A'
            
            # Stats (followers, following, likes)
            stat_selectors = [
                '[data-e2e="followers-count"]',
                '[data-e2e="following-count"]', 
                '[data-e2e="likes-count"]'
            ]
            stats = []
            for selector in stat_selectors:
                try:
                    stat = driver.find_element(By.CSS_SELECTOR, selector)
                    stats.append(stat.text.strip())
                except:
                    pass
            data['stats'] = stats
            
            driver.quit()
            return data
            
        except Exception as e:
            try:
                driver.quit()
            except:
                pass
            return {'error': f'TikTok scrape failed: {str(e)}', 'url': url}

    def google_dorks(self, query):
        """Run Google dorks for social media footprints"""
        dorks = [
            f'"{query}" site:facebook.com',
            f'"{query}" site:instagram.com',
            f'"{query}" site:tiktok.com/@',
            f'"{query}" site:linkedin.com/in'
        ]
        
        results = {}
        for dork in dorks:
            url = f"https://www.google.com/search?q={quote(dork)}"
            try:
                resp = self.session.get(url, timeout=8)
                soup = BeautifulSoup(resp.text, 'html.parser')
                links = []
                for g in soup.find_all('div', class_='g')[:3]:
                    a = g.find('a')
                    if a and a.get('href'):
                        links.append(a.get('href'))
                platform = dork.split('site:')[1].split('.')[0]
                results[platform] = links
            except:
                results[dork.split('site:')[1].split('.')[0]] = []
        
        return results

def main():
    parser = argparse.ArgumentParser(description='Social Media OSINT - Kali Linux Tool')
    parser.add_argument('target', help='Username/email/name to investigate')
    parser.add_argument('-p', '--platform', choices=['facebook', 'instagram', 'tiktok', 'google', 'all'], 
                       default='all', help='Specific platform')
    parser.add_argument('-o', '--output', help='Output JSON file')
    parser.add_argument('--no-selenium', action='store_true', help='Skip Selenium (faster, less data)')
    
    args = parser.parse_args()
    
    print(f"[+] Social Media OSINT starting for: {args.target}")
    osint = SocialMediaOSINT()
    results = {'target': args.target, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}
    
    if args.platform in ['all', 'instagram']:
        print(f"[+] [+] Instagram lookup...")
        results['instagram'] = osint.get_instagram_profile(args.target)
    
    if args.platform in ['all', 'facebook']:
        print(f"[+] [+] Facebook lookup...")
        results['facebook'] = osint.get_facebook_profile(args.target)
    
    if args.platform in ['all', 'tiktok'] and not args.no_selenium:
        print(f"[+] [+] TikTok lookup (Selenium)...")
        results['tiktok'] = osint.get_tiktok_profile(args.target)
    
    if args.platform in ['all', 'google']:
        print(f"[+] [+] Google dorking...")
        results['google_dorks'] = osint.google_dorks(args.target)
    
    print("\n" + "="*70)
    print(json.dumps(results, indent=2))
    print("="*70)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n[+] Saved to {args.output}")
    
    print(f"\n[+] Scan complete for {args.target}")

if __name__ == "__main__":
    main()
