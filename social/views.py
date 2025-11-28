from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Exists, OuterRef
from django.http import JsonResponse
from .models import LookbookPost, PostLike, PostComment, PostSave, UserFollow, StyleChallenge
from outfits.models import Outfit
from rest_framework import viewsets, permissions, decorators, response
from .serializers import LookbookPostSerializer, PostCommentSerializer, UserFollowSerializer, StyleChallengeSerializer
from .feed_algorithm import FeedAlgorithm, HashtagSystem
import re 
from .ai_photo_enhancer import AIPhotoEnhancer
import os
from django.core.files.storage import default_storage
import json
from django.core.files import File

# [file name]: views.py - AJOUTER CES FONCTIONS À LA FIN

@login_required
def trending_hashtags(request):
    """API pour les hashtags tendances"""
    trending = HashtagSystem.get_trending_hashtags()
    return JsonResponse({'trending': trending})

@login_required 
def hashtag_search(request, hashtag):
    """Recherche par hashtag"""
    posts = LookbookPost.objects.filter(
        hashtags__contains=[hashtag], 
        visibility='public'
    ).select_related('user', 'outfit').annotate(
        is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=request.user))
    ).order_by('-created_at')
    
    return render(request, 'social/hashtag_search.html', {
        'posts': posts, 
        'hashtag': hashtag,
        'trending_hashtags': HashtagSystem.get_trending_hashtags()
    })

# MODIFIER la fonction feed_view existante (remplacer le début)
# [file name]: views.py - MODIFIER feed_view
@login_required
def feed_view(request):
    """Retour à l'algorithme qui fonctionne"""
    # Get users the current user follows
    following_ids = UserFollow.objects.filter(
        follower=request.user
    ).values_list('following_id', flat=True)
    
    # Get posts from followed users + own posts
    posts = LookbookPost.objects.filter(
        Q(user_id__in=following_ids) | Q(user=request.user),
        visibility__in=['public', 'followers']
    ).select_related('user', 'outfit').prefetch_related('likes', 'comments').annotate(
        is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=request.user)),
        is_saved=Exists(PostSave.objects.filter(post=OuterRef('pk'), user=request.user))
    ).order_by('-created_at')[:20]
    
    # Get active challenges
    active_challenges = StyleChallenge.objects.filter(status='active')[:3]
    
    # User stats
    followers_count = UserFollow.objects.filter(following=request.user).count()
    following_count = UserFollow.objects.filter(follower=request.user).count()
    posts_count = LookbookPost.objects.filter(user=request.user).count()
    
    context = {
        'posts': posts,
        'active_challenges': active_challenges,
        'followers_count': followers_count,
        'following_count': following_count,
        'posts_count': posts_count,
        'trending_hashtags': HashtagSystem.get_trending_hashtags()[:5]
    }
    
    return render(request, 'social/feed.html', context)
@login_required
def discover_view(request):
    """Discover page showing trending and popular posts"""
    # Get all public posts
    posts = LookbookPost.objects.filter(
        visibility='public'
    ).select_related('user', 'outfit').prefetch_related('likes').annotate(
        is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=request.user)),
        is_saved=Exists(PostSave.objects.filter(post=OuterRef('pk'), user=request.user))
    ).order_by('-likes_count', '-created_at')[:30]
    
    context = {
        'posts': posts,
        'is_discover': True,
    }
    
    return render(request, 'social/discover.html', context)


