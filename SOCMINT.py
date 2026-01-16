#!/usr/bin/env python3
"""
SOCMINT Tool - Social Media Intelligence Collection
A comprehensive tool for gathering publicly available information from social media platforms.
Designed for educational and ethical use only.

Dependencies:
- Python 3.6+
- Required packages: requests, beautifulsoup4, pandas, colorama
"""

import argparse
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import csv
import os
from datetime import datetime
import sys

class SocialMediaIntelligenceTool:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
        })
        self.results = {}
        self.target_username = ""
        
    def instagram_recon(self, username):
        """Gather information from Instagram profiles"""
        print(f"[+] Instagram reconnaissance for: {username}")
        
        # Basic Instagram profile URL
        profile_url = f"https://www.instagram.com/{username}/"
        
        try:
            response = self.session.get(profile_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract JSON data from Instagram page
                script_tags = soup.find_all('script')
                json_data = None
                
                for script in script_tags:
                    if script.string and 'window._sharedData' in script.string:
                        json_str = script.string.split(' = ')[1].rstrip(';')
                        json_data = json.loads(json_str)
                        break
                
                if json_data:
                    # Extract user information
                    user_data = json_data['entry_data']['ProfilePage'][0]['graphql']['user']
                    
                    instagram_info = {
                        'username': user_data.get('username', 'N/A'),
                        'full_name': user_data.get('full_name', 'N/A'),
                        'biography': user_data.get('biography', 'N/A'),
                        'external_url': user_data.get('external_url', 'N/A'),
                        'followers': user_data.get('edge_followed_by', {}).get('count', 0),
                        'following': user_data.get('edge_follow', {}).get('count', 0),
                        'posts': user_data.get('edge_owner_to_timeline_media', {}).get('count', 0),
                        'is_private': user_data.get('is_private', False),
                        'profile_pic_url': user_data.get('profile_pic_url_hd', user_data.get('profile_pic_url', 'N/A')),
                        'account_type': 'personal' if not user_data.get('is_business_account', False) else 'business'
                    }
                    
                    # Extract additional details
                    if user_data.get('business_category_name'):
                        instagram_info['business_category'] = user_data['business_category_name']
                    
                    if user_data.get('connected_fb_page'):
                        instagram_info['facebook_page'] = user_data['connected_fb_page']
                    
                    self.results['instagram'] = instagram_info
                    print(f"[+] Instagram data collected successfully")
                    
                    # Extract recent posts information
                    posts = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
                    recent_posts = []
                    
                    for i, post in enumerate(posts[:10]):  # Get last 10 posts
                        node = post.get('node', {})
                        post_info = {
                            'shortcode': node.get('shortcode', 'N/A'),
                            'url': f"https://www.instagram.com/p/{node.get('shortcode', '')}/",
                            'caption': node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', 'N/A'),
                            'timestamp': node.get('taken_at_timestamp', 'N/A'),
                            'likes': node.get('edge_media_preview_like', {}).get('count', 0),
                            'comments': node.get('edge_media_to_comment', {}).get('count', 0),
                            'is_video': node.get('is_video', False),
                            'location': node.get('location', {}).get('name', 'N/A') if node.get('location') else 'N/A'
                        }
                        recent_posts.append(post_info)
                    
                    self.results['instagram']['recent_posts'] = recent_posts
                    
                else:
                    print(f"[-] Could not extract JSON data from Instagram page")
                    self.results['instagram'] = {'error': 'Failed to extract data'}
                    
            else:
                print(f"[-] Instagram profile not found or private (HTTP {response.status_code})")
                self.results['instagram'] = {'error': f'Profile not accessible (HTTP {response.status_code})'}
                
        except Exception as e:
            print(f"[-] Instagram reconnaissance failed: {str(e)}")
            self.results['instagram'] = {'error': str(e)}
    
    def tiktok_recon(self, username):
        """Gather information from TikTok profiles"""
        print(f"[+] TikTok reconnaissance for: {username}")
        
        # TikTok profile URL
        profile_url = f"https://www.tiktok.com/@{username}"
        
        try:
            response = self.session.get(profile_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for TikTok API data in script tags
                script_tags = soup.find_all('script')
                json_data = None
                
                for script in script_tags:
                    if script.string and '__DEFAULT_SCOPE__' in script.string:
                        try:
                            # Extract JSON data from TikTok page
                            json_str = script.string.split('__DEFAULT_SCOPE__ = ')[1].split(';')[0]
                            json_data = json.loads(json_str)
                            break
                        except:
                            continue
                
                if json_data:
                    # Extract user information from TikTok data
                    user_data = json_data.get('UserModule', {}).get('users', {}).get(username, {})
                    
                    tiktok_info = {
                        'username': user_data.get('uniqueId', username),
                        'nickname': user_data.get('nickname', 'N/A'),
                        'bio': user_data.get('signature', 'N/A'),
                        'followers': user_data.get('followerCount', 0),
                        'following': user_data.get('followingCount', 0),
                        'likes': user_data.get('heartCount', 0),
                        'videos': user_data.get('videoCount', 0),
                        'is_verified': user_data.get('verified', False),
                        'is_private': user_data.get('privateAccount', False),
                        'profile_pic_url': user_data.get('avatarLarger', 'N/A'),
                        'account_created': user_data.get('createTime', 'N/A')
                    }
                    
                    # Extract video information
                    videos = user_data.get('aweme_list', [])[:10]  # Get last 10 videos
                    recent_videos = []
                    
                    for video in videos:
                        video_info = {
                            'id': video.get('aweme_id', 'N/A'),
                            'title': video.get('desc', 'N/A'),
                            'duration': video.get('duration', 0),
                            'play_count': video.get('play_count', 0),
                            'digg_count': video.get('digg_count', 0),
                            'comment_count': video.get('comment_count', 0),
                            'share_count': video.get('share_count', 0),
                            'create_time': video.get('create_time', 'N/A'),
                            'has_music': video.get('music', {}) != {},
                            'has_location': video.get('poi', {}) != {}
                        }
                        recent_videos.append(video_info)
                    
                    tiktok_info['recent_videos'] = recent_videos
                    self.results['tiktok'] = tiktok_info
                    print(f"[+] TikTok data collected successfully")
                    
                else:
                    print(f"[-] Could not extract TikTok user data")
                    self.results['tiktok'] = {'error': 'Failed to extract data'}
                    
            else:
                print(f"[-] TikTok profile not found or private (HTTP {response.status_code})")
                self.results['tiktok'] = {'error': f'Profile not accessible (HTTP {response.status_code})'}
                
        except Exception as e:
            print(f"[-] TikTok reconnaissance failed: {str(e)}")
            self.results['tiktok'] = {'error': str(e)}
    
    def facebook_recon(self, username):
        """Gather information from Facebook profiles"""
        print(f"[+] Facebook reconnaissance for: {username}")
        
        # Facebook profile URL
        profile_url = f"https://www.facebook.com/{username}"
        
        try:
            response = self.session.get(profile_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html_parser')
                
                # Extract basic information from HTML
                facebook_info = {
                    'username': username,
                    'profile_url': profile_url,
                    'page_title': soup.find('title').get_text().strip() if soup.find('title') else 'N/A',
                    'meta_description': '',
                    'public_posts': []
                }
                
                # Extract meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    facebook_info['meta_description'] = meta_desc.get('content', 'N/A')
                
                # Look for public posts
                post_elements = soup.find_all('div', class_='userContent')
                public_posts = []
                
                for i, post in enumerate(post_elements[:5]):  # Get last 5 public posts
                    post_text = post.get_text().strip()
                    if post_text and len(post_text) > 20:  # Only substantial posts
                        public_posts.append({
                            'content': post_text[:200] + '...' if len(post_text) > 200 else post_text,
                            'timestamp': 'N/A'  # Facebook timestamps are complex to extract
                        })
                
                facebook_info['public_posts'] = public_posts
                self.results['facebook'] = facebook_info
                print(f"[+] Facebook data collected successfully")
                
            else:
                print(f"[-] Facebook profile may be private or not found (HTTP {response.status_code})")
                self.results['facebook'] = {'error': f'Profile not accessible (HTTP {response.status_code})'}
                
        except Exception as e:
            print(f"[-] Facebook reconnaissance failed: {str(e)}")
            self.results['facebook'] = {'error': str(e)}
    
    def cross_platform_username_search(self, username):
        """Search for the same username across multiple platforms"""
        print(f"[+] Cross-platform username search for: {username}")
        
        # List of platforms to check
        platforms = [
            'instagram.com',
            'tiktok.com', 
            'facebook.com',
            'twitter.com',
            'github.com',
            'linkedin.com',
            'reddit.com',
            'pinterest.com',
            'tumblr.com',
            'medium.com',
            'deviantart.com',
            'flickr.com',
            'dribbble.com',
            'behance.net',
            'youtube.com',
            'soundcloud.com',
            'spotify.com',
            'steamcommunity.com',
            'battle.net',
            ' twitch.tv',
            'discord.com',
            'telegram.org',
            'wa.me',
            'snapchat.com',
            'tiktok.com'
        ]
        
        found_platforms = {}
        
        for platform in platforms:
            url = f"https://{platform}/{username}"
            try:
                response = self.session.get(url, timeout=5, allow_redirects=False)
                
                # Check if username exists on platform
                if response.status_code == 200:
                    found_platforms[platform] = {
                        'url': url,
                        'status': 'found',
                        'http_status': response.status_code
                    }
                    print(f"[+] Found on {platform}")
                elif response.status_code == 302:
                    found_platforms[platform] = {
                        'url': url,
                        'status': 'redirect',
                        'http_status': response.status_code,
                        'redirect_url': response.headers.get('Location', 'N/A')
                    }
                    print(f"[+] Redirect found on {platform}")
                else:
                    found_platforms[platform] = {
                        'url': url,
                        'status': 'not_found',
                        'http_status': response.status_code
                    }
                    
            except Exception as e:
                found_platforms[platform] = {
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                }
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        self.results['cross_platform'] = found_platforms
        print(f"[+] Cross-platform search completed. Found on {len([p for p in found_platforms.values() if p['status'] == 'found'])} platforms")
    
    def generate_report(self, output_format='json'):
        """Generate a comprehensive report"""
        if not self.results:
            print("[-] No data to generate report")
            return
        
        report = {
            'target': self.target_username,
            'timestamp': datetime.now().isoformat(),
            'data': self.results,
            'summary': {
                'platforms_analyzed': len([k for k in self.results.keys() if k != 'cross_platform']),
                'total_findings': 0
            }
        }
        
        # Calculate summary statistics
        for platform, data in self.results.items():
            if platform != 'cross_platform' and isinstance(data, dict) and 'error' not in data:
                if platform == 'instagram':
                    report['summary']['total_findings'] += sum([
                        1 if data.get(key) else 0 
                        for key in ['full_name', 'biography', 'external_url', 'business_category']
                    ])
                elif platform == 'tiktok':
                    report['summary']['total_findings'] += sum([
                        1 if data.get(key) else 0 
                        for key in ['nickname', 'bio', 'account_created']
                    ])
                elif platform == 'facebook':
                    report['summary']['total_findings'] += len(data.get('public_posts', []))
        
        # Cross-platform findings
        if 'cross_platform' in self.results:
            cross_found = len([p for p in self.results['cross_platform'].values() if p['status'] == 'found'])
            report['summary']['cross_platform_findings'] = cross_found
        
        # Save report
        if output_format.lower() == 'json':
            filename = f"socint_report_{self.target_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"[+] Report saved as: {filename}")
        
        elif output_format.lower() == 'csv':
            filename = f"socint_report_{self.target_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Platform', 'Field', 'Value'])
                
                for platform, data in self.results.items():
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, (list, dict)):
                                continue
                            writer.writerow([platform, key, str(value)])
            
            print(f"[+] Report saved as: {filename}")
        
        # Print summary
        print(f"\n[=== INTELLIGENCE SUMMARY ===]")
        print(f"Target: {self.target_username}")
        print(f"Platforms Analyzed: {report['summary']['platforms_analyzed']}")
        print(f"Total Findings: {report['summary']['total_findings']}")
        if 'cross_platform_findings' in report['summary']:
            print(f"Cross-Platform Matches: {report['summary']['cross_platform_findings']}")
        print(f"[===========================]")

def main():
    parser = argparse.ArgumentParser(
        description='SOCMINT Tool - Social Media Intelligence Collection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python socint_tool.py -u target_user
  python socint_tool.py -u target_user --platforms instagram,tiktok
  python socint_tool.py -u target_user --cross-platform
  python socint_tool.py -u target_user --output json
  python socint_tool.py -u target_user --output csv
        """
    )
    
    parser.add_argument('-u', '--username', required=True, help='Target username to investigate')
    parser.add_argument('-p', '--platforms', nargs='+', 
                       choices=['instagram', 'tiktok', 'facebook', 'all'],
                       default=['all'], help='Platforms to analyze (default: all)')
    parser.add_argument('--cross-platform', action='store_true', 
                       help='Search for username across multiple platforms')
    parser.add_argument('-o', '--output', choices=['json', 'csv'], default='json',
                       help='Output format (default: json)')
    parser.add_argument('--timeout', type=int, default=10, 
                       help='Request timeout in seconds (default: 10)')
    parser.add_argument('--delay', type=float, default=1.0, 
                       help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Initialize tool
    tool = SocialMediaIntelligenceTool()
    tool.target_username = args.username
    
    print(f"[*] Starting SOCMINT investigation for: {args.username}")
    print(f"[*] Platforms: {', '.join(args.platforms)}")
    print(f"[*] Output format: {args.output}")
    print(f"[*] Cross-platform search: {'Enabled' if args.cross_platform else 'Disabled'}")
    
    # Set session timeout
    tool.session.timeout = args.timeout
    
    if args.verbose:
        print(f"[*] Request timeout: {args.timeout}s")
        print(f"[*] Request delay: {args.delay}s")
    
    # Analyze specified platforms
    platforms_to_analyze = args.platforms if 'all' not in args.platforms else ['instagram', 'tiktok', 'facebook']
    
    for platform in platforms_to_analyze:
        if platform == 'instagram':
            tool.instagram_recon(args.username)
        elif platform == 'tiktok':
            tool.tiktok_recon(args.username)
        elif platform == 'facebook':
            tool.facebook_recon(args.username)
        
        # Delay between requests to avoid rate limiting
        if args.delay > 0:
            time.sleep(args.delay)
    
    # Perform cross-platform search if requested
    if args.cross_platform:
        tool.cross_platform_username_search(args.username)
    
    # Generate report
    tool.generate_report(args.output)
    
    print(f"\n[*] SOCMINT investigation completed for: {args.username}")

if __name__ == "__main__":
    main()
