import re
import math


def clean_comment(comment):
    """
    댓글 하나를 정제한다.
    정제 결과와 제거 사유를 반환한다.

    반환값:
        (정제된 댓글, None)
        (None, 제거 사유)
    """

    # 1. 결측치 확인
    if comment is None:
        return None, "결측치"

    # 실수형 NaN 확인
    if isinstance(comment, float) and math.isnan(comment):
        return None, "결측치"

    text = str(comment)

    # 2. 불필요한 공백 제거
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return None, "빈 문자열"

    # 3. 불필요한 반복 패턴 제거
    # 예: ㅋㅋㅋ, ㅎㅎㅎ, ㅠㅠ, ㅜㅜ, ...., !!!
    noise_patterns = [
        r"[ㅋㅎ]{2,}",
        r"[ㅠㅜ]{2,}",
        r"[.!?~]{3,}",
    ]

    for pattern in noise_patterns:
        text = re.sub(pattern, " ", text)

    # 4. 의미 없는 특수문자 제거
    # 한글, 영어, 숫자, 기본 문장부호 및 일부 기호 유지
    text = re.sub(
        r"[^가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z0-9\s.,!?%+\-]",
        " ",
        text
    )

    # 5. 공백 재정리
    text = re.sub(r"\s+", " ", text).strip()

    # 6. 문자나 숫자가 없는 의미 없는 데이터 제거
    if not re.search(r"[가-힣a-zA-Z0-9]", text):
        return None, "의미 없는 특수문자"

    # 7. 댓글 길이 확인 (5자 이상 ~ 76자 이하)
    if len(text) < 5:
        return None, "댓글 길이 5자 미만"

    if len(text) > 76:
        return None, "댓글 길이 76자 초과"

    return text, None


def preprocess_comments(raw_comments):
    """
    원본 댓글 목록을 전처리한다.

    원본 데이터는 보존하고,
    정제된 댓글 목록과 제거된 댓글 목록을 별도로 반환한다.
    """

    if raw_comments is None:
        raw_comments = []
    else:
        raw_comments = list(raw_comments)

    cleaned_comments = []
    removed_comments = []

    for index, comment in enumerate(raw_comments):

        cleaned, reason = clean_comment(comment)

        if cleaned is None:
            removed_comments.append({
                "index": index,
                "original": comment,
                "reason": reason
            })
            continue

        cleaned_comments.append(cleaned)

    return {
        "original_comments": raw_comments,
        "cleaned_comments": cleaned_comments,
        "removed_comments": removed_comments,
        "original_count": len(raw_comments),
        "cleaned_count": len(cleaned_comments),
        "removed_count": len(removed_comments)
    }


def remove_inappropriate_comments(
    comments,
    inappropriate_indices
):
    """
    LLM이 반환한 부적절한 댓글 번호를 기준으로 제거한다.

    inappropriate_indices:
        LLM이 반환한 0부터 시작하는 댓글 인덱스 목록
        예: [1, 3, 5]
    """

    inappropriate_indices = {
        index
        for index in (inappropriate_indices or [])
        if isinstance(index, int) and not isinstance(index, bool)
    }

    filtered_comments = [
        comment
        for index, comment in enumerate(comments)
        if index not in inappropriate_indices
    ]

    return filtered_comments
