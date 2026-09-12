"""Reddit bot entry point — orchestrates accounts, actions, and reporting."""

from __future__ import annotations

import logging
import os
import random
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from tqdm import tqdm

from args import cmdline_args
from bot import BotConfig, GhostLogger
from bot.reporting import ExecutionSummary, setup_structured_logger
from bot.utils.input_parser import parse_links_file, ActionEntry
from openai import OpenAI

# إعداد الذكاء الاصطناعي المجاني عبر OpenRouter
ai_client = OpenAI(
    base_url="https://openrouter.ai",
    api_key=os.getenv("OPENAI_API_KEY")
)

def get_ai_comment(post_title, prompt_style):
    try:
        response = ai_client.chat.completions.create(
            model="deepseek/deepseek-chat-free",
            messages=[{"role": "user", "content": f"{prompt_style} for this Reddit post title: '{post_title}'. Keep it short, natural, and casual."}]
        )
        return response.choices.message.content
    except:
        return "Wow, that's really interesting! Thanks for sharing."

def run_api_bot(username, password, entries, logger):
    """تشغيل البوت بنظام الطلبات السريع والخفيف بدون متصفح كروم"""
    logger.info(f"Initializing API session for user: {username}")
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    login_url = "https://reddit.com"
    login_data = {'user': username, 'passwd': password, 'api_type': 'json'}
    
    res = session.post(login_url, data=login_data)
    if "invalid_grant" in res.text or not res.ok:
        logger.error(f"Login failed for {username}! Check your username or password.")
        return

    logger.info(f"[SUCCESS] Logged in successfully to Reddit as {username}!")

    for entry in entries:
        sub_url = entry.link
        prompt_style = entry.comment if entry.comment else "Write a cool response"
        sub_name = sub_url.split('/r/')[-1].split('/')[0]
        
        logger.info(f"Fetching hot posts from r/{sub_name}")
        
        feed_url = f"https://reddit.com{sub_name}/hot.json?limit=5"
        try:
            feed_res = session.get(feed_url).json()
            posts = feed_res['data']['children']
            
            for post in posts[:2]:  # التعليق على أول منشورين
                post_data = post['data']
                post_id = post_data['id']
                title = post_data['title']
                
                comment_text = get_ai_comment(title, prompt_style)
                
                comment_data = {'thing_id': f't3_{post_id}', 'text': comment_text, 'api_type': 'json'}
                comment_res = session.post("https://reddit.com", data=comment_data)
                
                if comment_res.ok:
                    logger.info(f"[SUCCESS] Commented on: '{title}' in r/{sub_name}")
                else:
                    logger.warning(f"[FAILED] Could not comment on post: {post_id}")
                
                # فاصل زمني آمن لعدم الحظر (من 3 إلى 7 دقائق)
                time.sleep(random.randint(180, 420))
        except Exception as e:
            logger.warning(f"Skipped r/{sub_name} due to an error: {e}")
            continue

def main() -> None:
    args = cmdline_args()
    config = BotConfig()
    config.merge_cli_args(args)

    logger = setup_structured_logger("reddit-bot", level=logging.INFO)

    # جلب الحساب مباشرة من المتغيرات السرية المضافة للسيرفر لتفادي أي أخطاء ملفات
    username = os.getenv("REDDIT_USERNAME")
    password = os.getenv("REDDIT_PASSWORD")

    if not username or not password:
        logger.error("Reddit credentials missing in environment variables! Please add REDDIT_USERNAME and REDDIT_PASSWORD in Railway.")
        sys.exit(1)

    if not config.links_path:
        config.links_path = "links.txt"

    entries = parse_links_file(config.links_path)
    if not entries:
        logger.error("No actions found in links file 'links.txt'.")
        sys.exit(1)

    logger.info(f"Loaded 1 account from env and {len(entries)} actions from links.txt")

    # إطلاق البوت السريع
    while True:
        try:
            run_api_bot(username, password, entries, logger)
            logger.info("Finished one complete cycle. Waiting 30 minutes before next run...")
            time.sleep(1800)
        except Exception as e:
            logger.error(f"Main loop exception: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