@login_required
def create_post(request):
    """Create a new lookbook post - VERSION DEBUG"""
    if request.method == 'POST':
        outfit_id = request.POST.get('outfit')
        caption = request.POST.get('caption', '')
        visibility = request.POST.get('visibility', 'public')
        hashtags = request.POST.get('hashtags', '').split()
        enhance_photos = request.POST.get('enhance_photos') == 'true'
        photo_style = request.POST.get('photo_style', 'auto')
        
        print("=" * 50)
        print("🚀 DÉBUT CREATE_POST - DEBUG AI")
        print(f"📝 Paramètres: AI={enhance_photos}, Style={photo_style}")
        
        if not outfit_id:
            messages.error(request, 'Please select an outfit.')
            return redirect('social:create_post')
        
        outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
        print(f"👕 Outfit: {outfit.name} ({outfit.items.count()} items)")
        
        enhanced_images = {}
        
        if enhance_photos:
            print("🎨 DÉMARRAGE AI...")
            ai_enhancer = AIPhotoEnhancer()
            
            for i, item in enumerate(outfit.items.all()):
                print(f"\n--- Item {i+1}: {item.name} ---")
                
                if not item.image:
                    print("⏭️  Pas d'image - ignoré")
                    continue
                
                print(f"📁 Image path: {item.image.name}")
                print(f"📁 Image URL: {item.image.url}")
                
                # Vérifier existence fichier
                if not default_storage.exists(item.image.name):
                    print("❌ FICHIER INTROUVABLE dans storage!")
                    continue
                
                print("✅ Fichier trouvé dans storage")
                
                try:
                    # Étape 1: Ouvrir l'image
                    original_img = ai_enhancer.processor.open_image(item.image.name)
                    if not original_img:
                        print("❌ Échec ouverture image")
                        continue
                    
                    print(f"✅ Image ouverte: {original_img.size}")
                    
                    # Étape 2: Appliquer l'AI
                    print("🔄 Application de l'AI...")
                    enhanced_img = ai_enhancer.enhance_fashion_photo(item.image.name, photo_style)
                    
                    if not enhanced_img:
                        print("❌ AI a retourné None")
                        continue
                    
                    print(f"✅ AI réussie - Image améliorée: {enhanced_img.size}")
                    
                    # Étape 3: Sauvegarder
                    print("💾 Sauvegarde...")
                    saved_path = ai_enhancer.processor.save_image(enhanced_img, 'enhanced_posts')
                    
                    if saved_path:
                        enhanced_images[str(item.id)] = saved_path
                        print(f"✅ SAUVEGARDE RÉUSSIE: {saved_path}")
                    else:
                        print("❌ Échec sauvegarde")
                        
                except Exception as e:
                    print(f"💥 ERREUR: {e}")
                    import traceback
                    traceback.print_exc()
        
        print(f"\n📊 RÉSULTAT FINAL: {len(enhanced_images)} images améliorées")
        print(f"📦 enhanced_images: {enhanced_images}")
        
        # Créer le post
        post = LookbookPost.objects.create(
            user=request.user,
            outfit=outfit,
            caption=caption,
            visibility=visibility,
            hashtags=hashtags,
            enhanced_images=enhanced_images
        )
        
        print(f"💾 POST CRÉÉ: ID {post.id}")
        print(f"🔍 enhanced_images dans BD: {post.enhanced_images}")
        print("=" * 50)
        
        # Message utilisateur
        if enhance_photos:
            if enhanced_images:
                messages.success(request, f'Post créé avec AI! 🎨 ({len(enhanced_images)} images améliorées)')
            else:
                messages.warning(request, 'Post créé mais AI non appliquée (voir logs)')
        else:
            messages.success(request, 'Post created successfully!')
        
        return redirect('social:post_detail', post_id=post.id)
    
    # GET
    outfits = Outfit.objects.filter(user=request.user)
    return render(request, 'social/create_post.html', {'outfits': outfits})
@login_required
def post_detail(request, post_id):
    """View a single post with comments"""
    post = get_object_or_404(
        LookbookPost.objects.select_related('user', 'outfit').annotate(
            is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=request.user)),
            is_saved=Exists(PostSave.objects.filter(post=OuterRef('pk'), user=request.user))
        ),
        id=post_id
    )
    
    # Check visibility permissions
    if post.visibility == 'private' and post.user != request.user:
        messages.error(request, 'This post is private.')
        return redirect('social:feed')
    
    if post.visibility == 'followers':
        is_following = UserFollow.objects.filter(
            follower=request.user,
            following=post.user
        ).exists()
        if not is_following and post.user != request.user:
            messages.error(request, 'This post is only visible to followers.')
            return redirect('social:feed')
    
    # Get comments
    comments = post.comments.select_related('user').filter(parent_comment__isnull=True).order_by('-created_at')
    
    context = {
        'post': post,
        'comments': comments,
        'is_own_post': post.user == request.user,
    }
    
    return render(request, 'social/post_detail.html', context)
