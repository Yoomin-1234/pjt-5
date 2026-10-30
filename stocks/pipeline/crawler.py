# stocks/crawler.py
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def crawl_company_comments(company_name, max_count=20):
    """
    토스증권에서 회사명을 검색해 최상단 종목의 커뮤니티 댓글 20개를 수집하여
    {"company": "실제종목명", "comments": ["댓글1", "댓글2", ...]} 형태로 반환합니다.
    """
    options = webdriver.ChromeOptions()
    # 브라우저 창을 띄우지 않고 실행하려면 아래 주석을 해제하세요. (디버깅 시에는 주석 유지 권장)
    # options.add_argument('--headless=new')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    wait = WebDriverWait(driver, 10)

    try:
        # 1. 토스증권 메인 페이지 접속 (01_open_main.py)
        driver.get('https://tossinvest.com/')
        time.sleep(2)

        # 2. 우측 상단 검색창(모달) 열기 및 회사명 입력 (02_search_company.py & 그림 3, 4)
        body = driver.find_element(By.TAG_NAME, 'body')
        body.send_keys('/')  # 토스증권 단축키 '/' 또는 검색 버튼 클릭으로 검색 모달 오픈
        time.sleep(1)

        search_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="text"], input[type="search"], input')
        search_input = None
        for inp in search_inputs:
            if inp.is_displayed():
                search_input = inp
                break

        if search_input is None:
            # 단축키로 열리지 않은 경우 검색 버튼 직접 클릭
            search_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '검색') or contains(@placeholder, '검색')]"))
            )
            search_btn.click()
            time.sleep(1)
            search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input')))

        search_input.clear()
        search_input.send_keys(company_name)
        time.sleep(2)  # 검색 결과 목록이 모달에 렌더링될 때까지 대기

        # 3. 최상단 노출 회사 선택 및 종목 코드 추출 (03_get_stock_code.py & F603)
        # 모달 내 종목 결과 링크(/stocks/종목코드/order) 중 가장 첫 번째 요소를 찾음
        stock_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/stocks/"]')
        if not stock_links:
            # Enter 키를 눌러 자동 포커싱된 최상단 결과로 이동 시도
            search_input.send_keys(Keys.ENTER)
            time.sleep(2)
            if '/stocks/' not in driver.current_url:
                return {'company': None, 'comments': []}
        else:
            first_link = stock_links[0]
            driver.execute_script('arguments[0].click();', first_link)
            time.sleep(2)

        # 현재 URL(예: https://tossinvest.com/stocks/A005930/order)에서 종목 코드 추출
        current_url = driver.current_url
        if '/stocks/' not in current_url:
            return {'company': None, 'comments': []}

        stock_code = current_url.split('/stocks/')[1].split('/')[0]

        # 4. 커뮤니티 탭으로 이동 (04_open_community.py & 그림 5)
        community_url = f'https://tossinvest.com/stocks/{stock_code}/community'
        driver.get(community_url)
        time.sleep(2.5)

        # 실제 종목명 추출 (상세 페이지 상단 타이틀 영역)
        actual_company_name = company_name
        try:
            title_el = driver.find_element(By.TAG_NAME, 'h1')
            if title_el.text.strip():
                actual_company_name = title_el.text.strip().split()[0]
        except Exception:
            # 브라우저 탭 제목(예: "삼성전자 주식 정보 | 토스증권")에서 추출
            if driver.title:
                actual_company_name = driver.title.split()[0]

        # 5. 커뮤니티 댓글 20개 수집 (05_collect_comments.py & F604)
        collected_comments = []
        seen = set()

        for _ in range(6):  # 스크롤하며 최대 20개 수집
            # 토스증권 커뮤니티 게시글 본문 요소 탐색
            articles = driver.find_elements(
                By.CSS_SELECTOR,
                'article span, article p, [data-testid*="comment"] span, main article div[class*="comment"]'
            )
            if not articles:
                articles = driver.find_elements(By.CSS_SELECTOR, 'article')

            for el in articles:
                text = el.text.strip()
                if not text or text in seen:
                    continue
                # 버튼 텍스트나 단순 시간/닉네임 노이즈 제외
                if text in ('팔로우', '인기순', '최신순', '더보기', actual_company_name):
                    continue
                seen.add(text)
                collected_comments.append(text)
                if len(collected_comments) >= max_count:
                    break

            if len(collected_comments) >= max_count:
                break

            driver.execute_script('window.scrollBy(0, 800);')
            time.sleep(1)

        return {
            'company': actual_company_name,
            'comments': collected_comments[:max_count],
        }

    except Exception as exc:
        print(f'[Crawler Error] {exc}')
        return {'company': None, 'comments': []}
    finally:
        driver.quit()