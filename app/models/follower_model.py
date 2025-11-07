from sqlalchemy import Column, ForeignKey, TIMESTAMP, Index, PrimaryKeyConstraint, select, delete, exists, Integer
from sqlalchemy.orm import relationship, Session, Mapped
from sqlalchemy.sql import func
from app.models.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user_model import User

class Follower(Base):
    __tablename__ = 'followers'

    # Foreign key to the User who is doing the following
    follower_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Foreign key to the User who is being followed
    followed_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Timestamp for when the follow relationship was created
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        PrimaryKeyConstraint('follower_id', 'followed_id'), # Composite Primary Key
        Index('idx_followers_followed_id', 'followed_id'),
    )


    def __repr__(self):
        return f'<Followers {self.follower_id} follows {self.followed_id}>'
    
    @classmethod
    def create_follow(cls, session: Session, follower_id: int, followed_id: int) -> 'Follower | None':
        """
        Creates a new follow relationship.
        Raises ValueError if a user tries to follow themselves or if the relationship already exists.
        """
        if followed_id == follower_id:
            raise ValueError(f"A user cannot follow themselves.")
        
        if cls.is_following(session, follower_id=follower_id, followed_id=followed_id):
            raise ValueError(f"User {follower_id} already follows user {followed_id}.")

        new_follow = cls(follower_id=follower_id, followed_id=followed_id)
        session.add(new_follow)
        return new_follow
    
    @classmethod
    def delete_follow(cls, session: Session, follower_id: int, followed_id: int) -> bool:
        """
        Deletes an existing follow relationship.
        Returns True if a relationship was deleted, False otherwise.
        """
        stmt = delete(cls).where(
            cls.follower_id == follower_id,
            cls.followed_id == followed_id
        )
        result = session.execute(stmt)
        return result.rowcount > 0
    
    @classmethod
    def is_following(cls, session: Session, follower_id: int, followed_id: int) -> bool:
        """Checks if a 'follower' user is following a 'followed' user."""
        if follower_id == followed_id:
            return False  

        stmt = select(cls.follower_id).where( 
            cls.follower_id == follower_id,
            cls.followed_id == followed_id
        )
        return session.execute(select(exists(stmt))).scalar_one()