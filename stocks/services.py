
from .pipeline.preprocess import preprocess_comments
from .pipeline.augment import augment_comments
from .pipeline.llm import (
    filter_bad_comments_with_llm,
    summarize_comments,
)


def process_comments_pipeline(comments):
    """
    원본 댓글을 전처리하고,
    GMS LLM으로 부적절한 댓글을 제거한 뒤,
    텍스트 증강 및 요약을 수행한다.
    """

    # 1. 원본 댓글 보존
    original_comments = list(comments or [])

    # 2. 기본 전처리
    preprocessing_result = preprocess_comments(
        original_comments
    )

    basic_cleaned_comments = preprocessing_result[
        "cleaned_comments"
    ]

    # 3. GMS LLM을 활용한 부적절 댓글 판별 및 제거
    cleaned_comments = filter_bad_comments_with_llm(
        basic_cleaned_comments
    )

    # 4. 정제된 댓글을 기반으로 텍스트 증강
    augmented_comments = augment_comments(
        cleaned_comments
    )

    # 5. 원본 댓글 전체를 기반으로 AI 요약
    summary = summarize_comments(
        original_comments
    )

    # 6. 길이 필터링 기준 정보
    # 실제 통계적 IQR 계산값이 아니라 명세서의 길이 기준
    iqr_info = {
        "lower_bound": 5,
        "upper_bound": 76,
    }

    # 7. 처리 결과 반환
    return {
        "original_comments": original_comments,
        "cleaned_comments": cleaned_comments,
        "augmented_comments": augmented_comments,
        "removed_comments": preprocessing_result[
            "removed_comments"
        ],
        "original_count": len(original_comments),
        "basic_cleaned_count": len(
            basic_cleaned_comments
        ),
        "cleaned_count": len(cleaned_comments),
        "removed_count": (
            len(original_comments) - len(cleaned_comments)
        ),
        "llm_removed_count": (
            len(basic_cleaned_comments) - len(cleaned_comments)
        ),
        "iqr_info": iqr_info,
        "summary": summary,
    }
