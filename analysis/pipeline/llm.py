# analysis/pipeline/llm.py
import json
from openai import OpenAI
from django.conf import settings

def _get_llm_client():
    """GMS API 클라이언트를 초기화하여 반환하는 내부 함수"""
    api_key = getattr(settings, 'GMS_API_KEY', '')
    if not api_key:
        print("[Warning] GMS_API_KEY가 설정되어 있지 않습니다.")
        return None
    return OpenAI(
        api_key=api_key,
        base_url='https://gms.ssafy.io/gmsapi/api.openai.com/v1',
    )


def call_gms_llm_api(prompt):
    """(F606) 단순 텍스트 증강용 LLM 호출 함수"""
    client = _get_llm_client()
    if not client:
        return prompt  # 키가 없으면 원본 그대로 반환

    try:
        response = client.chat.completions.create(
            model='gpt-5-nano',
            messages=[
                {'role': 'system', 'content': '당신은 주식 커뮤니티 댓글의 맥락을 살려 문장을 자연스럽게 확장해주는 주식 전문가입니다.'},
                {'role': 'user', 'content': prompt},
            ],
            timeout=10,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM Augment Error: {e}")
        return prompt


def filter_bad_comments_with_llm(comments):
    """
    (F605) 부적절한 댓글 필터링: 
    입력된 댓글 리스트 중 욕설, 비방 등 부적절한 댓글의 인덱스를 JSON 배열로 받아 제외함
    """
    client = _get_llm_client()
    if not client or not comments:
        return comments

    # 댓글 리스트를 인덱스와 함께 프롬프트에 전달
    comments_text = "\n".join([f"[{i}] {c}" for i, c in enumerate(comments)])
    prompt = (
        f"다음 댓글 목록에서 부적절한 댓글(욕설, 혐오, 비방, 선정성, 과도한 비난 등)의 번호만 JSON 배열로 알려줘.\n"
        f"형식: {{\"bad_indices\": [0, 2]}}\n\n"
        f"{comments_text}"
    )

    try:
        response = client.chat.completions.create(
            model='gpt-5-nano',
            messages=[
                {'role': 'system', 'content': '반드시 유효한 JSON 객체만 출력하는 텍스트 필터링 봇입니다.'},
                {'role': 'user', 'content': prompt},
            ],
            response_format={'type': 'json_object'},
            timeout=10,
        )
        parsed = json.loads(response.choices[0].message.content)
        bad_indices = parsed.get("bad_indices", [])
        
        # 부적절한 인덱스를 제외한 깨끗한 댓글만 필터링
        return [c for i, c in enumerate(comments) if i not in bad_indices]
    except Exception as e:
        print(f"LLM Filter Error: {e}")
        return comments


def summarize_comments(comments):
    """(F610 심화) 전체 댓글을 기반으로 요약 텍스트 생성"""
    client = _get_llm_client()
    if not client or not comments:
        return ""

    comments_text = "\n".join(comments)
    prompt = (
        f"다음은 특정 종목에 대한 주식 커뮤니티 댓글 모음입니다.\n\n{comments_text}\n\n"
        f"이 댓글들의 주요 반응과 분위기를 2~3문장으로 간결하게 요약해줘."
    )

    try:
        response = client.chat.completions.create(
            model='gpt-5-nano',
            messages=[
                {'role': 'system', 'content': '주식 시장의 투자자 반응을 객관적으로 분석하고 요약하는 전문가입니다.'},
                {'role': 'user', 'content': prompt},
            ],
            timeout=10,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM Summarize Error: {e}")
        return "댓글 요약 생성에 실패했습니다."