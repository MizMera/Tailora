from django.db import models
from users.models import User
from outfits.models import Outfit
import uuid


class UserFollow(models.Model):
    """
    Follow relationship between users
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_follows'
        unique_together = [['follower', 'following']]
        verbose_name = 'Abonnement'
        verbose_name_plural = 'Abonnements'
    
    def __str__(self):
        return f"{self.follower.email} follows {self.following.email}"


class LookbookPost(models.Model):
    """
    Module 5: Social Hub - Public outfit posts
    Users share their outfits with the community
    """
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('followers', 'Abonnés Seulement'),
        ('private', 'Privé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lookbook_posts')
    outfit = models.ForeignKey(Outfit, on_delete=models.CASCADE, related_name='lookbook_posts')
    
    # Post content
    caption = models.TextField(blank=True)
    hashtags = models.JSONField(default=list, blank=True)  # e.g., ["#mariage", "#lookdujour"]
    
    # Visibility
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    
    # Engagement metrics
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    saves_count = models.IntegerField(default=0)
    
    # Optional: Link to style challenge
    challenge = models.ForeignKey('StyleChallenge', on_delete=models.SET_NULL, null=True, blank=True, related_name='submissions')
    
    # NOUVEAU: Stocker les chemins des images améliorées pour ce post
    enhanced_images = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lookbook_posts'
        ordering = ['-created_at']
        verbose_name = 'Publication Lookbook'
        verbose_name_plural = 'Publications Lookbook'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['visibility', '-created_at']),
        ]
    
    def __str__(self):
        return f"Post by {self.user.email} - {self.outfit.name}"


class PostLike(models.Model):
    """
    Likes on lookbook posts
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    post = models.ForeignKey(LookbookPost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'post_likes'
        unique_together = [['user', 'post']]
        verbose_name = 'J\'aime'
        verbose_name_plural = 'J\'aimes'
    
    def __str__(self):
        return f"{self.user.email} likes post {self.post.id}"


class PostComment(models.Model):
    """
    Comments on lookbook posts
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments')
    post = models.ForeignKey(LookbookPost, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    
    # Reply functionality
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'post_comments'
        ordering = ['created_at']
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'
    
    def __str__(self):
        return f"Comment by {self.user.email} on post {self.post.id}"


class PostSave(models.Model):
    """
    Saved posts for inspiration
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_posts')
    post = models.ForeignKey(LookbookPost, on_delete=models.CASCADE, related_name='saves')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'post_saves'
        unique_together = [['user', 'post']]
        verbose_name = 'Publication Sauvegardée'
        verbose_name_plural = 'Publications Sauvegardées'
    
    def __str__(self):
        return f"{self.user.email} saved post {self.post.id}"


class StyleChallenge(models.Model):
    """
    Weekly style challenges for community engagement
    """
    STATUS_CHOICES = [
        ('upcoming', 'À Venir'),
        ('active', 'En Cours'),
        ('completed', 'Terminé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    theme = models.CharField(max_length=100)  # e.g., "Look monochrome", "Vintage"
    
    # Challenge period
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    
    # Challenge rules/guidelines
    rules = models.JSONField(default=list, blank=True)
    hashtag = models.CharField(max_length=50, unique=True)
    
    # Banner image
    banner_image = models.ImageField(upload_to='challenges/', blank=True, null=True)
    
    # Participation metrics
    participants_count = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'style_challenges'
        ordering = ['-start_date']
        verbose_name = 'Défi de Style'
        verbose_name_plural = 'Défis de Style'
    
    def __str__(self):
        return f"{self.title} - {self.theme}"
