from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from users.models import User, StyleProfile


@csrf_protect
def login_view(request):
    """
    Login view - handles user authentication
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        print(f"DEBUG: Login attempt with email: {email}")
        
        if not email or not password:
            messages.error(request, 'Veuillez fournir un email et un mot de passe.')
            return render(request, 'login.html')
        
        # Authenticate using email (since USERNAME_FIELD is 'email')
        user = authenticate(request, username=email, password=password)
        
        print(f"DEBUG: Login attempt with email: {email}")
        print(f"DEBUG: Authentication result: {user}")
        
        if user is None:
            print(f"DEBUG: Authentication failed")
            messages.error(request, 'Email ou mot de passe incorrect.')
            return render(request, 'login.html')
        
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
            
            # Send verification email
            try:
                send_verification_email(user)
            except Exception as e:
                print(f"Failed to send verification email: {e}")
            
            # Auto login after registration
            auth_login(request, user)
            
            messages.success(request, 'Compte créé avec succès! Veuillez vérifier votre email pour activer votre compte.')
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
def password_reset_request_view(request):
    """
    Password reset request view - sends reset email
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, 'Veuillez fournir une adresse email.')
            return render(request, 'password_reset_request.html')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link
            reset_link = f"{settings.FRONTEND_URL}{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"
            
            # Send email
            subject = 'Réinitialisation de votre mot de passe Tailora'
            message = f"""
Bonjour {user.username},

Vous avez demandé à réinitialiser votre mot de passe sur Tailora.

Cliquez sur le lien ci-dessous pour créer un nouveau mot de passe :
{reset_link}

Ce lien est valide pendant 1 heure.

Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.

Cordialement,
L'équipe Tailora
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                print(f"Password reset email sent to {user.email}")
                print(f"Reset link: {reset_link}")
            except Exception as email_error:
                print(f"Failed to send password reset email: {email_error}")
            
            messages.success(request, 'Un email de réinitialisation a été envoyé à votre adresse.')
            return redirect('login')
            
        except User.DoesNotExist:
            # Don't reveal that the user doesn't exist for security
            messages.success(request, 'Si un compte existe avec cet email, un lien de réinitialisation a été envoyé.')
            return redirect('login')
        except Exception as e:
            print(f"Password reset error: {e}")
            messages.error(request, 'Une erreur est survenue. Veuillez réessayer.')
            return render(request, 'password_reset_request.html')
    
    return render(request, 'password_reset_request.html')


@csrf_protect
def password_reset_confirm_view(request, uidb64, token):
    """
    Password reset confirmation view - actually resets the password
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            if not password1 or not password2:
                messages.error(request, 'Veuillez remplir tous les champs.')
                return render(request, 'password_reset_confirm.html', {'validlink': True})
            
            if password1 != password2:
                messages.error(request, 'Les mots de passe ne correspondent pas.')
                return render(request, 'password_reset_confirm.html', {'validlink': True})
            
            if len(password1) < 8:
                messages.error(request, 'Le mot de passe doit contenir au moins 8 caractères.')
                return render(request, 'password_reset_confirm.html', {'validlink': True})
            
            # Set new password
            user.set_password(password1)
            user.save()
            
            messages.success(request, 'Votre mot de passe a été réinitialisé avec succès.')
            return redirect('login')
        
        return render(request, 'password_reset_confirm.html', {'validlink': True})
    else:
        messages.error(request, 'Le lien de réinitialisation est invalide ou a expiré.')
        return render(request, 'password_reset_confirm.html', {'validlink': False})


@csrf_protect
def send_verification_email(user):
    """
    Send email verification link to user
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Create verification link
    verification_link = f"{settings.FRONTEND_URL}{reverse('verify_email', kwargs={'uidb64': uid, 'token': token})}"
    
    # Send email
    subject = 'Vérifiez votre adresse email - Tailora'
    message = f"""
Bonjour {user.username},

Merci de vous être inscrit sur Tailora !

Cliquez sur le lien ci-dessous pour vérifier votre adresse email :
{verification_link}

Cordialement,
L'équipe Tailora
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    print(f"Verification email sent to {user.email}")
    print(f"Verification link: {verification_link}")


