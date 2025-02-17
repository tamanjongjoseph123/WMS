from django.shortcuts import render
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q, F
from .models import WasteReport, Pickup, EducationalResource, Notification, UserProfile, WasteReportMedia, CleanupTeam, PickupRequest, WasteCollector, EducationalContent, Quiz, QuizQuestion, UserQuizAttempt, ForumTopic, ForumComment, FAQ, CustomUser
from .serializers import (
    WasteReportSerializer, PickupSerializer, EducationalResourceSerializer,
    NotificationSerializer, UserProfileSerializer, UserDashboardSerializer,
    AdminDashboardSerializer, CleanupTeamSerializer,
    PickupRequestSerializer, PickupRequestDetailSerializer,
    WasteCollectorSerializer, PickupAnalyticsSerializer,
    EducationalContentSerializer, QuizSerializer, QuizQuestionSerializer,
    UserQuizAttemptSerializer, ForumTopicSerializer, ForumCommentSerializer,
    FAQSerializer, SignUpSerializer, LoginSerializer, UserAdminSerializer
)
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from datetime import timedelta
import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .permissions import IsAdminUser
from django.db.utils import IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your views here.

class UserDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        current_date = timezone.now()
        thirty_days_ago = current_date - timedelta(days=30)

        # Get waste reports with detailed tracking
        reports = WasteReport.objects.filter(user=user)
        
        # Recent reports (last 30 days)
        recent_reports = reports.filter(
            created_at__gte=thirty_days_ago
        ).order_by('-created_at')

        # Reports by status
        reports_by_status = reports.values('status').annotate(count=Count('id'))
        
        # Reports by waste type
        reports_by_type = reports.values('waste_type').annotate(count=Count('id'))
        
        # Monthly report statistics
        monthly_reports = reports.filter(
            created_at__gte=thirty_days_ago
        ).count()

        # Status breakdown
        pending_reports = reports.filter(status='pending').count()
        in_progress_reports = reports.filter(status='in_progress').count()
        completed_reports = reports.filter(status='completed').count()
        
        # Reports requiring attention (pending for more than 7 days)
        attention_needed = reports.filter(
            status='pending',
            created_at__lte=current_date - timedelta(days=7)
        ).count()

        # Get reports with recent updates
        recently_updated = reports.filter(
            updated_at__gte=current_date - timedelta(days=7)
        ).exclude(
            created_at=F('updated_at')  # Exclude newly created reports
        ).order_by('-updated_at')[:5]

        # Get upcoming pickups
        upcoming_pickups = PickupRequest.objects.filter(
            user=user,
            pickup_date__gte=current_date.date(),
            status__in=['pending', 'scheduled', 'in_progress']
        ).order_by('pickup_date', 'pickup_time')

        # Get past pickups
        past_pickups = PickupRequest.objects.filter(
            user=user,
            pickup_date__lt=current_date.date()
        ).order_by('-pickup_date', '-pickup_time')

        # Get pickup statistics
        all_pickups = PickupRequest.objects.filter(user=user)
        total_pickups = all_pickups.count()
        completed_pickups = all_pickups.filter(status='completed').count()
        pending_pickups = all_pickups.filter(status__in=['pending', 'scheduled']).count()

        # Get educational resources
        educational_resources = EducationalContent.objects.filter(
            is_published=True
        ).order_by('-created_at')

        # Get resources by type
        articles = educational_resources.filter(content_type='article')[:3]
        videos = educational_resources.filter(content_type='video')[:2]
        
        # Get user's recent quiz attempts
        recent_quiz_attempts = UserQuizAttempt.objects.filter(
            user=user
        ).order_by('-created_at')[:3]

        # Get recent notifications
        recent_notifications = Notification.objects.filter(
            user=user,
            created_at__gte=current_date - timedelta(days=7)
        ).order_by('-created_at')[:5]

        # Get user profile
        profile = UserProfile.objects.filter(user=user).first()

        # Get notifications
        recent_notifications = Notification.objects.filter(
            user=user
        ).order_by('-created_at')[:10]  # Get last 10 notifications

        unread_notifications = Notification.objects.filter(
            user=user,
            is_read=False
        ).count()

        notifications_by_type = Notification.objects.filter(
            user=user
        ).values('notification_type').annotate(
            count=Count('id')
        )

        return Response({
            'user_info': {
                'username': user.username,
                'email': user.email,
                'phone_number': profile.phone_number if profile else None,
                'address': profile.address if profile else None
            },
            'reports_summary': {
                'total_reports': reports.count(),
                'reports_by_status': reports_by_status,
                'reports_by_type': reports_by_type,
                'recent_reports': WasteReportSerializer(recent_reports[:5], many=True).data
            },
            'waste_tracking': {
                'monthly_statistics': {
                    'total_reports': monthly_reports,
                    'resolution_rate': f"{(completed_reports/reports.count() * 100) if reports.count() > 0 else 0:.1f}%"
                },
                'status_breakdown': {
                    'pending': pending_reports,
                    'in_progress': in_progress_reports,
                    'completed': completed_reports,
                    'attention_needed': attention_needed
                },
                'recent_updates': WasteReportSerializer(recently_updated, many=True).data,
                'timeline': {
                    'last_30_days': monthly_reports,
                    'pending_over_7_days': attention_needed
                }
            },
            'pickups_summary': {
                'upcoming_pickups': PickupRequestSerializer(upcoming_pickups, many=True).data,
                'past_pickups': PickupRequestSerializer(past_pickups, many=True).data,
                'statistics': {
                    'total_pickups': total_pickups,
                    'completed_pickups': completed_pickups,
                    'pending_pickups': pending_pickups,
                    'completion_rate': f"{(completed_pickups/total_pickups * 100) if total_pickups > 0 else 0:.1f}%"
                }
            },
            'notifications': {
                'recent': NotificationSerializer(recent_notifications, many=True).data,
                'unread_count': unread_notifications,
                'by_type': notifications_by_type,
                'has_new': unread_notifications > 0
            },
            'educational_resources': EducationalContentSerializer(educational_resources, many=True).data
        })

