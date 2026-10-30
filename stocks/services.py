# stocks/services.py (팀원 B 담당 - 통합 전까지 임시 반환용)
def process_comments_pipeline(comments):
    """
    팀원 A가 수집한 comments(리스트)를 받아
    정제 댓글, 증강 댓글, IQR 정보, 요약문을 반환하는 인터페이스
    """
    return {
        'cleaned_comments': comments,
        'augmented_comments': [],
        'iqr_info': {'lower_bound': 5, 'upper_bound': 76},
        'summary': '',
    }