# [file name]: views.py - MODIFIER la fonction edit_post
@login_required
def edit_post(request, post_id):
    """Edit an existing post"""
    post = get_object_or_404(LookbookPost, id=post_id, user=request.user)
    
    if request.method == 'POST':
        caption = request.POST.get('caption', '')
        visibility = request.POST.get('visibility', 'public')
        hashtags_input = request.POST.get('hashtags', '')  # ⚠️ NOUVEAU : Récupérer les hashtags manuels
        
        # OPTION 1: Extraire les hashtags de l'input manuel
        hashtags = [tag.strip() for tag in hashtags_input.split() if tag.strip().startswith('#')]
        
        # OPTION 2: Extraire aussi de la caption (les deux)
        caption_hashtags = re.findall(r'#\w+', caption)
        all_hashtags = list(set(hashtags + caption_hashtags))  # Fusionner sans doublons
        
        post.caption = caption
        post.visibility = visibility
        post.hashtags = all_hashtags  # ⚠️ Utiliser les hashtags combinés
        post.save()
        
        messages.success(request, 'Post updated successfully!')
        return redirect('social:post_detail', post_id=post.id)
    
    # GET: Show edit form
    context = {
        'post': post,
    }
    
    return render(request, 'social/edit_post.html', context)

@login_required
def delete_post(request, post_id):
    """Delete a post"""
    post = get_object_or_404(LookbookPost, id=post_id, user=request.user)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('social:feed')
    
    return redirect('social:post_detail', post_id=post_id)


@login_required
def toggle_like(request, post_id):
    """Like or unlike a post"""
    post = get_object_or_404(LookbookPost, id=post_id)
    
    like, created = PostLike.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        like.delete()
        post.likes_count = max(0, post.likes_count - 1)
        liked = False
    else:
        post.likes_count += 1
        liked = True
    
    post.save(update_fields=['likes_count'])
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'likes_count': post.likes_count})
    
    return redirect('social:post_detail', post_id=post_id)


@login_required
def toggle_save(request, post_id):
    """Save or unsave a post"""
    post = get_object_or_404(LookbookPost, id=post_id)
    
    save, created = PostSave.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        save.delete()
        post.saves_count = max(0, post.saves_count - 1)
        saved = False
    else:
        post.saves_count += 1
        saved = True
    
    post.save(update_fields=['saves_count'])
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'saved': saved, 'saves_count': post.saves_count})
    
    return redirect('social:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    """Add a comment to a post"""
    post = get_object_or_404(LookbookPost, id=post_id)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id')
        
        if content:
            comment = PostComment.objects.create(
                user=request.user,
                post=post,
                content=content,
                parent_comment_id=parent_id if parent_id else None
            )
            post.comments_count += 1
            post.save(update_fields=['comments_count'])
            
            messages.success(request, 'Comment added!')
    
    return redirect('social:post_detail', post_id=post_id)


@login_required
def delete_comment(request, comment_id):
    """Delete a comment"""
    comment = get_object_or_404(PostComment, id=comment_id, user=request.user)
    post = comment.post
    
    if request.method == 'POST':
        comment.delete()
        post.comments_count = max(0, post.comments_count - 1)
        post.save(update_fields=['comments_count'])
        messages.success(request, 'Comment deleted!')
    
    return redirect('social:post_detail', post_id=post.id)


@login_required
def profile_view(request, user_id):
    """View a user's profile and posts"""
    from users.models import User
    profile_user = get_object_or_404(User, id=user_id)
    
    # Check if current user follows this profile
    is_following = UserFollow.objects.filter(
        follower=request.user,
        following=profile_user
    ).exists() if request.user != profile_user else False
    
    # Get user's posts
    if profile_user == request.user:
        posts = LookbookPost.objects.filter(user=profile_user)
    else:
        # Show only public posts or followers-only if following
        visibility_filter = Q(visibility='public')
        if is_following:
            visibility_filter |= Q(visibility='followers')
        posts = LookbookPost.objects.filter(user=profile_user).filter(visibility_filter)
    
    posts = posts.select_related('outfit').annotate(
        is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=request.user))
    ).order_by('-created_at')
    
    # Stats
    followers_count = UserFollow.objects.filter(following=profile_user).count()
    following_count = UserFollow.objects.filter(follower=profile_user).count()
    posts_count = posts.count()
    
    context = {
        'profile_user': profile_user,
        'posts': posts,
        'is_following': is_following,
        'is_own_profile': profile_user == request.user,
        'followers_count': followers_count,
        'following_count': following_count,
        'posts_count': posts_count,
    }
    
    return render(request, 'social/profile.html', context)