class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        data = {
            'total_reports': WasteReport.objects.count(),
            'pending_pickups': Pickup.objects.filter(
                status__in=['scheduled', 'in_progress']
            ).count(),
            'active_users': User.objects.filter(
                wastereport__created_at__gte=timezone.now() - timezone.timedelta(days=30)
            ).distinct().count(),
            'recent_reports': WasteReport.objects.all()
                .order_by('-created_at')[:10]
        }
        serializer = AdminDashboardSerializer(data)
        return Response(serializer.data)

class WasteReportViewSet(viewsets.ModelViewSet):
    serializer_class = WasteReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def get_queryset(self):
        if not self.request.user.is_staff:
            return WasteReport.objects.filter(user=self.request.user)
        return WasteReport.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def assign_team(self, request, pk=None):
        if not request.user.is_staff:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        report = self.get_object()
        team_id = request.data.get('team_id')
        
        try:
            team = CleanupTeam.objects.get(id=team_id)
            report.assigned_team = team
            report.status = 'in_progress'
            report.save()
            
            # Create notification for user
            Notification.objects.create(
                user=report.user,
                title='Cleanup Team Assigned',
                message=f'A cleanup team has been assigned to your report: {report.title}',
                notification_type='report'
            )
            
            return Response({'status': 'Team assigned successfully'})
        except CleanupTeam.DoesNotExist:
            return Response(
                {'error': 'Team not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        if not request.user.is_staff:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Get reports from last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        waste_type_stats = WasteReport.objects.filter(
            created_at__gte=thirty_days_ago
        ).values('waste_type').annotate(
            count=Count('id')
        )
        
        status_stats = WasteReport.objects.filter(
            created_at__gte=thirty_days_ago
        ).values('status').annotate(
            count=Count('id')
        )
        
        return Response({
            'waste_type_distribution': waste_type_stats,
            'status_distribution': status_stats,
        })

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        if not request.user.is_staff:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="waste_reports.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Title', 'Description', 'Waste Type', 'Status',
            'Location', 'Created At', 'Updated At'
        ])
        
        reports = self.get_queryset()
        for report in reports:
            writer.writerow([
                report.id, report.title, report.description,
                report.waste_type, report.status, report.address,
                report.created_at, report.updated_at
            ])
            
        return response

    @action(detail=True, methods=['get'])
    def tracking_history(self, request, pk=None):
        report = self.get_object()
        
        # Get related notifications for this report
        notifications = Notification.objects.filter(
            user=request.user,
            notification_type__in=['waste_report', 'status_update'],
            reference_id=report.id
        ).order_by('created_at')

        # Create timeline of events
        timeline = []
        
        # Add report creation
        timeline.append({
            'date': report.created_at,
            'event': 'Report Created',
            'details': f"Waste report '{report.title}' was submitted"
        })

        # Add status updates from notifications
        for notification in notifications:
            if notification.notification_type == 'status_update':
                timeline.append({
                    'date': notification.created_at,
                    'event': 'Status Updated',
                    'details': notification.message
                })

        return Response({
            'report_details': WasteReportSerializer(report).data,
            'timeline': timeline,
            'days_since_creation': (timezone.now() - report.created_at).days,
            'current_status': report.status,
            'last_updated': report.updated_at
        })

class PickupViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PickupSerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Pickup.objects.all()
        return Pickup.objects.filter(waste_report__user=self.request.user)

class EducationalResourceViewSet(viewsets.ModelViewSet):
    queryset = EducationalResource.objects.all()
    serializer_class = EducationalResourceSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_queryset(self):
        # Get or create the user profile
        profile, created = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                'phone_number': '',
                'address': ''
            }
        )
        return UserProfile.objects.filter(user=self.request.user)

    def get_object(self):
        # Get or create the profile when accessing a single object
        profile, created = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                'phone_number': '',
                'address': ''
            }
        )
        return profile

    def perform_create(self, serializer):
        # Check if profile already exists
        if UserProfile.objects.filter(user=self.request.user).exists():
            raise serializers.ValidationError("Profile already exists for this user")
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class CleanupTeamViewSet(viewsets.ModelViewSet):
    queryset = CleanupTeam.objects.all()
    serializer_class = CleanupTeamSerializer
    permission_classes = [permissions.IsAdminUser]

class PickupRequestViewSet(viewsets.ModelViewSet):
    serializer_class = PickupRequestSerializer
    
    def get_queryset(self):
        queryset = PickupRequest.objects.all()
        if not self.request.user.is_staff:
            return queryset.filter(user=self.request.user)
            
        # Admin filters
        status = self.request.query_params.get('status', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        waste_type = self.request.query_params.get('waste_type', None)
        
        if status:
            queryset = queryset.filter(status=status)
        if date_from:
            queryset = queryset.filter(pickup_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(pickup_date__lte=date_to)
        if waste_type:
            queryset = queryset.filter(waste_type=waste_type)
            
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PickupRequestDetailSerializer
        return PickupRequestSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def assign_collector(self, request, pk=None):
        if not request.user.is_staff:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        pickup = self.get_object()
        collector_id = request.data.get('collector_id')
        
        try:
            collector = WasteCollector.objects.get(id=collector_id, is_available=True)
            pickup.collector = collector
            pickup.status = 'scheduled'
            pickup.save()
            
            # Create notification
            Notification.objects.create(
                user=pickup.user,
                title='Pickup Scheduled',
                message=f'Your pickup request has been scheduled for {pickup.pickup_date}',
                notification_type='pickup'
            )
            
            return Response({'status': 'Collector assigned successfully'})
        except WasteCollector.DoesNotExist:
            return Response(
                {'error': 'Collector not found or not available'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        if not request.user.is_staff:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        total_pickups = PickupRequest.objects.count()
        completed_pickups = PickupRequest.objects.filter(status='completed').count()
        pending_pickups = PickupRequest.objects.filter(
            status__in=['pending', 'scheduled']
        ).count()
        
        waste_type_distribution = PickupRequest.objects.values(
            'waste_type'
        ).annotate(count=Count('id'))
        
        completion_rate = (completed_pickups / total_pickups * 100) if total_pickups > 0 else 0
        
        data = {
            'total_pickups': total_pickups,
            'completed_pickups': completed_pickups,
            'pending_pickups': pending_pickups,
            'waste_type_distribution': {
                item['waste_type']: item['count'] 
                for item in waste_type_distribution
            },
            'completion_rate': completion_rate
        }
        
        serializer = PickupAnalyticsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        if not request.user.is_staff:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="pickup_requests.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'User', 'Waste Type', 'Pickup Date', 'Status',
            'Address', 'Collector', 'Created At'
        ])
        
        pickups = self.get_queryset()
        for pickup in pickups:
            writer.writerow([
                pickup.id,
                pickup.user.username,
                pickup.waste_type,
                pickup.pickup_date,
                pickup.status,
                pickup.address,
                pickup.collector.name if pickup.collector else 'Not Assigned',
                pickup.created_at
            ])
            
        return response

class WasteCollectorViewSet(viewsets.ModelViewSet):
    queryset = WasteCollector.objects.all()
    serializer_class = WasteCollectorSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=True, methods=['post'])
    def update_location(self, request, pk=None):
        collector = self.get_object()
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        if latitude and longitude:
            collector.current_location_lat = latitude
            collector.current_location_lng = longitude
            collector.save()
            return Response({'status': 'Location updated successfully'})
        return Response(
            {'error': 'Latitude and longitude are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

class EducationalContentViewSet(viewsets.ModelViewSet):
    serializer_class = EducationalContentSerializer
    
    def get_queryset(self):
        queryset = EducationalContent.objects.all()
        if not self.request.user.is_admin:
            queryset = queryset.filter(is_published=True)
            
        content_type = self.request.query_params.get('type', None)
        if content_type:
            queryset = queryset.filter(content_type=content_type)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views = F('views') + 1
        instance.save()
        return super().retrieve(request, *args, **kwargs)

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['post'])
    def submit_attempt(self, request, pk=None):
        quiz = self.get_object()
        answers = request.data.get('answers', {})
        
        correct_answers = 0
        total_questions = quiz.questions.count()
        
        for question_id, answer in answers.items():
            try:
                question = QuizQuestion.objects.get(id=question_id, quiz=quiz)
                if question.correct_answer.lower() == answer.lower():
                    correct_answers += 1
            except QuizQuestion.DoesNotExist:
                pass
        
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        UserQuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=score
        )
        
        return Response({
            'score': score,
            'correct_answers': correct_answers,
            'total_questions': total_questions
        })

class ForumTopicViewSet(viewsets.ModelViewSet):
    serializer_class = ForumTopicSerializer
    
    def get_queryset(self):
        queryset = ForumTopic.objects.annotate(
            comments_count=Count('comments')
        )
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_approved=True)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        topic = self.get_object()
        serializer = ForumCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                author=request.user,
                topic=topic,
                is_approved=request.user.is_staff
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

