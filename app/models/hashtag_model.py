from sqlalchemy import Column, ForeignKey, Index, PrimaryKeyConstraint, select, Integer, String
from sqlalchemy.orm import relationship, Session, Mapped

from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .post_model import Post

# --- Association Table for Many-to-Many Relationship ---
# This model links Posts and Hashtags.

class PostHashtag(Base):
    """
    Association table for the many-to-many relationship between Posts and Hashtags.
    """
    __tablename__ = 'post_hashtags'
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    hashtag_id = Column(Integer, ForeignKey('hashtags.id', ondelete='CASCADE'), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('post_id', 'hashtag_id'),
        Index('idx_posthashtags_hashtag_id', 'hashtag_id'),
    )

# --- Main Hashtag Model ---

class Hashtag(Base):
    """
    Represents a unique hashtag.
    """
    __tablename__ = 'hashtags'

    id = Column(Integer, primary_key=True)
    tag_name = Column(String(100), unique=True, nullable=False)

    __table_args__ = (
        Index('idx_hashtags_tag_name', 'tag_name', unique=True),
    )

    # --- Relationships ---
    posts: Mapped[list['Post']] = relationship("Post", secondary='post_hashtags', back_populates="hashtags", viewonly=True)
    # Prevents modification through this side of the relationship

    def __repr__(self):
        return f'<Hashtag id={self.id} tag_name="{self.tag_name}">'

    # --- Class Methods ---
    
    @classmethod
    def find_or_create(cls, session: Session, tag_name: str) -> 'Hashtag':
        """
        Efficiently finds an existing hashtag by its name or creates a new one.
        This is the primary tool for the service layer to manage hashtags.
        """
        # Clean the tag name
        clean_tag = tag_name.strip().lower()
        if not clean_tag:
            raise ValueError("Tag name cannot be empty.")
        
        # Check if the hashtag already exists
        stmt = select(cls).where(cls.tag_name == clean_tag)
        existing_hashtag = session.execute(stmt).scalar_one_or_none()
        
        if existing_hashtag:
            return existing_hashtag
        else:
            # If not, create a new one
            new_hashtag = cls(tag_name=clean_tag)
            session.add(new_hashtag)
            session.flush() # Flush to get the ID for the new hashtag
            return new_hashtag