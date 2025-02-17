from django.contrib import admin
from .models import (
    CustomUser,
    WasteReport,
    WasteReportMedia,
    CleanupTeam,
    Pickup,
    EducationalResource,
    Notification,
    UserProfile,
    PickupRequest,
    WasteCollector,
    EducationalContent,
    Quiz,
    QuizQuestion,
    UserQuizAttempt,
    ForumTopic,
    ForumComment,
    FAQ
)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_admin', 'created_at')
    search_fields = ('username', 'email')
    list_filter = ('is_admin', 'is_staff', 'created_at')

@admin.register(WasteReport)
class WasteReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'waste_type', 'status', 'created_at')
    list_filter = ('status', 'waste_type', 'created_at')
    search_fields = ('title', 'description', 'address')

@admin.register(WasteReportMedia)
class WasteReportMediaAdmin(admin.ModelAdmin):
    list_display = ('waste_report', 'media_type', 'uploaded_at')
    list_filter = ('media_type', 'uploaded_at')

@admin.register(CleanupTeam)
class CleanupTeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone_number', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'contact_person')

@admin.register(Pickup)
class PickupAdmin(admin.ModelAdmin):
    list_display = ('waste_report', 'scheduled_date', 'status')
    list_filter = ('status', 'scheduled_date')

@admin.register(EducationalResource)
class EducationalResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'content')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number')
    search_fields = ('user__username', 'phone_number', 'address')

@admin.register(PickupRequest)
class PickupRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'waste_type', 'pickup_date', 'status')
    list_filter = ('status', 'waste_type', 'pickup_date')
    search_fields = ('address', 'instructions')

@admin.register(WasteCollector)
class WasteCollectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'vehicle_number', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name', 'vehicle_number', 'phone_number')

@admin.register(EducationalContent)
class EducationalContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'author', 'is_published', 'views')
    list_filter = ('content_type', 'is_published', 'created_at')
    search_fields = ('title', 'description', 'content')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'description')

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'question', 'correct_answer')
    search_fields = ('question', 'correct_answer')

@admin.register(UserQuizAttempt)
class UserQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'completed_at')
    list_filter = ('completed_at',)

@admin.register(ForumTopic)
class ForumTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_approved', 'views', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('title', 'description')

@admin.register(ForumComment)
class ForumCommentAdmin(admin.ModelAdmin):
    list_display = ('topic', 'author', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('content',)

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('question', 'answer', 'category')