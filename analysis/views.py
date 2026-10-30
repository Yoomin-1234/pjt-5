from django.shortcuts import render
from django.contrib import messages
from .models import TossCommentAnalysis
from .pipeline.crawler import crawl_toss_comments
from .pipeline.preprocess import preprocess_comments
from .pipeline.augment import augment_comments
from .pipeline.llm import summarize_comments

# Create your views here.

def analyze_comments(request):
    if request.method == "GET":
        company_name = request.GET.get('company_name')
        
        # F601: 회사명 입력 검증[cite: 127]
        if not company_name:
            return render(request, 'analysis/index.html')
            
        print(f"입력된 회사명: {company_name}") # 터미널 출력 요구사항
        
        # 1. 크롤링 (F603, F604)
        actual_name, original_comments = crawl_toss_comments(company_name)
        
        # F611: 데이터가 없는 경우 예외 처리[cite: 134]
        if not original_comments:
            messages.warning(request, "회사 검색 결과가 없거나 댓글 데이터가 존재하지 않습니다.")
            return render(request, 'analysis/index.html')
            
        # 2. 전처리 (F605)
        cleaned_comments = preprocess_comments(original_comments)
        
        # 3. 데이터 증강 (F606)
        augmented_comments = augment_comments(cleaned_comments)
        
        # 4. DB 저장 (F602)
        analysis_record = TossCommentAnalysis.objects.create(
            company_name=actual_name,
            original_comments=original_comments,
            cleaned_comments=cleaned_comments,
            augmented_comments=augmented_comments
        )
        
        # 심화 F610: 전체 댓글 요약[cite: 134]
        summary = summarize_comments(cleaned_comments)

        context = {
            'record': analysis_record,
            'summary': summary,
            'company_name': actual_name
        }
        
        return render(request, 'analysis/result.html', context)