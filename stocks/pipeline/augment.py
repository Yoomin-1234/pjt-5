
# stocks/pipeline/augment.py

from .llm import call_gms_llm_api


def augment_comments(cleaned_comments):

    augmented_comments = []

    for comment in cleaned_comments:

        if not isinstance(comment, str):
            continue

        if not comment.strip():
            continue

        # GMS LLM API를 활용한 댓글 증강
        augmented = call_gms_llm_api(comment)

        if not isinstance(augmented, str):
            raise ValueError(
                "증강 결과가 문자열이 아닙니다."
            )

        if not augmented.strip():
            raise ValueError(
                "증강 결과가 비어 있습니다."
            )

        augmented_comments.append(augmented.strip())

    return augmented_comments
