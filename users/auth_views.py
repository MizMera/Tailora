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
            messages.error(request, 'Please provide an email and password.')
            return render(request, 'login.html')
        
        # Authenticate using email (since USERNAME_FIELD is 'email')
        user = authenticate(request, username=email, password=password)
        
        print(f"DEBUG: Login attempt with email: {email}")
        print(f"DEBUG: Authentication result: {user}")
        
        if user is None:
            print(f"DEBUG: Authentication failed")
            messages.error(request, 'Incorrect email or password.')
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
            
            messages.success(request, f'Welcome {user.first_name or user.username}!')
            
            # Redirect to next or dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Incorrect email or password.')
    
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
            messages.error(request, 'Email, username, and password are required.')
            return render(request, 'register.html')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'This username is already taken.')
            return render(request, 'register.html')
        
        # Password validation
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
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
                send_verification_email(user=user, request=request)
            except Exception as e:
                print(f"Failed to send verification email: {e}")
            
            # Auto login after registration
            auth_login(request, user)
            
            messages.success(request, 'Account created! Please check your email to verify your account.')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'register.html')
    
    return render(request, 'register.html')


@login_required
def logout_view(request):
    """
    Logout view - logs out the user
    """
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@csrf_protect
def password_reset_request_view(request):
    """
    Password reset request view - sends reset email
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, 'Please provide an email address.')
            return render(request, 'password_reset_request.html')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link (prefer absolute URL from request)
            reset_path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            try:
                reset_link = request.build_absolute_uri(reset_path)
            except Exception:
                reset_link = f"{getattr(settings, 'FRONTEND_URL', '')}{reset_path}"
            
            # Send email
            subject = 'Reset your Tailora password'
            message = f"""
Hello {user.username},

We received a request to reset your Tailora password.

Click the link below to set a new password:
{reset_link}

This link is valid for 1 hour.

If you didn't request this, you can safely ignore this email.

Best regards,
The Tailora Team
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
            
            messages.success(request, 'A password reset email has been sent to your address.')
            return redirect('login')
            
        except User.DoesNotExist:
            # Don't reveal that the user doesn't exist for security
            messages.success(request, 'If an account exists for that email, a reset link has been sent.')
            return redirect('login')
        except Exception as e:
            print(f"Password reset error: {e}")
            messages.error(request, 'An error occurred. Please try again.')
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
                messages.error(request, 'Please fill in all fields.')
                return render(request, 'password_reset_confirm.html', {'validlink': True})
            
            if password1 != password2:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'password_reset_confirm.html', {'validlink': True})
            
            if len(password1) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'password_reset_confirm.html', {'validlink': True})
            
            # Set new password
            user.set_password(password1)
            user.save()
            
            messages.success(request, 'Your password has been reset successfully.')
            return redirect('login')
        
        return render(request, 'password_reset_confirm.html', {'validlink': True})
    else:
        messages.error(request, 'The reset link is invalid or has expired.')
        return render(request, 'password_reset_confirm.html', {'validlink': False})


def send_verification_email(user=None, request=None):
    """
    Send email verification link to user
    """
    if user is None:
        raise ValueError("User parameter is required")
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Create verification link (prefer absolute URL from request)
    verify_path = reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
    if request is not None:
        try:
            verification_link = request.build_absolute_uri(verify_path)
        except Exception:
            verification_link = f"{getattr(settings, 'FRONTEND_URL', '')}{verify_path}"
    else:
        verification_link = f"{getattr(settings, 'FRONTEND_URL', '')}{verify_path}"
    
    # Send email
    subject = 'Verify your email address - Tailora'
    message = f"""
Hello {user.username},

Thanks for signing up for Tailora!

Click the link below to verify your email address:
{verification_link}

Best regards,
The Tailora Team
    """
    
    print(f"[DEBUG] Attempting to send verification email to: {user.email}")
    print(f"[DEBUG] From: {settings.DEFAULT_FROM_EMAIL}")
    print(f"[DEBUG] Email backend: {settings.EMAIL_BACKEND}")
    print(f"[DEBUG] SMTP host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        print(f"[SUCCESS] Verification email sent to {user.email}")
        print(f"[SUCCESS] Verification link: {verification_link}")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


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
        messages.success(request, 'Your email has been verified!')
        return redirect('login')
    else:
        messages.error(request, 'The verification link is invalid or has expired.')
        return redirect('login')


@login_required
def resend_verification_email_view(request):
    """
    Resend verification email
    """
    if request.user.is_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('dashboard')
    
    try:
        send_verification_email(user=request.user, request=request)
        messages.success(request, 'A new verification email has been sent.')
    except Exception as e:
        print(f"Failed to resend verification email: {e}")
        messages.error(request, 'An error occurred. Please try again.')
    
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
        
        messages.success(request, 'Profile updated successfully!')
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
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'change_password.html')
        
        # Check current password
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return render(request, 'change_password.html')
        
        # Validate new passwords
        if new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
            return render(request, 'change_password.html')
        
        if len(new_password1) < 8:
            messages.error(request, 'New password must be at least 8 characters long.')
            return render(request, 'change_password.html')
        
        # Change password
        request.user.set_password(new_password1)
        request.user.save()
        
        # Update session to prevent logout
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Password changed successfully!')
        return redirect('profile_settings')
    
    return render(request, 'change_password.html')


