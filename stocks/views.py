# stocks/views.py
from django.shortcuts import render
from django.contrib import messages
from .models import StockCommentAnalysis
from .pipeline.crawler import crawl_company_comments
from .services import process_comments_pipeline


def index(request):
    company_name = request.GET.get('company_name', '').strip()

    # F601: 입력값이 없는 경우 수집 절차를 수행하지 않음
    if not company_name:
        return render(request, 'stocks/index.html')

    # F601: VS Code 터미널에 입력한 회사명 출력
    print(company_name)

    # F603 & F604: 토스증권 회사 검색 및 댓글 20개 수집
    crawl_result = crawl_company_comments(company_name, max_count=20)
    actual_company = crawl_result.get('company')
    original_comments = crawl_result.get('comments', [])

    # F611 (심화): 회사 검색 결과가 없거나 댓글 데이터가 존재하지 않는 경우 안내 메시지 출력
    if not actual_company:
        messages.warning(request, f"'{company_name}'에 대한 회사 검색 결과가 존재하지 않습니다.")
        return render(request, 'stocks/index.html', {'searched_name': company_name})

    if not original_comments:
        messages.warning(request, f"'{actual_company}' 종목의 커뮤니티 댓글 데이터가 존재하지 않습니다.")
        return render(request, 'stocks/index.html', {'searched_name': company_name})

    # 팀원 B의 전처리 및 AI 증강 파이프라인 호출 (F605, F606, F610)
    pipeline_result = process_comments_pipeline(original_comments)
    cleaned_comments = pipeline_result.get('cleaned_comments', [])
    augmented_comments = pipeline_result.get('augmented_comments', [])
    iqr_info = pipeline_result.get('iqr_info', {})
    summary = pipeline_result.get('summary', '')

    # F602 & F607: 각 단계의 결과를 DB에 저장
    record = StockCommentAnalysis.objects.create(
        company_name=actual_company,
        original_comments=original_comments,
        cleaned_comments=cleaned_comments,
        augmented_comments=augmented_comments,
        iqr_threshold=iqr_info,
    )

    context = {
        'searched_name': company_name,
        'company': actual_company,
        'original_comments': original_comments,
        'cleaned_comments': cleaned_comments,
        'augmented_comments': augmented_comments,
        'final_comments': cleaned_comments + augmented_comments,
        'iqr_info': iqr_info,
        'summary': summary,
        'record': record,
    }
    return render(request, 'stocks/results.html', context)