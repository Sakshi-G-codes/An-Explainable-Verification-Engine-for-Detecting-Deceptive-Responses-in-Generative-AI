from django.urls import path
from verification.views import VerifyAPIView, GenerateAndVerifyAPIView

urlpatterns = [
    path('verify/', VerifyAPIView.as_view(), name='verify'),
    path('generate-and-verify/', GenerateAndVerifyAPIView.as_view(), name='generate_and_verify'),
]
