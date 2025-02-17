from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import WasteReport, Pickup, EducationalResource, Notification, UserProfile, WasteReportMedia, CleanupTeam, PickupRequest, WasteCollector, EducationalContent, Quiz, QuizQuestion, UserQuizAttempt, ForumTopic, ForumComment, FAQ, CustomUser
from django.utils import timezone

class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'confirm_password')

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class WasteReportMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteReportMedia
        fields = ['id', 'media_type', 'file', 'uploaded_at']

class CleanupTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = CleanupTeam
        fields = '__all__'

class WasteReportSerializer(serializers.ModelSerializer):
    media = WasteReportMediaSerializer(many=True, read_only=True)
    uploaded_files = serializers.ListField(
        child=serializers.FileField(
            max_length=1000000,
            allow_empty_file=False,
            use_url=False
        ),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = WasteReport
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at', 'status')

    def create(self, validated_data):
        uploaded_files = validated_data.pop('uploaded_files', [])
        waste_report = WasteReport.objects.create(**validated_data)
        
        for file in uploaded_files:
            media_type = 'video' if file.content_type.startswith('video') else 'image'
            WasteReportMedia.objects.create(
                waste_report=waste_report,
                media_type=media_type,
                file=file
            )
        return waste_report

class PickupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pickup
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class EducationalResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationalResource
        fields = '__all__'
        read_only_fields = ('author', 'created_at', 'updated_at')

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('created_at',)

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ('id', 'username', 'email', 'phone_number', 'address', 'profile_picture')
        read_only_fields = ('user', 'id', 'username', 'email')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if not representation['phone_number']:
            representation['phone_number'] = ''
        if not representation['address']:
            representation['address'] = ''
        return representation

class UserDashboardSerializer(serializers.Serializer):
    reports_count = serializers.IntegerField()
    upcoming_pickups = PickupSerializer(many=True)
    recent_notifications = NotificationSerializer(many=True)
    educational_resources = EducationalResourceSerializer(many=True)

class AdminDashboardSerializer(serializers.Serializer):
    total_reports = serializers.IntegerField()
    pending_pickups = serializers.IntegerField()
    active_users = serializers.IntegerField()
    recent_reports = WasteReportSerializer(many=True)

class WasteCollectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteCollector
        fields = '__all__'

class PickupRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PickupRequest
        fields = '__all__'
        read_only_fields = ('user', 'status', 'collector', 'created_at', 'updated_at')

    def validate_pickup_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Pickup date cannot be in the past")
        return value

class PickupRequestDetailSerializer(PickupRequestSerializer):
    collector = WasteCollectorSerializer(read_only=True)

class PickupAnalyticsSerializer(serializers.Serializer):
    total_pickups = serializers.IntegerField()
    completed_pickups = serializers.IntegerField()
    pending_pickups = serializers.IntegerField()
    waste_type_distribution = serializers.DictField()
    completion_rate = serializers.FloatField()

class EducationalContentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = EducationalContent
        fields = '__all__'
        read_only_fields = ('author', 'views', 'slug')

class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = '__all__'
        extra_kwargs = {'correct_answer': {'write_only': True}}

class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Quiz
        fields = '__all__'

class UserQuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuizAttempt
        fields = '__all__'
        read_only_fields = ('user', 'score')

class ForumTopicSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ForumTopic
        fields = '__all__'           
        read_only_fields = ('author', 'is_approved', 'views')

class ForumCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = ForumComment
        fields = '__all__'
        read_only_fields = ('author', 'is_approved')

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'

class UserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'is_admin', 'created_at', 'is_active')
        read_only_fields = ('created_at',) 