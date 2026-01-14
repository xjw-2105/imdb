"""
IMDb 评论爬虫 - 增强稳定版 (Anti-Detect Selenium)
------------------------------------------------
修改说明:
1. 关闭 Headless 模式：浏览器会弹出，方便通过人工验证。
2. 集成反爬虫伪装：隐藏 WebDriver 特征，防止被识别为机器人。
3. 增加页面加载超时设置：解决 Read timed out 问题。

使用方法:
    python selenium_scraper.py tt1375666              # 爬取单部
    python selenium_scraper.py tt1375666 tt0068646   # 爬取多部
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import argparse
import random

def scrape_movie(movie_id, target_count=300):
    """爬取单部电影的评论"""
    print(f"\n{'='*50}")
    print(f"🎬 爬取电影: {movie_id}")
    print(f"🎯 目标: {target_count} 条评论")
    print(f"{'='*50}")

    # --- 浏览器配置 (反爬虫核心) ---
    options = webdriver.ChromeOptions()
    
    # 1. 【重要】关闭无头模式，让浏览器显示出来
    # 这样如果遇到验证码，你可以手动点一下，程序就能继续跑
    # options.add_argument('--headless') 
    
    # 2. 基础设置
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized') # 最大化窗口防止元素被遮挡
    
    # 3. 反检测设置 (伪装成正常浏览器)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # 4. 伪装 User-Agent (Mac Chrome)
    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # 5. 注入 JS 彻底隐藏 WebDriver 特征
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
            })
        """
    })

    try:
        # 设置页面加载超时 (防止一直在转圈导致报错)
        driver.set_page_load_timeout(60)
        
        url = f"https://www.imdb.com/title/{movie_id}/reviews?sort=submissionDate&dir=desc&ratingFilter=0"
        print(f"🌍 正在打开页面: {url}")
        
        try:
            driver.get(url)
        except Exception as e:
            print("⚠️ 页面加载超时，但可能已显示内容，继续尝试...")
            driver.execute_script("window.stop();")
        
        print("👀 页面已打开，等待渲染...")
        time.sleep(5) # 给足时间让页面显示

        # 循环点击 "Load More" 按钮
        current_count = 0
        click_count = 0
        # 计算需要点击多少次 (IMDb一次加载25条)
        max_clicks = (target_count // 25) + 5
        
        while current_count < target_count and click_count < max_clicks:
            try:
                # 尝试寻找按钮
                load_more_btn = None
                selectors = [
                    "button.ipc-see-more__button",
                    "button[data-testid='see-more-button']",
                    ".load-more-data",
                    "button.ipl-load-more__button",
                    "//button[contains(text(), 'Load More')]"
                ]
                
                for selector in selectors:
                    try:
                        if selector.startswith("//"):
                            load_more_btn = driver.find_element(By.XPATH, selector)
                        else:
                            load_more_btn = driver.find_element(By.CSS_SELECTOR, selector)
                        
                        if load_more_btn and load_more_btn.is_displayed():
                            break
                    except:
                        continue
                
                if not load_more_btn:
                    # 如果找不到按钮，再次检查是否已经是所有评论了
                    reviews_check = driver.find_elements(By.CSS_SELECTOR, "article.user-review-item, div.review-container")
                    if len(reviews_check) >= target_count:
                        print("✅ 已达到目标数量")
                        break
                    print("⚠️ 找不到加载更多按钮，尝试滚动页面...")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    continue
                
                # 滚动到按钮位置
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_btn)
                time.sleep(1) # 稍微停顿，模拟人类
                
                # 点击按钮 (使用 JS 点击更稳定)
                driver.execute_script("arguments[0].click();", load_more_btn)
                click_count += 1
                
                # 随机等待 2-4 秒 (反爬虫关键：不要太有规律)
                wait_time = random.uniform(2, 4)
                time.sleep(wait_time)
                
                # 实时显示进度
                reviews_on_page = driver.find_elements(By.CSS_SELECTOR, "article.user-review-item, div.review-container")
                current_count = len(reviews_on_page)
                print(f"📊 已加载: {current_count} 条 (点击 {click_count} 次)")
                
            except Exception as e:
                print(f"⚠️ 点击加载更多时出错 (可能是弹窗阻挡，请手动关闭): {e}")
                time.sleep(3) # 给用户时间手动处理
                continue

        print("🛑 停止加载，开始解析数据...")
        
        # 解析 HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 兼容两种 IMDb 页面结构
        review_containers = soup.select('article.user-review-item')
        if not review_containers:
            review_containers = soup.select('div.review-container')
        
        reviews = []
        for container in review_containers:
            review = parse_review(container)
            if review and review.get('content'):
                reviews.append(review)
        
        # 截断到目标数量
        reviews = reviews[:target_count]
        print(f"✅ 成功解析 {len(reviews)} 条评论")
        return reviews

    except Exception as e:
        print(f"❌ 爬取严重失败: {e}")
        return []
    
    finally:
        # 稍微等待一下再关闭，以防最后时刻报错
        time.sleep(2)
        driver.quit()
        print("🔌 浏览器已关闭")


