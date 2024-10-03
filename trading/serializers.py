from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Candle, Bet, UserProfile, ChartType, ManualControl

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    balance = serializers.DecimalField(source='userprofile.balance', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'balance')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user

class ChartTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChartType
        fields = ('id', 'name', 'symbol')

class CandleSerializer(serializers.ModelSerializer):
    chart_type_symbol = serializers.CharField(source='chart_type.symbol', read_only=True)

    class Meta:
        model = Candle
        fields = ('id', 'chart_type', 'chart_type_symbol', 'time', 'open_price', 
                 'close_price', 'min_price', 'max_price')

    def validate(self, data):
        if data['min_price'] > data['max_price']:
            raise serializers.ValidationError("Minimum price cannot be greater than maximum price")
        if data['open_price'] < data['min_price'] or data['open_price'] > data['max_price']:
            raise serializers.ValidationError("Open price must be between minimum and maximum prices")
        if data['close_price'] < data['min_price'] or data['close_price'] > data['max_price']:
            raise serializers.ValidationError("Close price must be between minimum and maximum prices")
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserProfile
        fields = ('id', 'username', 'balance')
        read_only_fields = ('balance',)

class BetSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    chart_symbol = serializers.CharField(source='chart_type.symbol', read_only=True)
    
    class Meta:
        model = Bet
        fields = ('id', 'user', 'username', 'chart_type', 'chart_symbol', 'amount', 
                 'duration', 'prediction', 'created_at', 'result')
        read_only_fields = ('user', 'created_at', 'result')

    def validate_amount(self, value):
        user = self.context['request'].user
        if value > user.userprofile.balance:
            raise serializers.ValidationError("Insufficient funds")
        if value <= 0:
            raise serializers.ValidationError("Bet amount must be positive")
        return value

    def validate_duration(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Duration cannot be in the past")
        return value

class ManualControlSerializer(serializers.ModelSerializer):
    chart_name = serializers.CharField(source='chart_type.name', read_only=True)

    class Meta:
        model = ManualControl
        fields = ('id', 'chart_type', 'chart_name', 'time', 'value', 'created_at')
        read_only_fields = ('created_at',)

    def validate_time(self, value):
        min_time = timezone.now() - timezone.timedelta(days=1)
        max_time = timezone.now() + timezone.timedelta(minutes=1)
        
        if value < min_time:
            raise serializers.ValidationError("Time cannot be more than 1 day in the past")
        if value > max_time:
            raise serializers.ValidationError("Time cannot be more than 1 minute in the future")
        return value