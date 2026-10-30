# analysis/pipeline/crawler.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def crawl_toss_comments(company_name):
    # 크롬 드라이버 설정 (Headless 옵션 권장)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    comments = []
    actual_company_name = company_name

    try:
        # 1. 토스증권 접속 및 검색 (F603)
        driver.get(f"https://tossinvest.com/search?keyword={company_name}")
        time.sleep(2)
        
        # 검색 결과 최상단 회사 클릭 (실제 CSS 선택자는 확인 필요)
        first_result = driver.find_element(By.CSS_SELECTOR, ".search-result-item")
        actual_company_name = first_result.text.split('\n')[0] # 실제 종목명 추출
        first_result.click()
        time.sleep(2)
        
        # 2. 커뮤니티 탭 이동 및 댓글 수집 (F604)
        community_tab = driver.find_element(By.XPATH, "//button[contains(text(), '커뮤니티')]")
        community_tab.click()
        time.sleep(2)
        
        comment_elements = driver.find_elements(By.CSS_SELECTOR, ".comment-text-class")[:20] # 20개 수집[cite: 131]
        comments = [elem.text for elem in comment_elements]
        
    except Exception as e:
        print(f"Crawling Error: {e}")
    finally:
        driver.quit()
        
    return actual_company_name, comments