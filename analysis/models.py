from django.db import models

# Create your models here.
class TossCommentAnalysis(models.Model):
    company_name = models.CharField(max_length=100, verbose_name="실제종목명")
    original_comments = models.JSONField(verbose_name="원본 댓글 목록")
    cleaned_comments = models.JSONField(verbose_name="정제 댓글 목록")
    augmented_comments = models.JSONField(verbose_name="증강 댓글 목록")
    iqr_threshold = models.CharField(max_length=50, null=True, blank=True, verbose_name="IQR 임계값 정보")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 일시")

    def __str__(self):
        return f"{self.company_name} - {self.created_at}"