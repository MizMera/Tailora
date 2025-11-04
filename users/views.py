from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, StyleProfile, Notification
from .serializers import (
    UserSerializer, 
    UserRegistrationSerializer, 
    StyleProfileSerializer,
    NotificationSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management
    Provides CRUD operations for user profiles
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """
        Allow registration without authentication
        """
        if self.action == 'create':
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        """
        Use registration serializer for create action
        """
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
    def get_queryset(self):
        """
        Users can only access their own profile
        """
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """
        Get or update current user profile
        GET /api/users/me/
        PUT /api/users/me/
        """
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        else:
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        """
        Login endpoint with JWT token generation
        POST /api/users/login/
        Body: {"email": "user@example.com", "password": "password"}
        """
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email et mot de passe requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=email, password=password)
        
        if user is None:
            return Response(
                {'error': 'Identifiants invalides'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })


class StyleProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for style profile management
    """
    queryset = StyleProfile.objects.all()
    serializer_class = StyleProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Users can only access their own style profile
        """
        return StyleProfile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """
        Automatically associate style profile with current user
        """
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get', 'put', 'patch', 'post'])
    def me(self, request):
        """
        Get or update current user's style profile
        Creates one if it doesn't exist
        GET/PUT /api/style-profiles/me/
        """
        try:
            profile = StyleProfile.objects.get(user=request.user)
            
            if request.method == 'GET':
                serializer = self.get_serializer(profile)
                return Response(serializer.data)
            else:
                serializer = self.get_serializer(profile, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
        except StyleProfile.DoesNotExist:
            if request.method == 'GET':
                return Response(
                    {'error': 'Profil de style non trouvé'},
                    status=status.HTTP_404_NOT_FOUND
                )
            else:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for notifications
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Users can only see their own notifications
        """
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark notification as read
        POST /api/notifications/{id}/mark_read/
        """
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marquée comme lue'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        Mark all notifications as read
        POST /api/notifications/mark_all_read/
        """
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'toutes les notifications marquées comme lues'})
