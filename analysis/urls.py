from django.urls import path
from . import views

urlpatterns = [
    # 기본 경로('/') 접속 시 views.py의 analyze_comments 함수 실행
    path('', views.analyze_comments, name='analyze'),
]