# serializers.py
from rest_framework import serializers
from .models import ReportReply

class ReportReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportReply
        fields = ['id', 'report', 'sender', 'message', 'created_at']
