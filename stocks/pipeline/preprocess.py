import re
from .llm import filter_bad_comments_with_llm


def preprocess_comments(comments):
  

    cleaned = []
    seen = set()

    for comment in comments:

        # 1. 문자열이 아닌 댓글 제외
        if not isinstance(comment, str):
            continue

        text = comment.strip()

        # 2. 원본 댓글 길이 검사
        if not 5 <= len(text) <= 76:
            continue

        # 3. 반복되는 감탄/웃음 표현 제거
        text = re.sub(r"[ㅋㅎㅠㅜ]{2,}", "", text)

        # 4. 주식 관련 기호를 제외한 특수문자 제거
        text = re.sub(
            r"[^가-힣a-zA-Z0-9\s%+\-.,]",
            "",
            text,
        )

        # 5. 불필요한 공백 제거
        text = re.sub(r"\s+", " ", text).strip()

        # 6. 정제 후 길이 다시 검사
        if not 5 <= len(text) <= 76:
            continue

        # 7. 중복 댓글 제거
        if text in seen:
            continue

        seen.add(text)
        cleaned.append(text)

    # 정제할 댓글이 없으면 API 호출 생략
    if not cleaned:
        return []

    # 8. LLM을 통한 부적절 댓글 제거
    return filter_bad_comments_with_llm(cleaned)
