
import traceback
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def find_search_input(driver):
    """실제로 입력 가능한 검색창 찾기"""
    inputs = driver.find_elements(
        By.CSS_SELECTOR,
        'input[type="text"], input[type="search"]'
    )

    for element in inputs:
        if (
            element.is_displayed()
            and element.is_enabled()
            and element.get_attribute("readonly") is None
            and element.get_attribute("disabled") is None
        ):
            return element

    return False


def crawl_company_comments(company_name, max_count=20):
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless=new')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    wait = WebDriverWait(driver, 10)

    try:
        # 1. 토스증권 메인 페이지 접속
        print("토스증권 접속 중...")

        driver.get("https://www.tossinvest.com/")

        wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # 2. 검색 버튼 클릭
        search_button = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//*[contains(text(), '검색하세요')]"
            ))
        )

        search_button.click()
        time.sleep(1)

        # 3. 검색창 찾기
        search_input = wait.until(find_search_input)

        print("검색창 확인 완료")

        # 4. 회사명 입력
        search_input.click()
        search_input.clear()
        search_input.send_keys(company_name)

        time.sleep(2)

        # 5. 검색 결과를 JavaScript로 한 번에 가져오기
        # Selenium WebElement를 반복해서 읽을 때 발생하는
        # StaleElementReferenceException 방지
        stock_candidates = driver.execute_script("""
            return Array.from(
                document.querySelectorAll('a[href*="/stocks/"]')
            ).map(link => ({
                text: (link.innerText || link.textContent || '').trim(),
                href: link.href
            }));
        """)

        print("전체 종목 링크 수:", len(stock_candidates))
        print("현재 URL:", driver.current_url)

        # 6. 입력한 회사명과 일치하는 검색 결과 찾기
        company_matches = []
        seen_hrefs = set()

        for candidate in stock_candidates:
            text = candidate["text"]
            href = candidate["href"]

            if (
                company_name.strip() in text
                and href
                and "/stocks/" in href
                and href not in seen_hrefs
            ):
                company_matches.append((text, href))
                seen_hrefs.add(href)

        print("회사명 일치 후보 수:", len(company_matches))

        for text, href in company_matches[:5]:
            print("검색 후보:", text, "|", href)

        # 검색 결과가 없으면 종료
        if not company_matches:
            print(
                f"'{company_name}'과 일치하는 종목이 없습니다."
            )

            return {
                "company": None,
                "comments": []
            }

        # 7. 최상단 검색 결과 선택
        target_text, target_href = company_matches[0]

        print("선택한 종목:", target_text)
        print("이동할 주소:", target_href)

        # 실제 매칭된 종목명
        actual_company_name = target_text.splitlines()[0].strip()

        # 기존 WebElement 클릭 대신 주소로 직접 이동
        driver.get(target_href)

        wait.until(
            lambda d: "/stocks/" in d.current_url
        )

        current_url = driver.current_url

        print("종목 페이지 URL:", current_url)

        # 8. 종목 코드 추출
        stock_code = (
            current_url.split('/stocks/')[1].split('/')[0]
        )

        # 9. 커뮤니티 페이지 이동
        community_url = (
            f"https://www.tossinvest.com/stocks/"
            f"{stock_code}/community"
        )

        print("커뮤니티 이동 주소:", community_url)

        driver.get(community_url)

        wait.until(
            EC.presence_of_element_located(
                (By.TAG_NAME, "body")
            )
        )

        time.sleep(3)

        print("커뮤니티 페이지 접속 완료")
        print("커뮤니티 현재 URL:", driver.current_url)

        # 10. 커뮤니티 게시글 수집
        # 게시글 하나를 댓글 데이터 하나로 취급
        collected_comments = []
        seen = set()

        no_new_data_count = 0
        max_scroll_attempts = 30

        print("\n========== 게시글 수집 시작 ==========")

        for scroll_count in range(max_scroll_attempts):

            posts = driver.find_elements(
                By.CSS_SELECTOR,
                'div[data-section-name="커뮤니티__게시글"]'
            )

            print(
                f"\n[{scroll_count + 1}회차] "
                f"화면 게시글 요소 수: {len(posts)}"
            )

            previous_count = len(collected_comments)

            for post in posts:
                try:
                    # 게시글 제목
                    title_elements = post.find_elements(
                        By.CSS_SELECTOR,
                        'span.tc3tm84'
                    )

                    # 게시글 본문
                    body_elements = post.find_elements(
                        By.CSS_SELECTOR,
                        'span._1xixuox1'
                    )

                    title = " ".join(
                        element.text.strip()
                        for element in title_elements
                        if element.text.strip()
                    )

                    body = " ".join(
                        element.text.strip()
                        for element in body_elements
                        if element.text.strip()
                    )

                    # 제목과 본문 결합
                    content = " ".join(
                        part
                        for part in [title, body]
                        if part
                    ).strip()

                    # 빈 데이터 및 중복 데이터 제외
                    if not content or content in seen:
                        continue

                    seen.add(content)
                    collected_comments.append(content)

                    print(
                        f"게시글 {len(collected_comments)}개 수집: "
                        f"{content[:100]}"
                    )

                    if len(collected_comments) >= max_count:
                        break

                except Exception as e:
                    print("게시글 처리 오류:", e)
                    continue

            # 목표 개수 도달
            if len(collected_comments) >= max_count:
                print("\n목표 수집 개수에 도달했습니다.")
                break

            # 새롭게 수집된 게시글이 있는지 확인
            new_data_count = (
                len(collected_comments) - previous_count
            )

            if new_data_count == 0:
                no_new_data_count += 1
            else:
                no_new_data_count = 0

            # 4회 연속 새 게시글이 없으면 종료
            if no_new_data_count >= 4:
                print("\n추가 게시글이 없어 수집을 종료합니다.")
                break

            # 11. 추가 게시글 로딩을 위한 스크롤
            # WebElement를 전달하지 않고 JavaScript에서 직접 탐색
            driver.execute_script("""
                let node = document.querySelector(
                    'div[data-section-name="커뮤니티__게시글"]'
                );

                while (node && node !== document.body) {
                    const style = window.getComputedStyle(node);

                    const isScrollable =
                        node.scrollHeight > node.clientHeight + 5 &&
                        (
                            style.overflowY === 'auto' ||
                            style.overflowY === 'scroll'
                        );

                    if (isScrollable) {
                        node.scrollTop += Math.max(
                            node.clientHeight * 0.8,
                            500
                        );
                        return;
                    }

                    node = node.parentElement;
                }

                window.scrollBy(
                    0,
                    Math.max(window.innerHeight * 0.8, 700)
                );
            """)

            time.sleep(1.5)

        # 12. 최종 수집 결과
        print("\n========== 수집 결과 ==========")
        print("회사명:", actual_company_name)
        print("목표 수집 개수:", max_count)
        print("실제 수집 개수:", len(collected_comments))

        for index, comment in enumerate(
            collected_comments,
            start=1
        ):
            print(f"{index}. {comment}")

        if len(collected_comments) < max_count:
            print(
                f"\n안내: 목표 {max_count}개 중 "
                f"{len(collected_comments)}개를 수집했습니다."
            )

        return {
            "company": actual_company_name,
            "comments": collected_comments[:max_count]
        }

    except Exception as e:
        print(f"[Crawler Error]: {e}")
        traceback.print_exc()

        return {
            "company": None,
            "comments": []
        }

    finally:
        driver.quit()