@login_required
def toggle_follow(request, user_id):
    """Follow or unfollow a user"""
    from users.models import User
    user_to_follow = get_object_or_404(User, id=user_id)
    
    if user_to_follow == request.user:
        messages.error(request, 'You cannot follow yourself.')
        return redirect('social:feed')
    
    follow, created = UserFollow.objects.get_or_create(
        follower=request.user,
        following=user_to_follow
    )
    
    if not created:
        follow.delete()
        messages.success(request, f'Unfollowed {user_to_follow.get_full_name()}.')
    else:
        messages.success(request, f'Now following {user_to_follow.get_full_name()}!')
    
    return redirect('social:profile', user_id=user_id)


@login_required
def followers_list(request, user_id):
    """List of user's followers"""
    from users.models import User
    user = get_object_or_404(User, id=user_id)
    
    followers = UserFollow.objects.filter(following=user).select_related('follower')
    
    context = {
        'user': user,
        'followers': followers,
    }
    
    return render(request, 'social/followers_list.html', context)


@login_required
def following_list(request, user_id):
    """List of users that this user follows"""
    from users.models import User
    user = get_object_or_404(User, id=user_id)
    
    following = UserFollow.objects.filter(follower=user).select_related('following')
    
    context = {
        'user': user,
        'following': following,
    }
    
    return render(request, 'social/following_list.html', context)


@login_required
def saved_posts(request):
    """View saved posts"""
    saves = PostSave.objects.filter(user=request.user).select_related(
        'post', 'post__user', 'post__outfit'
    ).order_by('-created_at')
    
    posts = [save.post for save in saves]
    
    context = {
        'posts': posts,
        'is_saved_view': True,
    }
    
    return render(request, 'social/saved_posts.html', context)


@login_required
def challenges_list(request):
    """List all style challenges"""
    challenges = StyleChallenge.objects.all().order_by('status', '-start_date')
    
    context = {
        'challenges': challenges,
    }
    
    return render(request, 'social/challenges_list.html', context)


@login_required
def challenge_detail(request, challenge_id):
    """View a style challenge and its submissions"""
    challenge = get_object_or_404(StyleChallenge, id=challenge_id)
    
    # Get challenge submissions
    submissions = LookbookPost.objects.filter(
        challenge=challenge,
        visibility='public'
    ).select_related('user', 'outfit').annotate(
        is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=request.user))
    ).order_by('-likes_count', '-created_at')
    
    context = {
        'challenge': challenge,
        'submissions': submissions,
    }
    
    return render(request, 'social/challenge_detail.html', context)



class LookbookPostViewSet(viewsets.ModelViewSet):
    queryset = LookbookPost.objects.all().select_related('user', 'outfit')
    serializer_class = LookbookPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    @decorators.action(detail=True, methods=['POST'])
    def like(self, request, pk=None):
        post = self.get_object()
        like, created = PostLike.objects.get_or_create(user=request.user, post=post)
        if not created:
            like.delete()
        return response.Response({'liked': created})

    @decorators.action(detail=True, methods=['POST'])
    def save(self, request, pk=None):
        post = self.get_object()
        save, created = PostSave.objects.get_or_create(user=request.user, post=post)
        if not created:
            save.delete()
        return response.Response({'saved': created})

