import json
from openai import OpenAI
from django.conf import settings


def _get_llm_client():

    if not settings.GMS_API_KEY:
        raise ValueError(
            "GMS API 키가 설정되지 않았습니다."
        )

    return OpenAI(
        api_key=settings.GMS_API_KEY,
        base_url=settings.GMS_BASE_URL,
        timeout=30.0,
        max_retries=1,
    )


def _request_llm(messages, json_mode=False):

    client = _get_llm_client()

    params = {
        "model": settings.GMS_MODEL,
        "messages": messages,
    }

    if json_mode:
        params["response_format"] = {
            "type": "json_object"
        }

    response = client.chat.completions.create(
        **params
    )

    content = response.choices[0].message.content

    if not content or not content.strip():
        raise ValueError("LLM 응답이 비어 있습니다.")

    return content.strip()


def filter_bad_comments_with_llm(comments):
 

    if not comments:
        return []

    numbered_comments = "\n".join(
        f"[{idx}] {comment}"
        for idx, comment in enumerate(comments)
    )

    prompt = f"""
다음은 주식 커뮤니티 댓글입니다.

욕설, 혐오, 심한 비방, 선정성,
과도한 인신공격 등이 포함된
부적절한 댓글의 인덱스를 골라주세요.

부정적인 주식 전망이나 정상적인 비판은
부적절한 댓글로 판단하지 마세요.

반드시 다음 JSON 객체 형식으로 답하세요.

{{"bad_indices": [0, 2]}}

댓글:
{numbered_comments}
"""

    result = _request_llm(
        [
            {
                "role": "system",
                "content": (
                    "댓글의 적절성을 판단하는 필터입니다. "
                    "JSON 객체만 반환하세요."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        json_mode=True,
    )

    data = json.loads(result)

    bad_indices = data.get("bad_indices")

    if not isinstance(bad_indices, list):
        raise ValueError(
            "LLM의 bad_indices 형식이 올바르지 않습니다."
        )

    if any(
        type(idx) is not int
        or not 0 <= idx < len(comments)
        for idx in bad_indices
    ):
        raise ValueError(
            "LLM이 잘못된 댓글 인덱스를 반환했습니다."
        )

    excluded = set(bad_indices)

    return [
        comment
        for idx, comment in enumerate(comments)
        if idx not in excluded
    ]


def call_gms_llm_api(comment):


    prompt = f"""
다음 주식 커뮤니티 댓글을 자연스럽게 확장하세요.

규칙:
1. 원래 댓글의 의미와 감정을 유지하세요.
2. 없는 사실이나 수치를 만들어내지 마세요.
3. 투자 조언을 추가하지 마세요.
4. 한 문장 또는 두 문장으로 작성하세요.
5. 설명 없이 확장된 문장만 출력하세요.

원본 댓글:
{comment}
"""

    return _request_llm(
        [
            {
                "role": "system",
                "content": (
                    "원문 의미를 보존하며 "
                    "문장을 자연스럽게 확장하는 도우미입니다."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]
    )


def summarize_comments(comments):

    if not comments:
        return ""

    comments_text = "\n".join(
        f"- {comment}" for comment in comments
    )

    prompt = f"""
다음 주식 커뮤니티 댓글의 주요 반응을
2~3문장으로 객관적으로 요약하세요.

규칙:
1. 긍정적/부정적 반응을 균형 있게 설명하세요.
2. 댓글에서 확인되지 않은 사실은 추가하지 마세요.
3. 투자 추천이나 매매 지시는 하지 마세요.
4. 핵심 반응만 간결하게 작성하세요.

댓글 목록:
{comments_text}
"""

    return _request_llm(
        [
            {
                "role": "system",
                "content": (
                    "주식 커뮤니티 여론을 "
                    "중립적으로 요약하는 도우미입니다."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]
    )
