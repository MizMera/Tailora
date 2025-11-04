# 👥 Tailora User Roles & Permissions System

## Overview
Tailora implements a comprehensive role-based access control (RBAC) system to provide different features and limitations based on user roles.

---

## 🎭 User Roles

### 1. **👤 User (Utilisateur Standard)** - `role='user'`
**Default role for new registrations**

**Features:**
- ✅ Access to basic wardrobe management
- ✅ Create up to 50 wardrobe items
- ✅ Create up to 20 outfits
- ✅ Basic outfit planning
- ✅ View social feed
- ✅ Follow other users
- ❌ No AI recommendations
- ❌ Limited weather integration
- ❌ Cannot create style challenges

---

### 2. **⭐ Premium (Utilisateur Premium)** - `role='premium'`
**Paid subscription tier**

**Features:**
- ✅ All User features, plus:
- ✅ Upload up to 1,000 wardrobe items
- ✅ Create up to 500 outfits
- ✅ **AI-powered outfit recommendations**
- ✅ Advanced weather-based suggestions
- ✅ Unlimited outfit history
- ✅ Export wardrobe data
- ✅ Priority support
- ✅ Ad-free experience
- ✅ Advanced analytics dashboard

**Pricing:** Managed via `premium_until` field

---

### 3. **👔 Stylist (Styliste)** - `role='stylist'`
**Professional fashion experts**

**Features:**
- ✅ All Premium features, plus:
- ✅ Create and publish style guides
- ✅ **Create style challenges** for community
- ✅ Verified badge: "👔 Styliste"
- ✅ Ability to curate outfit collections
- ✅ Access to professional analytics
- ✅ Featured in stylist directory
- ✅ Can offer consultation services

**How to get:** Approved by admin based on credentials

---

### 4. **🌟 Influencer (Influenceur)** - `role='influencer'`
**Content creators and fashion influencers**

**Features:**
- ✅ All Premium features, plus:
- ✅ Create branded style challenges
- ✅ Verified badge: "🌟 Influenceur"
- ✅ Enhanced social visibility
- ✅ Analytics on follower engagement
- ✅ Collaboration opportunities
- ✅ Featured in influencer spotlight
- ✅ Priority in social feeds

**How to get:** Application + minimum follower count (500+)

---

### 5. **🛡️ Admin (Administrateur)** - `role='admin'`
**Platform administrators**

**Features:**
- ✅ **All system permissions**
- ✅ Access to Django admin panel
- ✅ User management capabilities
- ✅ Content moderation
- ✅ Role assignment
- ✅ Platform analytics
- ✅ System configuration

**How to get:** Assigned by existing admin or superuser

---

## 📊 Account Status

Users can have different account statuses:

| Status | Value | Description |
|--------|-------|-------------|
| 🟢 **Active** | `active` | Normal operation, full access |
| ⚪ **Inactive** | `inactive` | Account exists but not in use |
| 🟡 **Suspended** | `suspended` | Temporarily restricted (violation) |
| 🔴 **Banned** | `banned` | Permanently banned from platform |

---

## 🔐 Permission Methods

### Role Checking
```python
# Check if user has premium access
user.is_premium_user()  # True for premium, stylist, influencer, admin

# Check specific roles
user.is_stylist()       # True for stylist, admin
user.is_influencer()    # True for influencer, admin
user.is_admin_user()    # True for admin role or superuser
```

### Feature Permissions
```python
# Check feature access
user.can_create_unlimited_outfits()      # Premium+
user.can_access_ai_recommendations()     # Premium+
user.can_upload_unlimited_items()        # Premium+
user.can_create_challenges()             # Stylist, Influencer, Admin
```

### Limits
```python
# Get user limits
user.get_max_wardrobe_items()  # 50 for free, 1000 for premium
user.get_max_outfits()          # 20 for free, 500 for premium
```

### Display
```python
# Get role badge for UI
user.get_role_display_badge()
# Returns: '⭐ Premium', '👔 Styliste', '🌟 Influenceur', '🛡️ Admin'
```

