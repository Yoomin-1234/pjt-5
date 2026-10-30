
from django.shortcuts import render
from django.contrib import messages

from .models import StockCommentAnalysis
from .pipeline.crawler import crawl_company_comments
from .services import process_comments_pipeline


def index(request):
    company_name = request.GET.get(
        'company_name', ''
    ).strip()

    # 회사명이 입력되지 않은 경우
    if not company_name:
        return render(request, 'stocks/index.html')

    print(f"입력된 회사명: {company_name}")

    # 1. F604: 커뮤니티 게시글 수집
    crawl_result = crawl_company_comments(
        company_name,
        max_count=20
    )

    actual_company = crawl_result.get('company')
    original_comments = crawl_result.get(
        'comments', []
    )

    # 2. F611: 회사 검색 결과 확인
    if not actual_company:
        messages.warning(
            request,
            f"'{company_name}'에 대한 회사 검색 결과가 없습니다."
        )

        return render(
            request,
            'stocks/index.html',
            {'searched_name': company_name}
        )

    # 3. F611: 댓글 데이터 존재 여부 확인
    if not original_comments:
        messages.warning(
            request,
            f"'{actual_company}' 종목의 커뮤니티 댓글 데이터가 없습니다."
        )

        return render(
            request,
            'stocks/index.html',
            {'searched_name': company_name}
        )

    # 4. F605, F606, F610:
    # 기본 전처리 -> LLM 필터링 -> 증강 -> 요약
    try:
        pipeline_result = process_comments_pipeline(
            original_comments
        )

    except Exception as e:
        print(f"[Pipeline Error]: {e}")

        messages.error(
            request,
            "댓글 분석 중 오류가 발생했습니다. "
            "GMS API 설정 및 연결 상태를 확인해주세요."
        )

        return render(
            request,
            'stocks/index.html',
            {'searched_name': company_name}
        )

    # 5. 처리 결과 가져오기
    cleaned_comments = pipeline_result.get(
        'cleaned_comments', []
    )

    augmented_comments = pipeline_result.get(
        'augmented_comments', []
    )

    iqr_info = pipeline_result.get(
        'iqr_info', {}
    )

    summary = pipeline_result.get(
        'summary', ''
    )

    # 6. F602, F607: DB 저장
    record = StockCommentAnalysis.objects.create(
        company_name=actual_company,
        original_comments=original_comments,
        cleaned_comments=cleaned_comments,
        augmented_comments=augmented_comments,
        iqr_threshold=iqr_info,
    )

    print("\n========== 최종 분석 결과 ==========")
    print("회사명:", actual_company)
    print("원본 댓글 수:", len(original_comments))
    print("정제 댓글 수:", len(cleaned_comments))
    print("증강 댓글 수:", len(augmented_comments))
    print("요약:", summary)

    # 7. 결과 페이지에 전달
    context = {
        'searched_name': company_name,
        'company': actual_company,
        'original_comments': original_comments,
        'cleaned_comments': cleaned_comments,
        'augmented_comments': augmented_comments,
        'iqr_info': iqr_info,
        'summary': summary,
        'record': record,

        # 전처리 결과 통계
        'original_count': pipeline_result.get(
            'original_count', 0
        ),
        'basic_cleaned_count': pipeline_result.get(
            'basic_cleaned_count', 0
        ),
        'cleaned_count': pipeline_result.get(
            'cleaned_count', 0
        ),
        'removed_count': pipeline_result.get(
            'removed_count', 0
        ),
        'llm_removed_count': pipeline_result.get(
            'llm_removed_count', 0
        ),
    }

    return render(
        request,
        'stocks/results.html',
        context
    )
