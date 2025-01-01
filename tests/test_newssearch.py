from newsplease import NewsPlease
import time
from fake_useragent import UserAgent
import requests

def search_news_articles():
    # 使用更可能成功的新闻网站URL
    news_urls = [

        'https://www.aibase.com/zh/news',

    ]
    
    try:
        keyword = "人工智能"
        print(f"正在搜索包含 '{keyword}' 的新闻...")
        
        # 创建请求头
        ua = UserAgent()
        headers = {
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        matching_articles = []
        for url in news_urls:
            try:
                # 添加延时避免被封
                time.sleep(2)
                
                # 使用requests获取页面内容
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    # 使用NewsPlease处理页面内容
                    article = NewsPlease.from_html(response.text, url=url)
                    
                    if article and article.title:
                        if keyword in (article.title or '') or keyword in (article.text or ''):
                            matching_articles.append({
                                '标题': article.title,
                                '发布日期': article.date_publish,
                                'URL': article.url
                            })
            except Exception as e:
                print(f"抓取 {url} 时出错: {str(e)}")
                continue
        
        if matching_articles:
            print(f"\n找到 {len(matching_articles)} 篇相关新闻：")
            for idx, article in enumerate(matching_articles, 1):
                print(f"\n{idx}. 标题：{article['标题']}")
                print(f"   发布日期：{article['发布日期']}")
                print(f"   链接：{article['URL']}")
        else:
            print("\n未找到相关新闻")
            
    except Exception as e:
        print(f"搜索过程中出现错误：{str(e)}")

if __name__ == "__main__":
    search_news_articles()