@login_required
def request_account_deletion_view(request):
    """
    Handles the initial request for account deletion by sending a confirmation code.
    """
    if request.method == 'POST':
        user = request.user
        user.generate_deletion_code()

        # Send email with deletion code
        subject = 'Your Account Deletion Code'
        message = f"""
Hello {user.username},

You requested to delete your account. Please use the following 6-digit code to confirm:

{user.deletion_code}

This code will expire in 15 minutes.

If you did not request this, please ignore this email.

Best regards,
The Tailora Team
"""
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            messages.success(request, 'A deletion code has been sent to your email.')
            return redirect('confirm_account_deletion')
        except Exception as e:
            messages.error(request, f'Failed to send deletion email: {e}')
            return redirect('profile_settings')

    return render(request, 'delete_account.html')


@login_required
def confirm_account_deletion_view(request):
    """
    Handles the final confirmation of account deletion with a code.
    """
    user = request.user
    if request.method == 'POST':
        code = request.POST.get('deletion_code')
        if not code:
            messages.error(request, 'Please enter the deletion code.')
            return render(request, 'delete_account_confirm.html')

        if user.deletion_code == code:
            from django.utils import timezone
            if user.deletion_code_expires_at > timezone.now():
                # Correct code and not expired, delete account
                user_email = user.email  # Save for message
                auth_logout(request)
                user.delete()
                messages.success(request, f'Account for {user_email} has been successfully deleted.')
                return redirect('login')
            else:
                messages.error(request, 'The deletion code has expired. Please request a new one.')
        else:
            messages.error(request, 'The deletion code is incorrect.')

    return render(request, 'delete_account_confirm.html')


@login_required
def upgrade_account_view(request):
    """
    Handles the user request to upgrade their account to Premium.
    """
    user = request.user
    from django.utils import timezone

    if user.role == 'premium':
        messages.info(request, 'You are already a full Premium member.')
        return redirect('profile_settings')
    
    if user.premium_until and user.premium_until > timezone.now():
        messages.info(request, f'You are currently on a Premium trial until {user.premium_until.strftime("%Y-%m-%d")}.')
        return redirect('profile_settings')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'trial':
            user.premium_until = timezone.now() + timezone.timedelta(days=7)
            user.save()
            messages.success(request, 'Congratulations! You have started a 7-day Premium trial.')
            return redirect('profile_settings')

        elif action == 'upgrade':
            card_number = request.POST.get('card_number')
            expiry_date = request.POST.get('expiry_date')
            cvc = request.POST.get('cvc')

            if card_number and expiry_date and cvc:
                # Simulate successful payment
                user.role = 'premium'
                user.premium_until = None  # Clear trial date if it exists
                user.save()
                messages.success(request, 'Congratulations! Your account has been upgraded to Premium.')
                return redirect('profile_settings')
            else:
                messages.error(request, 'Please fill in all payment details.')

    return render(request, 'upgrade_account.html')


@login_required
def cancel_subscription_view(request):
    """
    Handles the user request to cancel their Premium subscription.
    """
    if request.method == 'POST':
        user = request.user
        user.role = 'user'
        user.premium_until = None
        user.save()
        messages.success(request, 'Your Premium subscription has been canceled.')
        return redirect('profile_settings')
    
    # Redirect if accessed via GET
    return redirect('profile_settings')