---

## 📈 User Statistics

The system tracks:
- `wardrobe_items_count` - Total wardrobe items
- `outfits_created_count` - Total outfits created
- `posts_count` - Total social posts
- `followers_count` - Number of followers
- `following_count` - Number of users following
- `last_active` - Last activity timestamp

### Increment Methods
```python
user.increment_wardrobe_count()  # When adding wardrobe item
user.increment_outfits_count()   # When creating outfit
user.increment_posts_count()     # When publishing post
```

---

## 🛠️ Admin Actions

Admins can perform bulk actions in Django Admin:

1. **Make Premium (1 an)** - Upgrade users to Premium for 1 year
2. **Rendre Styliste** - Promote users to Stylist role
3. **Rendre Influenceur** - Promote users to Influencer role
4. **Activer les comptes** - Activate suspended accounts
5. **Suspendre les comptes** - Suspend accounts for violations

---

## 🎯 Implementation Examples

### Check Premium Features
```python
@login_required
def create_outfit_view(request):
    user = request.user
    
    # Check if user reached outfit limit
    if user.outfits_created_count >= user.get_max_outfits():
        if not user.is_premium_user():
            messages.error(request, "Limite atteinte. Passez à Premium!")
            return redirect('upgrade_premium')
    
    # Allow outfit creation
    # ...
```

### Check Challenge Creation
```python
@login_required
def create_challenge_view(request):
    if not request.user.can_create_challenges():
        messages.error(request, "Seuls les stylistes peuvent créer des défis.")
        return redirect('home')
    
    # Allow challenge creation
    # ...
```

### Display Role Badge in Template
```django
<div class="user-profile">
    <h3>{{ user.username }}</h3>
    {% if user.get_role_display_badge %}
        <span class="badge">{{ user.get_role_display_badge }}</span>
    {% endif %}
</div>
```

---

## 🔄 Role Upgrade Workflow

### Free → Premium
1. User subscribes via payment
2. Set `role='premium'`
3. Set `premium_until` = 1 year from now
4. Unlock premium features

### Premium → Stylist
1. User applies with credentials
2. Admin reviews application
3. Admin approves and changes `role='stylist'`
4. User gets verified badge

### Free → Influencer
1. User applies (must have 500+ followers)
2. Admin reviews social presence
3. Admin approves and changes `role='influencer'`
4. User gets influencer badge

---

## 📱 API Integration

### Serializer Example
```python
class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display_badge', read_only=True)
    is_premium = serializers.SerializerMethodField()
    
    def get_is_premium(self, obj):
        return obj.is_premium_user()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'role', 'role_display', 
            'is_premium', 'wardrobe_items_count', 'outfits_created_count',
            'followers_count', 'following_count'
        ]
```

---

## 🎨 Frontend Badge Display

### CSS Classes
```css
.badge-premium { background: gold; color: #2c2c2c; }
.badge-stylist { background: #7b513b; color: white; }
.badge-influencer { background: linear-gradient(45deg, #ff6b6b, #4ecdc4); color: white; }
.badge-admin { background: #2c2c2c; color: white; }
```

---

## 🔒 Security Considerations

1. **Role verification**: Always check permissions server-side, not just in templates
2. **Status checks**: Verify `is_account_active()` before granting access
3. **Premium expiry**: Check `premium_until` date for time-limited access
4. **Audit logging**: Log all role changes for security

---

## 📊 Database Indexes

The model includes indexes on:
- `role` - Fast role-based queries
- `status` - Quick status filtering
- `is_verified` - Efficient verification checks

---

## 🚀 Future Enhancements

Potential additions:
- [ ] Custom role permissions matrix
- [ ] Time-limited role assignments
- [ ] Role-based content filtering
- [ ] Automated role upgrades based on activity
- [ ] Role achievement system
- [ ] Multi-role support (user can have multiple roles)

---

**Last Updated:** November 4, 2025
**Version:** 1.0