# Authentication Views
class SignUpView(APIView):
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'User created successfully',
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            if user is not None:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                })
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminUserManagementView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        if not request.user.is_admin:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        users = CustomUser.objects.all().order_by('-created_at')
        serializer = UserAdminSerializer(users, many=True)
        return Response(serializer.data)

    def patch(self, request, user_id):
        if not request.user.is_admin:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = CustomUser.objects.get(id=user_id)
            serializer = UserAdminSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class AdminDashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get statistics for the dashboard
        total_users = CustomUser.objects.count()
        total_waste_reports = WasteReport.objects.count()
        total_pickups = PickupRequest.objects.count()
        recent_users = CustomUser.objects.order_by('-created_at')[:5]
        
        # Get waste reports by status
        waste_reports_by_status = WasteReport.objects.values('status').annotate(
            count=Count('id')
        )
        
        # Get pickups by status
        pickups_by_status = PickupRequest.objects.values('status').annotate(
            count=Count('id')
        )

        return Response({
            'total_users': total_users,
            'total_waste_reports': total_waste_reports,
            'total_pickups': total_pickups,
            'recent_users': UserAdminSerializer(recent_users, many=True).data,
            'waste_reports_by_status': waste_reports_by_status,
            'pickups_by_status': pickups_by_status
        })
