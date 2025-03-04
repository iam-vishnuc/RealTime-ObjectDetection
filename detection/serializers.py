from rest_framework import serializers

class DetectionResultSerializer(serializers.Serializer):
    name = serializers.CharField()
    confidence = serializers.FloatField()
    x1 = serializers.IntegerField()
    y1 = serializers.IntegerField()
    x2 = serializers.IntegerField()
    y2 = serializers.IntegerField()