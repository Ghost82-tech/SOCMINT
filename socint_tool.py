#!/usr/bin/env python3
"""
Enhanced SOCMINT Tool - Comprehensive Public Intelligence Collection
Gathers publicly available information from social media platforms ethically.
Designed for educational and security research purposes only.

Key improvements:
- Enhanced public information extraction
- Better error handling and rate limiting
- Comprehensive reporting and analysis
- Platform-specific optimizations
- Enhanced display of search results
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
import random
import string

class EnhancedSOCMINTTool:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
        })
        # Additional headers for better compatibility
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.results = {}
        self.target_username = ""
        self.request_delay = 1.0
        
    def random_delay(self, min_delay=0.5, max_delay=2.0):
        """Add random delay to avoid detection"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        
    def instagram_recon(self, username):
        """Enhanced Instagram reconnaissance with comprehensive public data extraction"""
        print(f"[+] Instagram reconnaissance for: {username}")
        
        # Multiple approaches for better data extraction
        urls_to_try = [
            f"https://www.instagram.com/{username}/",
            f"https://www.instagram.com/{username}/?__a=1"
        ]
        
        for url in urls_to_try:
            try:
                print(f"[*] Trying: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Method 1: Extract from shared data
                    script_tags = soup.find_all('script')
                    json_data = None
                    
                    for script in script_tags:
                        if script.string and 'window._sharedData' in script.string:
                            json_str = script.string.split(' = ')[1].rstrip(';')
                            json_data = json.loads(json_str)
                            break
                    
                    if json_data:
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
                            'is_verified': user_data.get('is_verified', False),
                            'profile_pic_url': user_data.get('profile_pic_url_hd', user_data.get('profile_pic_url', 'N/A')),
                            'account_type': 'personal' if not user_data.get('is_business_account', False) else 'business',
                            'business_category': user_data.get('business_category_name', 'N/A'),
                            'connected_fb_page': user_data.get('connected_fb_page', {}).get('username', 'N/A') if user_data.get('connected_fb_page') else 'N/A',
                            'has_highlight_reels': user_data.get('has_highlight_reels', False),
                            'total_igtv_videos': user_data.get('edge_felix_video_timeline', {}).get('count', 0)
                        }
                        
                        # Extract location information
                        if user_data.get('address_json'):
                            try:
                                location_data = json.loads(user_data['address_json'])
                                instagram_info['location'] = {
                                    'city': location_data.get('city', 'N/A'),
                                    'country': location_data.get('country', 'N/A'),
                                    'zip_code': location_data.get('zip', 'N/A')
                                }
                            except:
                                pass
                        
                        # Extract contact information (only if publicly shared)
                        if user_data.get('contact_method_button_text'):
                            instagram_info['contact_button'] = user_data['contact_method_button_text']
                        
                        self.results['instagram'] = instagram_info
                        print(f"[+] Instagram data collected successfully")
                        
                        # Extract recent posts with enhanced metadata
                        posts = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
                        recent_posts = []
                        
                        for i, post in enumerate(posts[:15]):  # Get last 15 posts
                            node = post.get('node', {})
                            post_info = {
                                'shortcode': node.get('shortcode', 'N/A'),
                                'url': f"https://www.instagram.com/p/{node.get('shortcode', '')}/",
                                'caption': node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', 'N/A'),
                                'timestamp': node.get('taken_at_timestamp', 'N/A'),
                                'likes': node.get('edge_media_preview_like', {}).get('count', 0),
                                'comments': node.get('edge_media_to_comment', {}).get('count', 0),
                                'is_video': node.get('is_video', False),
                                'is_carousel': node.get('is_carousel', False),
                                'location': node.get('location', {}).get('name', 'N/A') if node.get('location') else 'N/A',
                                'tagged_users': [tag.get('node', {}).get('username', 'N/A') for tag in node.get('edge_media_to_tagged_user', {}).get('edges', [])],
                                'hashtags': re.findall(r'#(\w+)', node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''))
                            }
                            recent_posts.append(post_info)
                        
                        self.results['instagram']['recent_posts'] = recent_posts
                        break  # Success, exit the loop
                        
                    else:
                        print(f"[-] Could not extract JSON data from Instagram page")
                        
                elif response.status_code == 404:
                    print(f"[-] Instagram profile not found (HTTP 404)")
                    self.results['instagram'] = {'error': 'Profile not found'}
                    break
                    
                else:
                    print(f"[-] Instagram access issue (HTTP {response.status_code})")
                    
            except Exception as e:
                print(f"[-] Instagram reconnaissance attempt failed: {str(e)}")
                continue
        
        # If no success, set error
        if 'instagram' not in self.results:
            self.results['instagram'] = {'error': 'Failed to extract data after multiple attempts'}
            
        self.random_delay()
    
    def tiktok_recon(self, username):
        """Enhanced TikTok reconnaissance with comprehensive user data"""
        print(f"[+] TikTok reconnaissance for: {username}")
        
        # Multiple approaches for TikTok data extraction
        urls_to_try = [
            f"https://www.tiktok.com/@{username}",
            f"https://www.tiktok.com/@{username}/video"
        ]
        
        for url in urls_to_try:
            try:
                print(f"[*] Trying: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Method 1: Look for TikTok API data in script tags
                    script_tags = soup.find_all('script')
                    json_data = None
                    
                    for script in script_tags:
                        if script.string and '__DEFAULT_SCOPE__' in script.string:
                            try:
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
                            'profile_pic_url': user_data.get('avatarLarger', user_data.get('avatarMedium', 'N/A')),
                            'account_created': user_data.get('createTime', 'N/A'),
                            'sec_uid': user_data.get('secUid', 'N/A'),
                            'is_business_account': user_data.get('isBusinessAccount', False)
                        }
                        
                        # Extract location and contact info if available
                        if user_data.get('region'):
                            tiktok_info['region'] = user_data['region']
                        
                        if user_data.get('contactInfo'):
                            tiktok_info['contact_info'] = user_data['contactInfo']
                        
                        # Extract video information
                        videos = user_data.get('aweme_list', [])[:15]  # Get last 15 videos
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
                                'has_location': video.get('poi', {}) != {},
                                'is_duet': video.get('is_duet', False),
                                'is_stitch': video.get('is_stitch', False),
                                'hashtags': [tag.get('hashtag_name', '') for tag in video.get('text_extra', [])]
                            }
                            recent_videos.append(video_info)
                        
                        tiktok_info['recent_videos'] = recent_videos
                        self.results['tiktok'] = tiktok_info
                        print(f"[+] TikTok data collected successfully")
                        break
                        
                    else:
                        print(f"[-] Could not extract TikTok user data")
                        
                elif response.status_code == 404:
                    print(f"[-] TikTok profile not found (HTTP 404)")
                    self.results['tiktok'] = {'error': 'Profile not found'}
                    break
                    
                else:
                    print(f"[-] TikTok access issue (HTTP {response.status_code})")
                    
            except Exception as e:
                print(f"[-] TikTok reconnaissance attempt failed: {str(e)}")
                continue
        
        # If no success, set error
        if 'tiktok' not in self.results:
            self.results['tiktok'] = {'error': 'Failed to extract data after multiple attempts'}
            
        self.random_delay()
    
    def facebook_recon(self, username):
        """Enhanced Facebook reconnaissance with comprehensive public data"""
        print(f"[+] Facebook reconnaissance for: {username}")
        
        # Multiple approaches for Facebook data extraction
        urls_to_try = [
            f"https://www.facebook.com/{username}",
            f"https://www.facebook.com/{username}/about"
        ]
        
        for url in urls_to_try:
            try:
                print(f"[*] Trying: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html_parser')
                    
                    # Extract basic information from HTML
                    facebook_info = {
                        'username': username,
                        'profile_url': url,
                        'page_title': soup.find('title').get_text().strip() if soup.find('title') else 'N/A',
                        'meta_description': '',
                        'public_posts': [],
                        'about_section': '',
                        'photos': [],
                        'friends': [],
                        'likes': []
                    }
                    
                    # Extract meta description
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc:
                        facebook_info['meta_description'] = meta_desc.get('content', 'N/A')
                    
                    # Extract about section information
                    about_section = soup.find('div', {'id': 'pagelet_timeline_profile_actions'})
                    if about_section:
                        facebook_info['about_section'] = about_section.get_text().strip()
                    
                    # Look for public posts
                    post_elements = soup.find_all('div', class_='userContent')
                    public_posts = []
                    
                    for i, post in enumerate(post_elements[:10]):  # Get last 10 posts
                        post_text = post.get_text().strip()
                        if post_text and len(post_text) > 20:  # Only substantial posts
                            post_info = {
                                'content': post_text[:300] + '...' if len(post_text) > 300 else post_text,
                                'timestamp': 'N/A',
                                'likes': 'N/A',
                                'comments': 'N/A'
                            }
                            public_posts.append(post_info)
                    
                    facebook_info['public_posts'] = public_posts
                    
                    # Extract photos information
                    photo_elements = soup.find_all('a', href=re.compile(r'/photos/'))
                    photos = []
                    for photo in photo_elements[:10]:
                        photo_url = photo.get('href', '')
                        if photo_url and 'photo' in photo_url:
                            photos.append(photo_url)
                    
                    facebook_info['photos'] = photos
                    
                    # Extract interests and likes
                    like_elements = soup.find_all('a', href=re.compile(r'/pages/'))
                    likes = []
                    for like in like_elements[:15]:
                        like_text = like.get_text().strip()
                        if like_text and len(like_text) > 3:
                            likes.append(like_text)
                    
                    facebook_info['likes'] = likes
                    
                    self.results['facebook'] = facebook_info
                    print(f"[+] Facebook data collected successfully")
                    break
                    
                elif response.status_code == 404:
                    print(f"[-] Facebook profile not found (HTTP 404)")
                    self.results['facebook'] = {'error': 'Profile not found'}
                    break
                    
                else:
                    print(f"[-] Facebook access issue (HTTP {response.status_code})")
                    
            except Exception as e:
                print(f"[-] Facebook reconnaissance attempt failed: {str(e)}")
                continue
        
        # If no success, set error
        if 'facebook' not in self.results:
            self.results['facebook'] = {'error': 'Failed to extract data after multiple attempts'}
            
        self.random_delay()
    
    def enhanced_cross_platform_search(self, username):
        """Enhanced cross-platform username search with more platforms"""
        print(f"[+] Enhanced cross-platform username search for: {username}")
        
        # Expanded list of platforms to check
        platforms = [
            # Major social media
            'instagram.com', 'tiktok.com', 'facebook.com', 'twitter.com', 'linkedin.com',
            # Development and professional
            'github.com', 'gitlab.com', 'stackoverflow.com', 'dribbble.com', 'behance.net',
            # Content creation
            'youtube.com', 'vimeo.com', 'soundcloud.com', 'spotify.com', 'bandcamp.com',
            # Gaming
            'twitch.tv', 'steamcommunity.com', 'battle.net', 'epic.games.com',
            # Photography and art
            'flickr.com', 'deviantart.com', 'pinterest.com', '500px.com',
            # Blogging and publishing
            'medium.com', 'wordpress.com', 'tumblr.com', 'reddit.com',
            # Communication
            'discord.com', 'telegram.org', 'signal.org', 'wa.me',
            # Other platforms
            'pinterest.com', 'quora.com', 'imgur.com', 'fiverr.com', 'upwork.com'
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
            
            # Random delay to avoid detection
            self.random_delay(min_delay=0.3, max_delay=1.0)
        
        self.results['cross_platform'] = found_platforms
        found_count = len([p for p in found_platforms.values() if p['status'] == 'found'])
        print(f"[+] Cross-platform search completed. Found on {found_count} platforms")
    
    def display_search_results(self):
        """Enhanced display of search results with formatting"""
        print("\n" + "="*80)
        print("SOCMINT INTELLIGENCE REPORT".center(80))
        print("="*80)
        print(f"TARGET USERNAME: {self.target_username}".center(80))
        print(f"GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
        print("="*80)
        
        # Display Instagram Results
        if 'instagram' in self.results:
            print("\n" + "INSTAGRAM ANALYSIS".center(80))
            print("-"*80)
            instagram_data = self.results['instagram']
            
            if 'error' in instagram_data:
                print(f"❌ Error: {instagram_data['error']}")
            else:
                print(f"👤 Username: {instagram_data.get('username', 'N/A')}")
                print(f"📝 Full Name: {instagram_data.get('full_name', 'N/A')}")
                print(f"📄 Biography: {instagram_data.get('biography', 'N/A')}")
                print(f"🔗 External URL: {instagram_data.get('external_url', 'N/A')}")
                print(f"👥 Followers: {instagram_data.get('followers', 0):,}")
                print(f"👫 Following: {instagram_data.get('following', 0):,}")
                print(f"📸 Posts: {instagram_data.get('posts', 0):,}")
                print(f"🔒 Private Account: {'Yes' if instagram_data.get('is_private', False) else 'No'}")
                print(f"✅ Verified: {'Yes' if instagram_data.get('is_verified', False) else 'No'}")
                print(f"💼 Account Type: {instagram_data.get('account_type', 'N/A')}")
                
                if instagram_data.get('location'):
                    loc = instagram_data['location']
                    print(f"📍 Location: {loc.get('city', 'N/A')}, {loc.get('country', 'N/A')}")
                
                if instagram_data.get('business_category'):
                    print(f"🏢 Business Category: {instagram_data['business_category']}")
                
                if instagram_data.get('recent_posts'):
                    print(f"\n📱 Recent Posts (Last 5):")
                    for i, post in enumerate(instagram_data['recent_posts'][:5]):
                        print(f"  {i+1}. {post.get('caption', 'No caption')[:100]}...")
                        print(f"     👍 {post.get('likes', 0)} likes | 💬 {post.get('comments', 0)} comments")
                        print(f"     🔗 {post.get('url', 'N/A')}")
                        print()
        
        # Display TikTok Results
        if 'tiktok' in self.results:
            print("\n" + "TIKTOK ANALYSIS".center(80))
            print("-"*80)
            tiktok_data = self.results['tiktok']
            
            if 'error' in tiktok_data:
                print(f"❌ Error: {tiktok_data['error']}")
            else:
                print(f"👤 Username: {tiktok_data.get('username', 'N/A')}")
                print(f"🎵 Nickname: {tiktok_data.get('nickname', 'N/A')}")
                print(f"📄 Bio: {tiktok_data.get('bio', 'N/A')}")
                print(f"👥 Followers: {tiktok_data.get('followers', 0):,}")
                print(f"👫 Following: {tiktok_data.get('following', 0):,}")
                print(f"❤️ Likes: {tiktok_data.get('likes', 0):,}")
                print(f"🎥 Videos: {tiktok_data.get('videos', 0):,}")
                print(f"🔒 Private Account: {'Yes' if tiktok_data.get('is_private', False) else 'No'}")
                print(f"✅ Verified: {'Yes' if tiktok_data.get('is_verified', False) else 'No'}")
                
                if tiktok_data.get('region'):
                    print(f"🌍 Region: {tiktok_data['region']}")
                
                if tiktok_data.get('recent_videos'):
                    print(f"\n🎬 Recent Videos (Last 5):")
                    for i, video in enumerate(tiktok_data['recent_videos'][:5]):
                        print(f"  {i+1}. {video.get('title', 'No title')[:100]}...")
                        print(f"     👁️ {video.get('play_count', 0):,} views | ❤️ {video.get('digg_count', 0):,} likes")
                        print(f"     💬 {video.get('comment_count', 0):,} comments | 🔄 {video.get('share_count', 0):,} shares")
                        print()
        
        # Display Facebook Results
        if 'facebook' in self.results:
            print("\n" + "FACEBOOK ANALYSIS".center(80))
            print("-"*80)
            facebook_data = self.results['facebook']
            
            if 'error' in facebook_data:
                print(f"❌ Error: {facebook_data['error']}")
            else:
                print(f"👤 Username: {facebook_data.get('username', 'N/A')}")
                print(f"📄 Page Title: {facebook_data.get('page_title', 'N/A')}")
                print(f"📝 Meta Description: {facebook_data.get('meta_description', 'N/A')}")
                print(f"📸 Photos Available: {'Yes' if facebook_data.get('photos') else 'No'}")
                print(f"👥 Interests/Likes: {len(facebook_data.get('likes', []))} found")
                
                if facebook_data.get('about_section'):
                    print(f"📋 About Section: {facebook_data['about_section'][:200]}...")
                
                if facebook_data.get('public_posts'):
                    print(f"\n📱 Public Posts (Last 3):")
                    for i, post in enumerate(facebook_data['public_posts'][:3]):
                        print(f"  {i+1}. {post.get('content', 'No content')[:150]}...")
                        print()
        
        # Display Cross-Platform Results
        if 'cross_platform' in self.results:
            print("\n" + "CROSS-PLATFORM ANALYSIS".center(80))
            print("-"*80)
            cross_data = self.results['cross_platform']
            
            found_platforms = [p for p in cross_data.values() if p['status'] == 'found']
            redirect_platforms = [p for p in cross_data.values() if p['status'] == 'redirect']
            
            print(f"✅ Found on {len(found_platforms)} platforms:")
            for platform, data in cross_data.items():
                if data['status'] == 'found':
                    print(f"  • {platform}")
                elif data['status'] == 'redirect':
                    print(f"  • {platform} → {data.get('redirect_url', 'N/A')}")
            
            print(f"\n🔄 Redirects on {len(redirect_platforms)} platforms:")
            for platform, data in cross_data.items():
                if data['status'] == 'redirect':
                    print(f"  • {platform}")
        
        # Summary Statistics
        print("\n" + "INTELLIGENCE SUMMARY".center(80))
        print("-"*80)
        
        total_platforms = len([k for k in self.results.keys() if k != 'cross_platform'])
        total_findings = 0
        
        for platform, data in self.results.items():
            if platform != 'cross_platform' and isinstance(data, dict) and 'error' not in data:
                if platform == 'instagram':
                    total_findings += sum([
                        1 if data.get(key) else 0 
                        for key in ['full_name', 'biography', 'external_url', 'business_category', 'location']
                    ])
                elif platform == 'tiktok':
                    total_findings += sum([
                        1 if data.get(key) else 0 
                        for key in ['nickname', 'bio', 'region', 'contact_info']
                    ])
                elif platform == 'facebook':
                    total_findings += len(data.get('public_posts', [])) + len(data.get('likes', []))
        
        cross_found = len([p for p in self.results.get('cross_platform', {}).values() if p['status'] == 'found'])
        
        print(f"📊 Platforms Analyzed: {total_platforms}")
        print(f"🔍 Total Findings: {total_findings}")
        print(f"🌐 Cross-Platform Matches: {cross_found}")
        print(f"📊 Digital Footprint Score: {min(100, (cross_found * 10) + (total_findings * 2))}/100")
        
        risk_level = "Low"
        if min(100, (cross_found * 10) + (total_findings * 2)) > 70:
            risk_level = "High"
        elif min(100, (cross_found * 10) + (total_findings * 2)) > 40:
            risk_level = "Medium"
        
        print(f"⚠️  Risk Assessment: {risk_level}")
        print("="*80)
    
    def generate_enhanced_report(self, output_format='json'):
        """Generate enhanced comprehensive report with analysis"""
        if not self.results:
            print("[-] No data to generate report")
            return
        
        report = {
            'target': self.target_username,
            'timestamp': datetime.now().isoformat(),
            'data': self.results,
            'analysis': {
                'platforms_analyzed': len([k for k in self.results.keys() if k != 'cross_platform']),
                'total_findings': 0,
                'digital_footprint_score': 0,
                'activity_patterns': {},
                'risk_assessment': 'Low'
            }
        }
        
        # Calculate enhanced summary statistics
        for platform, data in self.results.items():
            if platform != 'cross_platform' and isinstance(data, dict) and 'error' not in data:
                if platform == 'instagram':
                    findings = sum([
                        1 if data.get(key) else 0 
                        for key in ['full_name', 'biography', 'external_url', 'business_category', 'location']
                    ])
                    report['analysis']['total_findings'] += findings
                    
                    # Activity pattern analysis
                    posts = data.get('recent_posts', [])
                    if posts:
                        times = [post.get('timestamp', 0) for post in posts if post.get('timestamp')]
                        if times:
                            # Simple activity analysis
                            report['analysis']['activity_patterns'][platform] = {
                                'total_posts': len(posts),
                                'avg_likes': sum(p.get('likes', 0) for p in posts) / len(posts),
                                'has_location': any(p.get('location') for p in posts)
                            }
                
                elif platform == 'tiktok':
                    findings = sum([
                        1 if data.get(key) else 0 
                        for key in ['nickname', 'bio', 'region', 'contact_info']
                    ])
                    report['analysis']['total_findings'] += findings
                    
                    # Activity pattern analysis
                    videos = data.get('recent_videos', [])
                    if videos:
                        report['analysis']['activity_patterns'][platform] = {
                            'total_videos': len(videos),
                            'avg_views': sum(v.get('play_count', 0) for v in videos) / len(videos),
                            'has_music': any(v.get('has_music') for v in videos)
                        }
                
                elif platform == 'facebook':
                    findings = len(data.get('public_posts', [])) + len(data.get('likes', []))
                    report['analysis']['total_findings'] += findings
                    
                    # Activity pattern analysis
                    posts = data.get('public_posts', [])
                    likes = data.get('likes', [])
                    report['analysis']['activity_patterns'][platform] = {
                        'total_posts': len(posts),
                        'total_likes': len(likes),
                        'has_photos': len(data.get('photos', [])) > 0
                    }
        
        # Calculate digital footprint score
        cross_found = len([p for p in self.results.get('cross_platform', {}).values() if p['status'] == 'found'])
        report['analysis']['digital_footprint_score'] = min(100, (cross_found * 10) + (report['analysis']['total_findings'] * 2))
        
        # Risk assessment
        if report['analysis']['digital_footprint_score'] > 70:
            report['analysis']['risk_assessment'] = 'High'
        elif report['analysis']['digital_footprint_score'] > 40:
            report['analysis']['risk_assessment'] = 'Medium'
        
        # Save enhanced report
        if output_format.lower() == 'json':
            filename = f"enhanced_socint_report_{self.target_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"[+] Enhanced report saved as: {filename}")
        
        elif output_format.lower() == 'csv':
            filename = f"enhanced_socint_report_{self.target_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Platform', 'Field', 'Value'])
                
                for platform, data in self.results.items():
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, (list, dict)):
                                continue
                            writer.writerow([platform, key, str(value)])
            
            print(f"[+] Enhanced report saved as: {filename}")

def main():
    parser = argparse.ArgumentParser(
        description='Enhanced SOCMINT Tool - Comprehensive Public Intelligence Collection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enhanced_socint_tool.py -u target_user
  python enhanced_socint_tool.py -u target_user --platforms instagram,tiktok
  python enhanced_socint_tool.py -u target_user --cross-platform
  python enhanced_socint_tool.py -u target_user --output json
  python enhanced_socint_tool.py -u target_user --output csv --verbose
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
    parser.add_argument('--timeout', type=int, default=15, 
                       help='Request timeout in seconds (default: 15)')
    parser.add_argument('--delay', type=float, default=1.0, 
                       help='Base delay between requests in seconds (default: 1.0)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Initialize tool
    tool = EnhancedSOCMINTTool()
    tool.target_username = args.username
    tool.request_delay = args.delay
    
    print(f"[*] Starting Enhanced SOCMINT investigation for: {args.username}")
    print(f"[*] Platforms: {', '.join(args.platforms)}")
    print(f"[*] Output format: {args.output}")
    print(f"[*] Cross-platform search: {'Enabled' if args.cross_platform else 'Disabled'}")
    
    # Set session timeout
    tool.session.timeout = args.timeout
    
    if args.verbose:
        print(f"[*] Request timeout: {args.timeout}s")
        print(f"[*] Base request delay: {args.delay}s")
    
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
    
    # Perform enhanced cross-platform search if requested
    if args.cross_platform:
        tool.enhanced_cross_platform_search(args.username)
    
    # Display enhanced search results
    tool.display_search_results()
    
    # Generate enhanced report
    tool.generate_enhanced_report(args.output)
    
    print(f"\n[*] Enhanced SOCMINT investigation completed for: {args.username}")

if __name__ == "__main__":
    main()
