from sqlalchemy import Column, ForeignKey, TIMESTAMP, Index, PrimaryKeyConstraint, select, delete, exists, Integer, UUID as SqlUUID
from sqlalchemy.orm import relationship, Session, Mapped
from sqlalchemy.sql import func
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .post_model import Post
    from .user_model import User

class PostLike(Base):
    """ Represents a 'like' relationship between a User and a Post."""
    __tablename__ = 'post_likes'
    # Foreign key to the User who liked the post.
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Foreign key to the Post that was liked.
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)

    # Timestamp for when the like was created.
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # --- Table Arguments ---
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'post_id'),
        Index('idx_post_likes_post_id', 'post_id'),
    )

    # --- Relationships ---
    user: Mapped['User'] = relationship("User", back_populates="likes")
    post: Mapped['Post'] = relationship("Post", back_populates="likes")

    def __repr__(self):
        return f'<Like user_id={self.user_id} post_id={self.post_id}>'

    # --- Class Methods for DB Operations ---
    @classmethod
    def create(cls, session: Session, user_id: int, post_id: int) -> 'PostLike':
        """
        Creates a new like relationship. It does not perform any business logic checks
        or have side effects like incrementing counters.
        """
        new_like = cls(user_id=user_id, post_id=post_id)
        session.add(new_like)
        return new_like

    @classmethod
    def delete(cls, session: Session, user_id: int, post_id: int) -> bool:
        """
        Deletes a like relationship. Returns True if a row was deleted, False otherwise.
        It does not have side effects like decrementing counters.
        """
        query = delete(cls).where(
            cls.user_id == user_id,
            cls.post_id == post_id
        )
        result = session.execute(query)
        return result.rowcount > 0
    
    @classmethod
    def exists(cls, session: Session, user_id: int, post_id: int) -> bool:
        """
        Checks if a user has already liked a specific post.
        This is the primary tool for the service layer to check for duplicates.
        """
        query = select(cls).where(
            cls.user_id == user_id,
            cls.post_id == post_id
        )
        return session.execute(select(exists(query))).scalar()


