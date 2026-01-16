    # Initialize session with better headers
    self.session = requests.Session()
    
    # Rotate user agents to avoid detection
    self.user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0'
    ]
    
    # Set security-focused headers
    self.session.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    })
    
    self.results: Dict[str, Any] = {}
    self.target_username: str = ""
    self.max_retries: int = 3
    self.base_delay: float = 2.0
    
def get_random_user_agent(self) -> str:
    """Get a random user agent"""
    return random.choice(self.user_agents)

def validate_url(self, url: str) -> bool:
    """Validate URL format and security"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def make_request(self, url: str, timeout: int = 15, max_retries: Optional[int] = None) -> requests.Response:
    """Make HTTP request with retry logic and security checks"""
    if not self.validate_url(url):
        raise ValueError(f"Invalid URL: {url}")
        
    if max_retries is None:
        max_retries = self.max_retries
        
    user_agent = self.get_random_user_agent()
    headers = self.session.headers.copy()
    headers['User-Agent'] = user_agent
    
    for attempt in range(max_retries):
        try:
            self.logger.info(f"Attempt {attempt + 1}/{max_retries} for URL: {url}")
            
            response = self.session.get(
                url, 
                headers=headers, 
                timeout=timeout,
                allow_redirects=False
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                self.logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                continue
                
            # Handle server errors
            if 500 <= response.status_code < 600:
                wait_time = (attempt + 1) * 2
                self.logger.warning(f"Server error {response.status_code}. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            
            return response
            
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Request failed (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 3
                self.logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                raise e
    
    raise Exception(f"Failed after {max_retries} attempts")

def extract_json_from_script(self, soup: BeautifulSoup, key: str) -> Optional[Dict]:
    """Extract JSON data from script tags with security checks"""
    script_tags = soup.find_all('script')
    
    for script in script_tags:
        if script.string and key in script.string:
            try:
                # Extract JSON string
                json_str = script.string.split(key + '=')[1].split(';')[0]
                # Clean up the JSON string
                json_str = json_str.strip()
                if json_str.startswith('{') and json_str.endswith('}'):
                    return json.loads(json_str)
            except Exception as e:
                self.logger.warning(f"Failed to extract JSON: {str(e)}")
                continue
    
    return None

def instagram_recon(self, username: str) -> None:
    """Enhanced Instagram reconnaissance with better error handling"""
    self.logger.info(f"Instagram reconnaissance for: {username}")
    
    # Validate username
    if not re.match(r'^[a-zA-Z0-9._]{1,30}$', username):
        self.logger.error(f"Invalid Instagram username format: {username}")
        self.results['instagram'] = {'error': 'Invalid username format'}
        return
    
    # Multiple approaches for better data extraction
    urls_to_try = [
        f"https://www.instagram.com/{username}/",
        f"https://www.instagram.com/{username}/?__a=1"
    ]
    
    for url in urls_to_try:
        try:
            self.logger.info(f"Trying: {url}")
            response = self.make_request(url, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Method 1: Extract from shared data
                json_data = self.extract_json_from_script(soup, 'window._sharedData')
                
                if json_data:
                    try:
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
                        
                        self.results['instagram'] = instagram_info
                        self.logger.info("Instagram data collected successfully")
                        
                        # Extract recent posts
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
                                'is_carousel': node.get('is_carousel', False),
                                'location': node.get('location', {}).get('name', 'N/A') if node.get('location') else 'N/A',
                                'tagged_users': [tag.get('node', {}).get('username', 'N/A') for tag in node.get('edge_media_to_tagged_user', {}).get('edges', [])],
                                'hashtags': re.findall(r'#(\w+)', node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''))
                            }
                            recent_posts.append(post_info)
                        
                        instagram_info['recent_posts'] = recent_posts
                        break
                        
                    except Exception as e:
                        self.logger.error(f"Error processing Instagram data: {str(e)}")
                        continue
                
                else:
                    self.logger.warning("Could not extract JSON data from Instagram page")
                    
            elif response.status_code == 404:
                self.logger.warning(f"Instagram profile not found (HTTP 404)")
                self.results['instagram'] = {'error': 'Profile not found'}
                break
                
            else:
                self.logger.warning(f"Instagram access issue (HTTP {response.status_code})")
                
        except Exception as e:
            self.logger.error(f"Instagram reconnaissance failed: {str(e)}")
            continue
    
    # If no success, set error
    if 'instagram' not in self.results:
        self.results['instagram'] = {'error': 'Failed to extract data after multiple attempts'}
        
    # Random delay to avoid rate limiting
    time.sleep(random.uniform(1, 3))

def tiktok_recon(self, username: str) -> None:
    """Enhanced TikTok reconnaissance with better error handling"""
    self.logger.info(f"TikTok reconnaissance for: {username}")
    
    # Validate username format
    if not re.match(r'^[a-zA-Z0-9._]{1,24}$', username):
        self.logger.error(f"Invalid TikTok username format: {username}")
        self.results['tiktok'] = {'error': 'Invalid username format'}
        return
    
    # Multiple approaches for TikTok data extraction
    urls_to_try = [
        f"https://www.tiktok.com/@{username}",
        f"https://www.tiktok.com/@{username}/video"
    ]
    
    for url in urls_to_try:
        try:
            self.logger.info(f"Trying: {url}")
            response = self.make_request(url, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Method 1: Look for TikTok API data in script tags
                json_data = self.extract_json_from_script(soup, '__DEFAULT_SCOPE__')
                
                if json_data:
                    try:
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
                                'has_location': video.get('poi', {}) != {},
                                'is_duet': video.get('is_duet', False),
                                'is_stitch': video.get('is_stitch', False),
                                'hashtags': [tag.get('hashtag_name', '') for tag in video.get('text_extra', [])]
                            }
                            recent_videos.append(video_info)
                        
                        tiktok_info['recent_videos'] = recent_videos
                        self.results['tiktok'] = tiktok_info
                        self.logger.info("TikTok data collected successfully")
                        break
                        
                    except Exception as e:
                        self.logger.error(f"Error processing TikTok data: {str(e)}")
                        continue
                
                else:
                    self.logger.warning("Could not extract TikTok user data")
                    
            elif response.status_code == 404:
                self.logger.warning(f"TikTok profile not found (HTTP 404)")
                self.results['tiktok'] = {'error': 'Profile not found'}
                break
                
            else:
                self.logger.warning(f"TikTok access issue (HTTP {response.status_code})")
                
        except Exception as e:
            self.logger.error(f"TikTok reconnaissance failed: {str(e)}")
            continue
    
    # If no success, set error
    if 'tiktok' not in self.results:
        self.results['tiktok'] = {'error': 'Failed to extract data after multiple attempts'}
        
    # Random delay to avoid rate limiting
    time.sleep(random.uniform(1, 3))

def facebook_recon(self, username: str) -> None:
    """Enhanced Facebook reconnaissance with better error handling"""
    self.logger.info(f"Facebook reconnaissance for: {username}")
    
    # Validate username format
    if not re.match(r'^[a-zA-Z0-9._]{1,50}$', username):
        self.logger.error(f"Invalid Facebook username format: {username}")
        self.results['facebook'] = {'error': 'Invalid username format'}
        return
    
    # Multiple approaches for Facebook data extraction
    urls_to_try = [
        f"https://www.facebook.com/{username}",
        f"https://www.facebook.com/{username}/about"
    ]
    
    for url in urls_to_try:
        try:
            self.logger.info(f"Trying: {url}")
            response = self.make_request(url, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
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
                
                for i, post in enumerate(post_elements[:5]):  # Get last 5 public posts
                    post_text = post.get_text().strip()
                    if post_text and len(post_text) > 20:  # Only substantial posts
                        post_info = {
                            'content': post_text[:200] + '...' if len(post_text) > 200 else post_text,
                            'timestamp': 'N/A',
                            'likes': 'N/A',
                            'comments': 'N/A'
                        }
                        public_posts.append(post_info)
                
                facebook_info['public_posts'] = public_posts
                
                # Extract photos information
                photo_elements = soup.find_all('a', href=re.compile(r'/photos/'))
                photos = []
                for photo in photo_elements[:5]:
                    photo_url = photo.get('href', '')
                    if photo_url and 'photo' in photo_url:
                        photos.append(photo_url)
                
                facebook_info['photos'] = photos
                
                # Extract interests and likes
                like_elements = soup.find_all('a', href=re.compile(r'/pages/'))
                likes = []
                for like in like_elements[:10]:
                    like_text = like.get_text().strip()
                    if like_text and len(like_text) > 3:
                        likes.append(like_text)
                
                facebook_info['likes'] = likes
                
                self.results['facebook'] = facebook_info
                self.logger.info("Facebook data collected successfully")
                break
                
            elif response.status_code == 404:
                self.logger.warning(f"Facebook profile not found (HTTP 404)")
                self.results['facebook'] = {'error': 'Profile not found'}
                break
                
            else:
                self.logger.warning(f"Facebook access issue (HTTP {response.status_code})")
                
        except Exception as e:
            self.logger.error(f"Facebook reconnaissance failed: {str(e)}")
            continue
    
    # If no success, set error
    if 'facebook' not in self.results:
        self.results['facebook'] = {'error': 'Failed to extract data after multiple attempts'}
        
    # Random delay to avoid rate limiting
    time.sleep(random.uniform(1, 3))

def enhanced_cross_platform_search(self, username: str) -> None:
    """Enhanced cross-platform username search with better error handling"""
    self.logger.info(f"Enhanced cross-platform username search for: {username}")
    
    # Validate username
    if not username or len(username) < 1 or len(username) > 50:
        self.logger.error("Invalid username length")
        return
    
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
            response = self.make_request(url, timeout=10, max_retries=2)
            
            # Check if username exists on platform
            if response.status_code == 200:
                found_platforms[platform] = {
                    'url': url,
                    'status': 'found',
                    'http_status': response.status_code
                }
                self.logger.info(f"Found on {platform}")
            elif response.status_code == 302:
                found_platforms[platform] = {
                    'url': url,
                    'status': 'redirect',
                    'http_status': response.status_code,
                    'redirect_url': response.headers.get('Location', 'N/A')
                }
                self.logger.info(f"Redirect found on {platform}")
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
        time.sleep(random.uniform(0.5, 1.5))
    
    self.results['cross_platform'] = found_platforms
    found_count = len([p for p in found_platforms.values() if p['status'] == 'found'])
    self.logger.info(f"Cross-platform search completed. Found on {found_count} platforms")

def display_search_results(self) -> None:
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
        error_platforms = [p for p in cross_data.values() if p['status'] == 'error']
        
        print(f"✅ Found on {len(found_platforms)} platforms:")
        for platform, data in cross_data.items():
            if data['status'] == 'found':
                print(f"  • {platform}")
            elif data['status'] == 'redirect':
                print(f"  • {platform} → {data.get('redirect_url', 'N/A')[:50]}...")
        
        print(f"\n🔄 Redirects on {len(redirect_platforms)} platforms:")
        for platform, data in cross_data.items():
            if data['status'] == 'redirect':
                print(f"  • {platform}")
        
        if error_platforms:
            print(f"\n❌ Errors on {len(error_platforms)} platforms:")
            for platform, data in cross_data.items():
                if data['status'] == 'error':
                    print(f"  • {platform}: {data.get('error', 'Unknown error')}")
    
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

def generate_enhanced_report(self, output_format: str = 'json') -> None:
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
        filename = f"robust_socint_report_{self.target_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"[+] Enhanced report saved as: {filename}")
    
    elif output_format.lower() == 'csv':
        filename = f"robust_socint_report_{self.target_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
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