def parse_review(container):
    """解析单条评论 (保持原逻辑)"""
    review = {}
    
    # 用户名
    user_selectors = ['a[data-testid="author-link"]', 'span.display-name-link a', 'a.author-link']
    for sel in user_selectors:
        tag = container.select_one(sel)
        if tag:
            review['user'] = tag.get_text(strip=True)
            break
    else:
        review['user'] = 'Anonymous'
    
    # 日期
    date_selectors = ['li.review-date', 'span.review-date', '.date']
    for sel in date_selectors:
        tag = container.select_one(sel)
        if tag:
            review['date'] = tag.get_text(strip=True)
            break
    else:
        review['date'] = ''
    
    # 评分
    rating_selectors = ['span.ipc-rating-star--otherUserAlt', 'span.rating-other-user-rating span', 'span.ipl-rating-star__rating']
    for sel in rating_selectors:
        tag = container.select_one(sel)
        if tag:
            rating_text = tag.get_text(strip=True)
            import re
            match = re.search(r'(\d+)', rating_text)
            if match:
                review['rating'] = f"{match.group(1)}/10"
                break
    else:
        review['rating'] = 'N/A'
    
    # 内容
    content_selectors = ['div[data-testid="review-overflow"]', 'div.text.show-more__control', 'div.review-text', 'div.content']
    for sel in content_selectors:
        tag = container.select_one(sel)
        if tag:
            review['content'] = tag.get_text(strip=True)
            break
    else:
        review['content'] = ''
    
    return review


def save_reviews(movie_id, reviews, output_dir='data'):
    """保存评论到 CSV"""
    if not reviews:
        print(f"⚠️ 没有评论可保存")
        return None
    
    os.makedirs(output_dir, exist_ok=True)
    
    df = pd.DataFrame(reviews)
    filepath = os.path.join(output_dir, f"{movie_id}_reviews.csv")
    # 使用 utf-8-sig 防止 Excel 打开乱码
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    print(f"💾 已保存到: {filepath} ({len(reviews)} 条)")
    return filepath


def main():
    parser = argparse.ArgumentParser(description='IMDb 评论爬虫 (Selenium 增强版)')
    parser.add_argument('movie_ids', nargs='+', help='IMDb 电影 ID (如 tt1375666)')
    parser.add_argument('--max', type=int, default=300, help='每部电影最大评论数')
    parser.add_argument('--output', type=str, default='data', help='输出目录')
    
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════╗
║      IMDb 评论爬虫 - 增强稳定版                 ║
╠══════════════════════════════════════════════════╣
║  提示: 浏览器将自动打开。                        ║
║  如果看到 "Verify you are human" 或 Cookie 弹窗，  ║
║  请在浏览器中【手动点击】通过，爬虫会自动继续！      ║
╚══════════════════════════════════════════════════╝
    """)
    
    results = []
    for i, movie_id in enumerate(args.movie_ids):
        # 确保 ID 格式正确
        if not movie_id.startswith('tt'):
            movie_id = f'tt{movie_id}'
        
        reviews = scrape_movie(movie_id, args.max)
        filepath = save_reviews(movie_id, reviews, args.output)
        
        results.append({
            'movie_id': movie_id,
            'count': len(reviews),
            'filepath': filepath
        })
        
        # 多部电影之间的随机等待 (防止封 IP)
        if i < len(args.movie_ids) - 1:
            wait_time = random.randint(10, 15)
            print(f"⏳ 为了安全，等待 {wait_time} 秒后继续下一部...")
            time.sleep(wait_time)
    
    print(f"\n✅ 全部完成! 数据保存在 {args.output}/ 目录")


if __name__ == '__main__':
    main()
