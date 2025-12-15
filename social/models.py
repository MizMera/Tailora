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
    
    # AI Enhanced Images
    # Dictionary mapping outfit item IDs to enhanced image paths: { "item_id": "path/to/image.jpg" }
    enhanced_images = models.JSONField(default=dict, blank=True)
    # Enhancement style used: auto, vibrant, elegant, vintage, bright
    enhancement_style = models.CharField(max_length=20, blank=True, default='')
    
    # Visibility
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    
    # Engagement metrics
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    saves_count = models.IntegerField(default=0)
    
    # Optional: Link to style challenge
    challenge = models.ForeignKey('StyleChallenge', on_delete=models.SET_NULL, null=True, blank=True, related_name='submissions')
    
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


class PostDraft(models.Model):
    """
    Draft posts for later publication
    """
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('scheduled', 'Programmé'),
        ('published', 'Publié'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_drafts')
    outfit = models.ForeignKey(Outfit, on_delete=models.CASCADE, related_name='post_drafts')
    
    # Draft content
    caption = models.TextField(blank=True)
    hashtags = models.JSONField(default=list, blank=True)
    enhanced_images = models.JSONField(default=dict, blank=True)
    visibility = models.CharField(max_length=20, choices=LookbookPost.VISIBILITY_CHOICES, default='public')
    
    # AI optimization
    ai_optimized_hashtags = models.JSONField(default=list, blank=True)
    ai_suggested_captions = models.JSONField(default=list, blank=True)
    ai_best_time = models.DateTimeField(null=True, blank=True)
    ai_confidence_score = models.FloatField(default=0.0)
    
    # Scheduling
    scheduled_for = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'post_drafts'
        ordering = ['-created_at']
        verbose_name = 'Brouillon de Publication'
        verbose_name_plural = 'Brouillons de Publication'
    
    def __str__(self):
        return f"Draft by {self.user.email} - {self.status}"
    
    def publish(self):
        """Convert draft to published post"""
        post = LookbookPost.objects.create(
            user=self.user,
            outfit=self.outfit,
            caption=self.caption,
            hashtags=self.hashtags,
            enhanced_images=self.enhanced_images,
            visibility=self.visibility
        )
        
        self.status = 'published'
        self.save()
        return post


class Badge(models.Model):
    """
    Achievement badges for users
    """
    BADGE_TYPES = (
        ('starter', 'Starter'),
        ('popular', 'Popular'), 
        ('influencer', 'Influencer'),
        ('trendsetter', 'Trendsetter'),
        ('champion', 'Champion'),
        ('social', 'Social'),
        ('creator', 'Creator'),
    )
    
    name = models.CharField(max_length=100)
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    description = models.TextField()
    icon = models.CharField(max_length=50)  # Emoji
    color = models.CharField(max_length=7, default='#FFD700')  # Hex color code
    criteria = models.JSONField(default=dict)  # Conditions to earn the badge
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'badges'
        verbose_name = 'Badge'
        verbose_name_plural = 'Badges'

    def __str__(self):
        return f"{self.icon} {self.name}"


class UserBadge(models.Model):
    """
    Badges earned by users
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_badges'
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']
        verbose_name = 'Badge Utilisateur'
        verbose_name_plural = 'Badges Utilisateur'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.badge.name}"


class AIEngagementData(models.Model):
    """
    Store AI-generated engagement insights for posts
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(LookbookPost, on_delete=models.CASCADE, related_name='ai_insights', null=True, blank=True)
    draft = models.ForeignKey(PostDraft, on_delete=models.CASCADE, related_name='ai_insights', null=True, blank=True)
    
    # Optimization data
    optimal_post_time = models.DateTimeField()
    hashtag_suggestions = models.JSONField(default=list)
    caption_suggestions = models.JSONField(default=list)
    
    # Performance predictions
    predicted_likes = models.IntegerField(default=0)
    predicted_comments = models.IntegerField(default=0)
    predicted_saves = models.IntegerField(default=0)
    confidence_score = models.FloatField(default=0.0)
    
    # User engagement patterns
    user_best_time_window = models.CharField(max_length=50, blank=True)  # e.g., "weekday_18_21"
    best_performing_hashtags = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_engagement_data'
        verbose_name = 'Données d\'Engagement IA'
        verbose_name_plural = 'Données d\'Engagement IA'
