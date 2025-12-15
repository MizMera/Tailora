from social.models import LookbookPost

# Get all posts
posts = list(LookbookPost.objects.all())

if posts:
    # Different like counts to trigger different badges
    badge_counts = [250, 150, 75, 45, 30, 20, 10, 5]
    
    for i, post in enumerate(posts):
        likes = badge_counts[i % len(badge_counts)]
        post.likes_count = likes
        post.save()
        badge = 'Iconic' if likes >= 200 else 'Star' if likes >= 100 else 'Viral' if likes >= 50 else 'None'
        print(f'Post: {post.outfit.name[:30]:30} | Likes: {likes:3} | Badge: {badge}')
    
    print(f'\n✅ Updated {len(posts)} posts with demo likes!')
else:
    print('No posts found')
