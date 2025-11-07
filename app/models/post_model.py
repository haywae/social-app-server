from uuid import uuid4
from sqlalchemy import Column, Integer, UUID as SqlUUID, ForeignKey, Text, String, Enum as SqlEnum, DateTime, CheckConstraint, Index, case
from sqlalchemy.sql import select, or_, and_, func, update, exists
from sqlalchemy.orm import Session, relationship, Mapped
from geoalchemy2 import Geometry, WKTElement, Geography
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_Distance

from app.models.base import Base
from app.exceptions import PostNotFoundError, PermissionDeniedError
from utils.model_utils.enums import PostVisibility, PostType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user_model import User
    from .post_model import Post
    from .post_like_model import PostLike
    from .hashtag_model import Hashtag
    
class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True, autoincrement=True) # Internal primary key for performance.
    public_id = Column(SqlUUID(as_uuid=True), default=uuid4, unique=True, nullable=False) # External identifier for public APIs.
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=True) # Text content of the post. Can be restricted with VARCHAR(max_length).
    post_type = Column(
        SqlEnum(PostType, name='post_type_enum', create_type=True), 
        nullable=False, 
        server_default=PostType.REGULAR.name,
        default=PostType.REGULAR,
    )
    media_url = Column(String(1024), nullable=True)
    visibility = Column(
        SqlEnum(PostVisibility, name="post_visibility_enum", create_type=True), 
        nullable=False,
        server_default=PostVisibility.PUBLIC.name,
        default=PostVisibility.PUBLIC, 
    )
    location = Column(Geometry('POINT', srid=4326), nullable=True) 
    like_count = Column(Integer, nullable=False, server_default="0", default=0)
    comment_count = Column(Integer, nullable=False, server_default="0", default=0)
    reshare_count = Column(Integer, nullable=False, server_default="0", default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    #------ Define relationships -----
    user: Mapped['User'] = relationship("User", back_populates="posts")
    likes: Mapped[list['PostLike']] = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")
    hashtags: Mapped[list['Hashtag']] = relationship("Hashtag", secondary='post_hashtags', back_populates="posts", cascade="all, delete")
    mentioned_users: Mapped[list['User']] = relationship("User", secondary="post_mentions", back_populates="mentioned_in_posts")
    
    #------- Table arguments: constraints and indexes
    __table_args__ = (
        CheckConstraint("content IS NOT NULL OR media_url IS NOT NULL", name="ck_post_content_or_media_required"),
        
        #----- Indexes for performance optimization
        Index("idx_posts_user_id", "user_id"), 
        Index("idx_posts_created_at_desc", created_at.desc()), 
        Index("idx_posts_location_gist", "location", postgresql_using="gist", postgresql_where=location.isnot(None)), 
    )

    _stat_fields = ["like_count", "comment_count", "reshare_count"]
    

    #==============================
    # 1. Utility / Static Methods
    #==============================
    @staticmethod
    def _convert_coordinates_to_wkt(location_coords: tuple[float, float] = None) -> WKTElement | None:
        """Converts (longitude, latitude) to a WKTElement, or returns None."""
        if location_coords:
            longitude, latitude = location_coords
            if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
                raise ValueError("Invalid longitude or latitude values.")
            return WKTElement(f"POINT({longitude} {latitude})", srid=4326)
        return None
    
    #=====================
    # 2. Query Methods
    #=====================
    #========================================================
    # Core CRUD Operations (Create, Read, Update, Delete)
    #=========================================================
    @classmethod
    def create(cls, session: Session, user_id: int, content: str = None, media_url: str = None, **kwargs) -> 'Post':
        """
        Creates and stores a new post in the database.
        Can include visibility, tags, and location.
        """
        if not content and not media_url:
            raise ValueError("A post must contain either content or a media URL.")
        
        new_post = cls(
            user_id=user_id, 
            content=content, 
            media_url=media_url, 
            visibility=kwargs.get("visibility", PostVisibility.PUBLIC), 
            location=cls._convert_coordinates_to_wkt(kwargs.get("location_coords")),
            post_type=kwargs.get("post_type", PostType.REGULAR),
            hashtags=kwargs.get("hashtags", []),
            mentioned_users=kwargs.get("mentioned_users", [])
        )
        session.add(new_post)
        return new_post

    @classmethod
    def update(cls, session: Session, post_id: int, requesting_user_id: int, **update_data) -> 'Post':
        """
        Modifies an existing post identified by post_id. 
        updated_data: content, media_url, visibility, tags, location_coords
        """
        post: Post = session.get(cls, post_id)
        if not post:
            return None
        if post.user_id != requesting_user_id:
            raise PermissionDeniedError("You do not have permission to update this post.")
        
        allowed_fields = {"content", "media_url", "visibility", "tags", "location_coords", "hashtags", "mentioned_users"}

        for key, value in update_data.items():
            if key not in allowed_fields:
                raise ValueError(f"Field '{key}' is not allowed for updates.") 
            if key == "location_coords":
                setattr(post, "location", cls._convert_coordinates_to_wkt(value))
            else:
                setattr(post, key, value)
        return post
    
    @classmethod
    def delete(cls, session: Session, post_id: int, requesting_user_id: int) -> bool:
        """Removes a post from the database. """
        post = session.get(cls, post_id)

        if not post:
            return False # Post already deleted or never existed.
        if post.user_id != requesting_user_id:
            raise PermissionDeniedError("You do not have permission to delete this post.")
            
        session.delete(post)
        return True 
    
    #==============================
    # Getter Class Methods with Visibility
    #==============================
    @classmethod
    def get_post_by_id(cls, session: Session, post_id: int, requesting_user_id: int | None = None ) -> 'Post | None':
        """Retrieves a specific post from the database using its internal integer id. """
        from .follower_model import Follower

        query = select(cls).where(cls.id == post_id)
        post = session.execute(query).scalar_one_or_none()

        if not post:
            return None
        if post.visibility == PostVisibility.PUBLIC:
            return post
        if requesting_user_id is None: 
            return None
        if post.user_id == requesting_user_id: 
            return post
        if post.visibility == PostVisibility.FOLLOWERS_ONLY:
            is_follower = session.execute(select(exists().where(
                and_(Follower.follower_id == requesting_user_id, Follower.followed_id == post.user_id)
            ))).scalar()
            if is_follower:
                return post
        
        return None 
    
    @classmethod
    def get_posts_by_user(cls, session: Session, target_user_id: int = None, requesting_user_id: int = None) -> list['Post']:
        """Retrieves a paginated list of posts created by a specific user, identified by target_user_id. """
        from .follower_model import Follower

        query = select(cls).where(cls.user_id == target_user_id)

        # If the target user is the same as the requesting user, return all posts
        if target_user_id == requesting_user_id:
            return session.execute(query.order_by(cls.created_at.desc())).scalars().all()

        visibility_conditions = [cls.visibility == PostVisibility.PUBLIC]
        if requesting_user_id is not None:
            is_follower_subquery = select(exists().where(
                and_(Follower.follower_id == requesting_user_id, Follower.followed_id == target_user_id)
            )).scalar_subquery()
            visibility_conditions.append(and_(cls.visibility == PostVisibility.FOLLOWERS_ONLY, is_follower_subquery))

        query = query.where(or_(*visibility_conditions)).order_by(cls.created_at.desc())
        return session.execute(query).scalars().all()