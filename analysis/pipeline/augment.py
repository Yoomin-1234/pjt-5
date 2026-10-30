# analysis/pipeline/augment.py
from .llm import call_gms_llm_api

def augment_comments(cleaned_comments):
    augmented = []
    for comment in cleaned_comments:
        prompt = f"다음 주식 커뮤니티 댓글의 의미를 유지하면서 문장을 조금 더 풍성하고 자연스럽게 확장해줘: '{comment}'"
        result = call_gms_llm_api(prompt)
        augmented.append(result)
    return augmented