class PostCommentViewSet(viewsets.ModelViewSet):
    queryset = PostComment.objects.all().select_related('user', 'post')
    serializer_class = PostCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserFollowViewSet(viewsets.ModelViewSet):
    queryset = UserFollow.objects.all()
    serializer_class = UserFollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    @decorators.action(detail=True, methods=['POST'])
    def toggle_follow(self, request, pk=None):
        follow_instance = self.get_object()
        if follow_instance.follower == request.user:
            return response.Response({'error': "Cannot follow yourself."})
        exists = UserFollow.objects.filter(follower=request.user, following=follow_instance.following).exists()
        if exists:
            UserFollow.objects.filter(follower=request.user, following=follow_instance.following).delete()
            followed = False
        else:
            UserFollow.objects.create(follower=request.user, following=follow_instance.following)
            followed = True
        return response.Response({'followed': followed})
class StyleChallengeViewSet(viewsets.ModelViewSet):
    queryset = StyleChallenge.objects.all()
    serializer_class = StyleChallengeSerializer
    permission_classes = [permissions.IsAuthenticated]

@login_required
def ai_photo_preview(request, outfit_id):
    """Prévisualisation AI - Version simplifiée"""
    from outfits.models import Outfit
    outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            photo_style = data.get('style', 'auto')
            
            print(f"🔍 AI Preview demandé - Outfit: {outfit.name}, Style: {photo_style}")
            
            ai_enhancer = AIPhotoEnhancer()
            preview_results = []
            items_with_images = [item for item in outfit.items.all() if item.image]
            print(f"📸 Items avec images: {len(items_with_images)}")
            for item in outfit.items.all()[:8]:  # Limiter à 2 items
                if item.image:
                    print(f"📸 Traitement de: {item.name}")
                    
                    try:
                        enhanced = ai_enhancer.enhance_fashion_photo(item.image.name, photo_style)
                        if enhanced:
                            enhanced_path = ai_enhancer.processor.save_image(enhanced, 'previews')
                            preview_results.append({
                                'item': {'name': item.name, 'id': str(item.id)},
                                'original': item.image.url,
                                'enhanced': default_storage.url(enhanced_path),
                                'style': photo_style
                            })
                            print(f"✅ Succès: {item.name}")
                        else:
                            print(f"❌ Échec amélioration: {item.name}")
                    except Exception as e:
                        print(f"❌ Erreur traitement {item.name}: {e}")
            
            print(f"📊 Résultat: {len(preview_results)} images améliorées")
            return JsonResponse({'previews': preview_results})
            
        except Exception as e:
            print(f"❌ Erreur générale AI Preview: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
@login_required
def debug_ai(request):
    """Page de debug pour l'AI"""
    outfit = Outfit.objects.filter(user=request.user).first()
    debug_info = {}
    
    if outfit:
        debug_info['outfit'] = {
            'name': outfit.name,
            'item_count': outfit.items.count(),
            'items': []
        }
        
        ai_enhancer = AIPhotoEnhancer()
        
        for item in outfit.items.all()[:2]:  # Test avec 2 items max
            item_info = {
                'name': item.name,
                'has_image': bool(item.image),
                'image_path': item.image.name if item.image else None,
                'image_exists': False,
                'ai_works': False,
                'error': None
            }
            
            if item.image:
                # Vérifier si l'image existe dans le storage
                item_info['image_exists'] = default_storage.exists(item.image.name)
                
                if item_info['image_exists']:
                    try:
                        # Tester l'AI
                        enhanced = ai_enhancer.enhance_fashion_photo(item.image.name, 'vibrant')
                        item_info['ai_works'] = bool(enhanced)
                        if enhanced:
                            # Tester la sauvegarde
                            saved_path = ai_enhancer.processor.save_image(enhanced, 'debug_ai')
                            item_info['saved_path'] = saved_path
                    except Exception as e:
                        item_info['error'] = str(e)
            
            debug_info['outfit']['items'].append(item_info)
    
    return JsonResponse(debug_info)