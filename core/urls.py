from django.urls import path
from .views import SignUpView, LoginView, AdminUserManagementView, AdminDashboardStatsView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import (
    WasteReportViewSet, PickupViewSet, EducationalResourceViewSet,
    NotificationViewSet, UserProfileViewSet, UserDashboardView,
    AdminDashboardView, CleanupTeamViewSet, PickupRequestViewSet,
    WasteCollectorViewSet, EducationalContentViewSet, QuizViewSet,
    ForumTopicViewSet, FAQViewSet
)

router = DefaultRouter()
router.register(r'waste-reports', WasteReportViewSet, basename='waste-report')
router.register(r'pickups', PickupViewSet, basename='pickup')
router.register(r'educational-resources', EducationalResourceViewSet, basename='educational-resource')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'cleanup-teams', CleanupTeamViewSet, basename='cleanup-team')
router.register(r'pickup-requests', PickupRequestViewSet, basename='pickup-request')
router.register(r'waste-collectors', WasteCollectorViewSet, basename='waste-collector')
router.register(r'educational-content', EducationalContentViewSet, basename='educational-content')
router.register(r'quizzes', QuizViewSet, basename='quiz')
router.register(r'forum-topics', ForumTopicViewSet, basename='forum-topic')
router.register(r'faqs', FAQViewSet, basename='faq')

urlpatterns = [
    path('auth/signup/', SignUpView.as_view(), name='signup'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('dashboard/user/', UserDashboardView.as_view(), name='user-dashboard'),
    path('dashboard/admin/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin/users/', AdminUserManagementView.as_view(), name='admin-users'),
    path('admin/users/<int:user_id>/', AdminUserManagementView.as_view(), name='admin-user-detail'),
    path('admin/dashboard/stats/', AdminDashboardStatsView.as_view(), name='admin-dashboard-stats'),
] + router.urls 