# analysis/pipeline/preprocess.py
import re
from .llm import filter_bad_comments_with_llm # 압축파일의 llm.py 활용

def preprocess_comments(comments):
    cleaned = []
    for comment in comments:
        # 1. 특수문자 및 불필요한 패턴 제거
        text = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', comment)
        text = re.sub(r'ㅋ+', '', text)
        
        # 2. 길이 필터링 (5이상 ~ 76이하)
        text = text.strip()
        if 5 <= len(text) <= 76:
            cleaned.append(text)
            
    # 3. LLM을 활용한 부적절한 댓글 제거[cite: 132]
    # filter_bad_comments_with_llm 함수는 프롬프트로 부적절한 인덱스를 JSON 배열로 받아 제외하는 로직을 포함해야 합니다.
    final_cleaned = filter_bad_comments_with_llm(cleaned) 
    
    return final_cleaned