from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from users.models import User, StyleProfile


@csrf_protect
def login_view(request):
    """
    Login view - handles user authentication
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        if not email or not password:
            messages.error(request, 'Veuillez fournir un email et un mot de passe.')
            return render(request, 'login.html')
        
        # Authenticate using email
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            user = None
        
        if user is not None:
            auth_login(request, user)
            
            # Handle remember me
            if not remember_me:
                # Session expires when browser closes
                request.session.set_expiry(0)
            else:
                # Session lasts for 30 days
                request.session.set_expiry(2592000)
            
            messages.success(request, f'Bienvenue {user.first_name or user.username}!')
            
            # Redirect to next or dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Email ou mot de passe incorrect.')
    
    return render(request, 'login.html')


@csrf_protect
def register_view(request):
    """
    Registration view - creates new user account with style profile
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Basic user information
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        phone = request.POST.get('phone', '').strip()
        
        # Style profile information
        preferred_styles = request.POST.getlist('preferred_styles')
        favorite_colors = request.POST.getlist('favorite_colors')
        body_type = request.POST.get('body_type', '').strip()
        height = request.POST.get('height', '').strip()
        
        # Preferences
        prefers_sustainable = request.POST.get('prefers_sustainable') == 'true'
        prefers_secondhand = request.POST.get('prefers_secondhand') == 'true'
        
        # Validation
        if not email or not username or not password:
            messages.error(request, 'Email, nom d\'utilisateur et mot de passe sont requis.')
            return render(request, 'register.html')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Un compte avec cet email existe déjà.')
            return render(request, 'register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur est déjà pris.')
            return render(request, 'register.html')
        
        # Password validation
        if len(password) < 8:
            messages.error(request, 'Le mot de passe doit contenir au moins 8 caractères.')
            return render(request, 'register.html')
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Update phone if provided
            if phone:
                user.phone = phone
                user.save()
            
            # Create style profile with preferences
            style_profile_data = {
                'user': user,
                'preferred_styles': preferred_styles,
                'favorite_colors': favorite_colors,
                'prefers_sustainable': prefers_sustainable,
                'prefers_secondhand': prefers_secondhand,
            }
            
            # Add optional fields
            if body_type:
                style_profile_data['body_type'] = body_type
            
            if height and height.isdigit():
                height_int = int(height)
                if 100 <= height_int <= 250:
                    style_profile_data['height'] = height_int
            
            StyleProfile.objects.create(**style_profile_data)
            
            # Mark onboarding as completed since we collected all info
            user.onboarding_completed = True
            user.save()
            
            # Auto login after registration
            auth_login(request, user)
            
            messages.success(request, 'Compte créé avec succès! Bienvenue sur Tailora.')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du compte: {str(e)}')
            return render(request, 'register.html')
    
    return render(request, 'register.html')


@login_required
def logout_view(request):
    """
    Logout view - logs out the user
    """
    auth_logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')


@csrf_protect
def password_reset_view(request):
    """
    Password reset request view
    """
    # TODO: Implement password reset functionality
    messages.info(request, 'La fonctionnalité de réinitialisation de mot de passe sera bientôt disponible.')
    return redirect('login')


@login_required
def dashboard_view(request):
    """
    Dashboard view - main page after login
    """
    context = {
        'user': request.user,
    }
    return render(request, 'dashboard.html', context)
