# stocks/pipeline/crawler.py
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def crawl_company_comments(company_name, max_count=20):
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless=new') # 브라우저 창을 숨기려면 주석 해제
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)

    try:
        # 1. 토스증권 메인 접속 및 검색 모달 오픈
        driver.get("https://tossinvest.com/")
        time.sleep(2)
        
        body = driver.find_element(By.TAG_NAME, 'body')
        body.send_keys('/')
        time.sleep(1)

        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input')))
        search_input.clear()
        search_input.send_keys(company_name)
        time.sleep(2)

        # F603: 최상단 노출 회사 자동 선택
        stock_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/stocks/"]')
        if not stock_links:
            search_input.send_keys(Keys.ENTER)
            time.sleep(2)
            if '/stocks/' not in driver.current_url:
                return {"company": None, "comments": []}
        else:
            driver.execute_script("arguments[0].click();", stock_links[0])
            time.sleep(2)

        current_url = driver.current_url
        if '/stocks/' not in current_url:
            return {"company": None, "comments": []}
            
        stock_code = current_url.split('/stocks/')[1].split('/')[0]

        # 2. 커뮤니티 탭 이동
        driver.get(f"https://tossinvest.com/stocks/{stock_code}/community")
        time.sleep(2.5)

        actual_company_name = company_name
        try:
            title_el = driver.find_element(By.TAG_NAME, 'h1')
            if title_el.text.strip():
                actual_company_name = title_el.text.strip().split()[0]
        except Exception:
            pass

        # F604: 커뮤니티 댓글 20개 수집
        collected_comments = []
        seen = set()
        for _ in range(6):
            articles = driver.find_elements(By.CSS_SELECTOR, 'article span, article p, [data-testid*="comment"] span')
            for el in articles:
                text = el.text.strip()
                if not text or text in seen:
                    continue
                if text in ('팔로우', '인기순', '최신순', '더보기', actual_company_name):
                    continue
                seen.add(text)
                collected_comments.append(text)
                if len(collected_comments) >= max_count:
                    break
            if len(collected_comments) >= max_count:
                break
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(1)

        return {
            "company": actual_company_name,
            "comments": collected_comments[:max_count]
        }
    except Exception as e:
        print(f"[Crawler Error]: {e}")
        return {"company": None, "comments": []}
    finally:
        driver.quit()