def verify_email_view(request, uidb64, token):
    """
    Email verification view
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_verified = True
        user.save()
        messages.success(request, 'Votre email a été vérifié avec succès!')
        return redirect('login')
    else:
        messages.error(request, 'Le lien de vérification est invalide ou a expiré.')
        return redirect('login')


@login_required
def resend_verification_email_view(request):
    """
    Resend verification email
    """
    if request.user.is_verified:
        messages.info(request, 'Votre email est déjà vérifié.')
        return redirect('dashboard')
    
    try:
        send_verification_email(request.user)
        messages.success(request, 'Un nouvel email de vérification a été envoyé.')
    except Exception as e:
        messages.error(request, 'Une erreur est survenue. Veuillez réessayer.')
    
    return redirect('dashboard')


@login_required
def dashboard_view(request):
    """
    Dashboard view - main page after login
    """
    # Get or create style profile
    try:
        style_profile = request.user.style_profile
    except StyleProfile.DoesNotExist:
        style_profile = StyleProfile.objects.create(user=request.user)
    
    context = {
        'user': request.user,
        'style_profile': style_profile,
    }
    return render(request, 'dashboard.html', context)


@login_required
def profile_settings_view(request):
    """
    User profile settings view
    """
    user = request.user
    
    try:
        style_profile = user.style_profile
    except StyleProfile.DoesNotExist:
        style_profile = StyleProfile.objects.create(user=user)
    
    if request.method == 'POST':
        # Update user basic info
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.phone = request.POST.get('phone', '')
        
        # Handle profile image upload
        if request.FILES.get('profile_image'):
            user.profile_image = request.FILES['profile_image']
        
        user.save()
        
        # Update style profile
        style_profile.preferred_styles = request.POST.getlist('preferred_styles')
        style_profile.favorite_colors = request.POST.getlist('favorite_colors')
        style_profile.body_type = request.POST.get('body_type', '')
        
        height = request.POST.get('height', '').strip()
        if height and height.isdigit():
            height_int = int(height)
            if 100 <= height_int <= 250:
                style_profile.height = height_int
        
        style_profile.prefers_sustainable = request.POST.get('prefers_sustainable') == 'true'
        style_profile.prefers_secondhand = request.POST.get('prefers_secondhand') == 'true'
        
        style_profile.save()
        
        messages.success(request, 'Profil mis à jour avec succès!')
        return redirect('profile_settings')
    
    context = {
        'user': user,
        'style_profile': style_profile,
    }
    return render(request, 'profile_settings.html', context)


@login_required
def change_password_view(request):
    """
    Change password view for logged-in users
    """
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if not all([current_password, new_password1, new_password2]):
            messages.error(request, 'Veuillez remplir tous les champs.')
            return render(request, 'change_password.html')
        
        # Check current password
        if not request.user.check_password(current_password):
            messages.error(request, 'Le mot de passe actuel est incorrect.')
            return render(request, 'change_password.html')
        
        # Validate new passwords
        if new_password1 != new_password2:
            messages.error(request, 'Les nouveaux mots de passe ne correspondent pas.')
            return render(request, 'change_password.html')
        
        if len(new_password1) < 8:
            messages.error(request, 'Le nouveau mot de passe doit contenir au moins 8 caractères.')
            return render(request, 'change_password.html')
        
        # Change password
        request.user.set_password(new_password1)
        request.user.save()
        
        # Update session to prevent logout
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Mot de passe modifié avec succès!')
        return redirect('profile_settings')
    
    return render(request, 'change_password.html')


@login_required
def delete_account_view(request):
    """
    Delete user account view
    """
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm = request.POST.get('confirm')
        
        if confirm != 'DELETE':
            messages.error(request, 'Veuillez taper "DELETE" pour confirmer.')
            return render(request, 'delete_account.html')
        
        if not request.user.check_password(password):
            messages.error(request, 'Mot de passe incorrect.')
            return render(request, 'delete_account.html')
        
        # Delete user account
        user = request.user
        auth_logout(request)
        user.delete()
        
        messages.success(request, 'Votre compte a été supprimé.')
        return redirect('login')
    
    return render(request, 'delete_account.html')
