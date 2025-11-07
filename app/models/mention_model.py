from sqlalchemy import Table, Column, Integer, ForeignKey, Index
from .base import Base

class PostMentions(Base):
    __tablename__ = 'post_mentions'
    post_id = Column(Integer, ForeignKey('posts.id', ondelete="CASCADE"), primary_key=True) 
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)

    __table_args__ = (
        Index('idx_post_mentions_post_id', 'post_id'),
        Index('idx_post_mentions_user_id', 'user_id'),
    )
