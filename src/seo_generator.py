import os
import re
from openai import OpenAI
import json
try:
    from .logger import logger
except ImportError:
    from logger import logger

def clean_filename(filename):
    # Remove extension and replace underscores/hyphens with spaces
    name_without_ext = os.path.splitext(filename)[0]
    cleaned = re.sub(r'[-_]', ' ', name_without_ext)
    return cleaned.strip()

def generate_seo_metadata(filename, media_type='reel'):
    """
    Generates SEO title, description, and hashtags based on the video filename.
    Optimized for US audience with English content.
    Returns a dictionary with 'title', 'description', and 'hashtags'.
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.warning("OPENAI_API_KEY not found. Using fallback metadata generator.")
        return generate_fallback_metadata(filename)
        
    base_url = os.environ.get('OPENAI_API_BASE_URL')
    model = os.environ.get('OPENAI_API_MODEL', 'gpt-3.5-turbo')
    
    if base_url:
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=api_key)
        
    topic = clean_filename(filename)
    
    content_type_str = "Facebook Reel" if media_type == 'reel' else "Facebook Photo Post"
    video_str = "short vertical video (Facebook Reel / YouTube Shorts)" if media_type == 'reel' else "stunning photo/image"
    hashtag_str = "#Reels #viral" if media_type == 'reel' else "#PhotoOfTheDay #viral"
    
    system_prompt = (
        "You are an expert Social Media Manager specializing in viral content for Facebook and YouTube Shorts "
        "targeting a United States audience. "
        "Your goal is to maximize engagement, click-through rate, and virality among American viewers. "
        "All generated titles, descriptions, and hashtags must be in English. "
        "Use emotionally engaging words, curiosity gaps, and trending formats popular on US social media."
    )
    
    user_prompt = f"""
    Generate viral SEO metadata for a {video_str} about: "{topic}".
    
    Requirements:
    1. Title: Short, catchy, uses emotional words, includes relevant emojis. Written in English. Max 60 characters.
    2. Description: 1-2 short sentences in English that create curiosity and encourage engagement. Use American English.
    3. Hashtags: 5-8 highly relevant and trending hashtags for US audience. Mix viral tags with topic-specific tags. Include {hashtag_str}.
    
    US Audience Hashtag Guidelines:
    - Always include popular US viral tags: #viral #trending #fyp #foryou #explore #reels #shorts
    - Add topic-specific tags where relevant
    - Use English hashtags for maximum reach in the US market
    
    Format the output exactly as JSON:
    {{
        "title": "...",
        "description": "...",
        "hashtags": "#tag1 #tag2 ..."
    }}
    """
    
    try:
        params = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "timeout": 45.0
        }
        if "gpt-" in model:
            params["response_format"] = {"type": "json_object"}
            
        response = client.chat.completions.create(**params)
        
        result_json = response.choices[0].message.content.strip()
        
        # Clean markdown code blocks if present
        if result_json.startswith("```"):
            result_json = re.sub(r'^```(?:json)?\n', '', result_json)
            result_json = re.sub(r'\n```$', '', result_json)
            result_json = result_json.strip()
            
        data = json.loads(result_json)
        
        return {
            'title': data.get('title', topic.title()),
            'description': data.get('description', f"Incredible video about {topic}! Must see!"),
            'hashtags': data.get('hashtags', "#viral #trending #reels #shorts #fyp #foryou")
        }
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return generate_fallback_metadata(filename)

def generate_fallback_metadata(filename):
    import hashlib
    
    def get_deterministic_choice(fn, lst):
        h = int(hashlib.md5(fn.encode('utf-8')).hexdigest(), 16)
        return lst[h % len(lst)]
        
    topic = clean_filename(filename)
    topic_title = topic.title()
    
    # Extract lowercase words for keyword matching
    words = [w.lower() for w in re.findall(r'\w+', topic) if len(w) > 2]
    
    # Define stopwords
    stopwords = {
        'the', 'and', 'for', 'you', 'with', 'from', 'this', 'that',
        'are', 'was', 'were', 'has', 'have', 'had', 'its', 'their', 'our',
        'your', 'his', 'her', 'she', 'him', 'them', 'who', 'whom', 'which'
    }
    
    keywords = [w for w in words if w not in stopwords]
    
    # Classify category
    wildlife_keywords = {
        'tiger', 'lion', 'leopard', 'cheetah', 'gorilla', 'elephant', 'shark', 'whale',
        'bear', 'eagle', 'hawk', 'snake', 'hunt', 'predator', 'safari', 'animal', 'wolf',
        'panther', 'jaguar', 'buffalo', 'crocodile', 'alligator'
    }
    
    nature_keywords = {
        'nature', 'forest', 'jungle', 'ocean', 'river', 'mountain', 'sea', 'sky',
        'rain', 'storm', 'scenic', 'landscape', 'valley', 'desert', 'beach', 'sunset',
        'sunrise', 'lake', 'waterfall', 'canyon'
    }
    
    culture_keywords = {
        'chinese', 'china', 'beijing', 'shanghai', 'temple', 'kungfu', 'martial',
        'dragon', 'lantern', 'tea', 'silk', 'wall', 'panda', 'dumpling', 'noodle',
        'dance', 'music', 'opera', 'calligraphy', 'painting', 'festival', 'newyear',
        'spring', 'autumn', 'ancient', 'traditional', 'culture', 'hanfu', 'cheongsam'
    }
    
    food_keywords = {
        'food', 'cooking', 'recipe', 'chef', 'kitchen', 'bake', 'grill', 'bbq',
        'noodle', 'dumpling', 'rice', 'wok', 'stir', 'soup', 'hotpot', 'dimsum',
        'sushi', 'ramen', 'fried', 'steamed', 'spicy', 'sweet'
    }
    
    craft_keywords = {
        'craft', 'diy', 'handmade', 'origami', 'clay', 'carve', 'carving',
        'wood', 'woodworking', 'paint', 'painting', 'draw', 'drawing',
        'knitting', 'crochet', 'sew', 'sewing', 'creative', 'art', 'artist',
        'sculpt', 'sculpture', 'lifehack', 'lifehacks', 'papercraft'
    }
    
    is_wildlife = any(k in wildlife_keywords for k in keywords)
    is_nature = any(k in nature_keywords for k in keywords)
    is_culture = any(k in culture_keywords for k in keywords)
    is_food = any(k in food_keywords for k in keywords)
    is_craft = any(k in craft_keywords for k in keywords)
    
    # Common viral hashtags for US audience
    common_viral_tags = ['#viral', '#trending', '#fyp', '#foryou', '#explore', '#reels', '#shorts']
    
    # Pre-saved SEO Patterns (Titles & Descriptions) - English versions for US audience
    if is_wildlife:
        titles = [
            "Wait For It... This {topic} Is INSANE! 😱",
            "POV: You're Face to Face With a {topic}! 🤯",
            "This {topic} Just Did Something UNTHINKABLE! 🔥",
            "Nature's Most Powerful {topic} Caught on Camera! 💪",
            "You Won't BELIEVE What This {topic} Just Did! 🚨"
        ]
        descriptions = [
            "The raw power of nature captured in one incredible moment. This {topic} video will leave you speechless! 🌍",
            "Close-up footage of a {topic} that's going viral right now. Nature never ceases to amaze! 🐾",
            "This is hands down the most incredible {topic} footage you'll see today. Share with someone who needs to see this! 😱"
        ]
        cat_tags = ['#wildlife', '#nature', '#animals', '#safari', '#predator', '#wildlifephotography', '#naturelovers', '#wild']
    elif is_nature:
        titles = [
            "This {topic} View Is Absolutely BREATHTAKING! 😍",
            "The Most Beautiful {topic} You'll See Today! ✨",
            "Nature's Masterpiece: {topic} at Its Finest! 🌎",
            "I Can't Stop Watching This {topic}! 🌿",
            "This {topic} Is Pure Magic! You Need to See This! 😍"
        ]
        descriptions = [
            "Take a deep breath and immerse yourself in the beauty of {topic}. Nature is the best healer! 🍃",
            "These stunning {topic} views will make you want to book a flight right now! Pure beauty! ✨",
            "Mother Nature really outdid herself with this {topic}. Share the beauty! 🌎"
        ]
        cat_tags = ['#nature', '#travel', '#beautiful', '#landscape', '#explore', '#earth', '#wanderlust', '#scenic']
    elif is_culture:
        titles = [
            "This {topic} Will Blow Your Mind! So Beautiful! 😱",
            "The Most Incredible {topic} You've Ever Seen! 🔥",
            "I Can't Believe This {topic} Is Real! So Stunning! ✨",
            "This {topic} Is Going VIRAL! Watch Until the End! 🤯",
            "You've NEVER Seen a {topic} Like This Before! 💥"
        ]
        descriptions = [
            "The beauty and elegance of {topic} captured in one incredible video. This is why culture matters! 🌏",
            "Stunning footage of {topic} that's breaking the internet right now. Must watch! 🎌",
            "This {topic} video is absolutely mesmerizing. Share the beauty with the world! ✨"
        ]
        cat_tags = ['#culture', '#beautiful', '#art', '#traditional', '#history', '#world', '#travel', '#amazing']
    elif is_food:
        titles = [
            "This {topic} Looks INCREDIBLE! I Need This NOW! 🤤",
            "Wait Until You See How This {topic} Is Made! 😱",
            "The Most Satisfying {topic} Video You'll See Today! 🔥",
            "I Tried This {topic} And It Changed My Life! 🤯",
            "This {topic} Is Making Me SO Hungry! 🍽️"
        ]
        descriptions = [
            "This {topic} looks absolutely delicious! Foodies, you need to see this! 🤤",
            "The art of making {topic} captured perfectly. This is food porn at its finest! 🍕",
            "Warning: Do NOT watch this video hungry! This {topic} is incredible! 🔥"
        ]
        cat_tags = ['#food', '#foodie', '#cooking', '#recipe', '#yummy', '#delicious', '#foodporn', '#chef']
    elif is_craft:
        titles = [
            "This {topic} DIY Is Pure Genius! 😱",
            "Wait Until You See How This {topic} Is Made! 🎨",
            "The Most Satisfying {topic} Craft You'll See Today! 🔥",
            "I Tried This {topic} Idea And It's Amazing! 🤯",
            "This {topic} Lifehack Is A Game Changer! 🛠️"
        ]
        descriptions = [
            "This creative {topic} idea is absolutely brilliant! DIY lovers, you must try this! 🎨",
            "The art of making {topic} captured perfectly. This is crafting at its finest! ✂️",
            "Get inspired by this beautiful {topic} project. Share it with fellow creators! 🔥"
        ]
        cat_tags = ['#diy', '#craft', '#handmade', '#creative', '#art', '#crafting', '#lifehacks', '#maker']
    else:
        titles = [
            "Wait For It... This {topic} Is CRAZY! 😱",
            "POV: You Witness Something INSANE! {topic}! 🤯",
            "This {topic} Video Is Going VIRAL Right Now! 🔥",
            "You Won't BELIEVE What Just Happened! {topic}! 🚨",
            "This Is the Most {topic} Thing I've EVER Seen! 💥"
        ]
        descriptions = [
            "This {topic} video is breaking the internet! You have to see this to believe it! 💥",
            "The most incredible {topic} footage you'll see today. Share with your friends! 👇",
            "This {topic} moment is absolutely unreal. Don't miss this! 🔥"
        ]
        cat_tags = ['#viral', '#trending', '#fyp', '#foryou', '#explore', '#reels', '#shorts', '#amazing']
        
    # Get deterministic choices based on filename to keep output consistent per video
    title_template = get_deterministic_choice(filename, titles)
    desc_template = get_deterministic_choice(filename, descriptions)
    
    # Generate Title & Base Description
    title = title_template.format(topic=topic_title)
    # Ensure title length limit
    if len(title) > 60:
        title = title[:57] + "..."
        
    base_desc = desc_template.format(topic=topic_title)
    
    # US-style CTAs (Call to Action)
    ctas = [
        "Like & Share if this blew your mind! ❤️",
        "Follow for more amazing content! 📲",
        "Tag someone who needs to see this! 👇",
        "Drop a comment if you agree! 💬",
        "Share this with your friends! ✈️",
        "Smash that like button! 👍",
        "Don't forget to follow for daily updates! 🔔"
    ]
    cta = get_deterministic_choice(filename + "_cta", ctas)
    description = f"{base_desc}\n\n{cta}"
    
    # Keywords Database mapping (US audience tags)
    KEYWORDS_DATABASE = {
        'tiger': ['tigers', 'bigcats', 'savethetigers'],
        'lion': ['lions', 'kingofthejungle', 'wildlions'],
        'leopard': ['leopards', 'bigcats', 'wildlife'],
        'cheetah': ['cheetahs', 'speed', 'africansafari'],
        'elephant': ['elephants', 'gentlegiants', 'africanwildlife'],
        'shark': ['sharks', 'underwater', 'oceanlife'],
        'whale': ['whales', 'ocean', 'marinelife'],
        'gorilla': ['gorillas', 'primates', 'silverback'],
        'eagle': ['eagles', 'raptors', 'birdsofprey'],
        'hunt': ['hunting', 'predators', 'survival'],
        'jungle': ['jungle', 'rainforest', 'wildnature'],
        'mountain': ['mountains', 'hiking', 'adventure'],
        'ocean': ['ocean', 'sea', 'underwater'],
        'panda': ['pandas', 'cutest', 'endangered'],
        'dragon': ['dragon', 'mythical', 'fantasy'],
        'tea': ['tea', 'tealover', 'teatime'],
        'silk': ['silk', 'luxury', 'craftsmanship'],
        'dance': ['dance', 'dancing', 'viral'],
        'music': ['music', 'musical', 'song'],
        'temple': ['temple', 'ancient', 'architecture'],
        'noodle': ['noodles', 'noodlelover', 'asianfood'],
        'dumpling': ['dumplings', 'foodie', 'asianfood'],
        'hotpot': ['hotpot', 'spicyfood', 'chinesefood'],
        'cooking': ['cooking', 'chef', 'homemade'],
        'food': ['food', 'foodie', 'delicious'],
        'spicy': ['spicy', 'hot', 'spicyfood'],
        'fried': ['fried', 'crispy', 'friedfood'],
        'soup': ['soup', 'souplover', 'comfortfood'],
        'sweet': ['sweet', 'dessert', 'treats'],
        'spring': ['spring', 'springtime', 'seasons'],
        'autumn': ['autumn', 'fall', 'cozy'],
        'ancient': ['ancient', 'history', 'mysterious'],
        'traditional': ['traditional', 'heritage', 'classic'],
        'festival': ['festival', 'celebration', 'holiday'],
    }
    
    # Build Hashtags list
    # 1. Start with fundamental US viral tags
    hash_tags_set = {'#viral', '#trending', '#fyp', '#foryou', '#explore', '#reels', '#shorts'}
    
    # 2. Add category tags
    for tag in cat_tags:
        hash_tags_set.add(tag.lower())
        
    # 3. Add tags from clean keywords database
    for k in keywords:
        if k in KEYWORDS_DATABASE:
            for extra in KEYWORDS_DATABASE[k]:
                hash_tags_set.add(f"#{extra}")
                
    # 4. Add keywords as tags themselves
    for k in keywords:
        if len(k) > 2:
            hash_tags_set.add(f"#{k}")
            
    # Convert set back to list, ensure we don't have duplicates, and limit to ~10 tags
    ordered_tags = ['#viral', '#trending', '#fyp', '#reels', '#shorts']
    for tag in sorted(hash_tags_set):
        if tag not in ordered_tags:
            ordered_tags.append(tag)
            
    # Slice to a max of 10 hashtags to avoid tag stuffing
    final_tags = ordered_tags[:10]
    hashtags_str = " ".join(final_tags)
    
    return {
        'title': title,
        'description': description,
        'hashtags': hashtags_str
    }

def format_caption(seo_metadata):
    """
    Combines the title, description, and hashtags into the final Facebook caption format.
    """
    return f"{seo_metadata['title']}\n\n{seo_metadata['description']}\n\n{seo_metadata['hashtags']}"
