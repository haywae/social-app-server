from app.models import Post

def serialize_post(post: Post) -> dict:
    """
    Serializes a Post object with a consistent, nested structure.
    """
    # This matches the structure of other serializers.
    author_data = {
        "displayName": "Unknown User",
        "username": "unknown",
        "avatarUrl": None
    }
    if post.user:
        author_data = {
            "displayName": post.user.display_name,
            "username": post.user.username,
            "avatarUrl": post.user.profile_picture_url,
        }

        return {
        "id": str(post.public_id),
        
        # --- Flatten the author data into top-level keys ---
        "authorName": author_data["displayName"],
        "authorUsername": author_data["username"],
        "authorAvatarUrl": author_data["avatarUrl"],
        
        "content": post.content,
        "createdAt": post.created_at.isoformat(),
        "likeCount": post.like_count,
        "isLiked": getattr(post, 'is_liked_by_requester', False),
        "postType": post.post_type.name,
        
        "hashtags": [tag.tag_name for tag in post.hashtags] if post.hashtags else []
    }
    
