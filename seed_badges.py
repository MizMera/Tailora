from social.models import LookbookPost

def seed_badges():
    # Get 4 most recent posts
    posts = list(LookbookPost.objects.all().order_by('-created_at')[:4])
    
    if not posts:
        print("No posts found! Please create some posts first.")
        return

    configs = [
        (205, "Iconic (Diamond)"),      # > 200
        (105, "Star (Gold/Silver)"),    # > 100
        (55, "Viral (Fire)"),           # > 50
        (26, "Appreciated (Heart)")     # > 25
    ]

    print("Seeding likes for badges verification:")
    print("-" * 50)

    for i, post in enumerate(posts):
        if i >= len(configs):
            break
            
        likes, badge_name = configs[i]
        post.likes_count = likes
        post.save(update_fields=['likes_count'])
        print(f"Post: {post.outfit.name[:30]:<30} -> Set likes to {likes:<4} [{badge_name}]")

    print("-" * 50)
    print("Done! Refresh the feed to see the badges.")

if __name__ == '__main__' or True:
    seed_badges()
