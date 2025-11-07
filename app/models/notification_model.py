from uuid import uuid4, UUID
from sqlalchemy import Column, ForeignKey, TIMESTAMP, Index, select, update, func, String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID as SqlUUID
from sqlalchemy.orm import relationship, Session, Mapped

from app.models.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user_model import User

class Notification(Base):
    """
    Represents a notification for a user about an action in the application.
    """
    __tablename__ = 'notifications'

    # --- Columns ---
    id = Column(Integer, primary_key=True)
    public_id = Column(SqlUUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    
    # The user who should receive the notification.
    recipient_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # The user who triggered the notification Can be null if the actor deletes their account.
    actor_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # The action that generated the notification. e.g., 'like',  'follow', 'mention'.
    action_type = Column(String(50), nullable=False)
    
    # --- Polymorphic Target Columns ---
    # The source object that the action was performed on.
    target_type = Column(String(50), nullable=True) # e.g., 'post', 'user'
    target_id = Column(Integer, nullable=True)
    
    is_read = Column(Boolean, nullable=False, server_default='f')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # --- Table Arguments for Indexes ---
    __table_args__ = (
        Index('idx_notifications_recipient_is_read', 'recipient_user_id', 'is_read', created_at.desc()),
    )

    # --- Relationships ---
    recipient: Mapped['User'] = relationship("User", foreign_keys=[recipient_user_id], back_populates="notifications")
    actor: Mapped['User'] = relationship("User", foreign_keys=[actor_user_id])

    def __repr__(self):
            return f'<Notification id={self.id} recipient={self.recipient_user_id} action={self.action_type}>'

    # --- Class Methods ---
    @classmethod
    def create( cls, session: Session, recipient_user_id: int, *, actor_user_id: int | None = None,
        action_type: str, target_type: str | None = None, target_id: int | None = None
    ) -> 'Notification':
        """ 
        Creates a new notification.
        The recipient is the user who should receive the notification. \n
        The actor is the user who triggered the notification. \n
        The action is the type of notification. 'Like', 'Follow \n
        The target is the object that the notification was performed on. 'Post', 'User' \n
        """
        # Avoid self-notification
        if recipient_user_id == actor_user_id:
            return None

        new_notification = cls(
            recipient_user_id=recipient_user_id,
            actor_user_id=actor_user_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id
        )
        session.add(new_notification)
        return new_notification

    # --- Finder Methods ---

    @classmethod
    def get_by_id(cls, session: Session, notification_id: int) -> 'Notification | None':
        """Retrieves a notification by its internal integer ID."""
        return session.get(cls, notification_id)

    @classmethod
    def get_by_public_id(cls, session: Session, public_id: UUID) -> 'Notification | None':
        """Retrieves a notification by its public UUID."""
        return session.execute(
            select(cls).where(cls.public_id == public_id)
        ).scalar_one_or_none()