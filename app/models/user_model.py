from datetime import date
from uuid import uuid4, UUID
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from sqlalchemy import Column, Integer, UUID as SqlUUID, String, Enum as SqlEnum, Text, Date, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func, select, exists, or_
from sqlalchemy.orm import Session, relationship, Mapped
from app.models.base import Base
from utils.model_utils import UserStatus, HasherConfig
from geoalchemy2 import Geometry, WKTElement, Geography
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_Distance
import logging
from typing import TYPE_CHECKING
from sqlalchemy.orm.attributes import flag_modified

if TYPE_CHECKING:
    from .post_model import Post
    from .follower_model import Follower
    from .post_like_model import PostLike
    from .notification_model import Notification

#----------------
# User Model
#----------------
class User(Base):
    __tablename__ = 'users'
    #------> Essential <------
    id = Column(Integer, primary_key=True)
    public_id = Column(SqlUUID(as_uuid=True), default=uuid4, unique=True, nullable=False)  # External ID
    google_id = Column(String(255), nullable=True, unique=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(128), nullable=False, unique=True)
    hashed_password = Column(String(256), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    country = Column(String(128), nullable=True)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    display_name = Column(String(256), nullable=False)

    #------> Optional <------
    profile_picture_url = Column(String(1024))
    bio = Column(Text)
    location = Column(Geometry('POINT', srid=4326), nullable=True) 
    
    #-----> General Settings <-----
    account_status = Column(
        SqlEnum(UserStatus, name="user_status_enum", create_type=True),
        nullable=False,
        server_default=UserStatus.PENDING_VERIFICATION.name,
        default=UserStatus.PENDING_VERIFICATION
    )
    profile_info = Column(JSONB)
    notification_preferences = Column(JSONB)
    privacy_settings = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True))

    #------> Define relationships <-----
    posts: Mapped[list['Post']] = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    likes: Mapped[list['PostLike']] = relationship("PostLike", back_populates="user", cascade="all, delete-orphan")

    notifications: Mapped[list['Notification']] = relationship(
        "Notification", back_populates="recipient", foreign_keys="Notification.recipient_user_id", cascade="all, delete-orphan"
    )

    followed: Mapped[list['User']] = relationship(
        "User",
        secondary="followers",  # The name of the intermediary table
        primaryjoin="User.id == Follower.follower_id",
        secondaryjoin="User.id == Follower.followed_id",
        back_populates="followers"
    )

    followers: Mapped[list['User']] = relationship(
        "User",
        secondary="followers",
        primaryjoin="User.id == Follower.followed_id",
        secondaryjoin="User.id == Follower.follower_id",
        back_populates="followed"
    )

    mentioned_in_posts: Mapped[list['Post']] = relationship(
        "Post", 
        secondary="post_mentions", 
        back_populates="mentioned_users"
    )

    __table_args__ = (
        Index('idx_users_username_lower', func.lower(username), unique=True),
        Index('idx_users_email_lower', func.lower(email), unique=True),
    )

    @staticmethod
    def _get_password_hasher() -> PasswordHasher:
    #-----> Password hashser object from Argon 2
        return PasswordHasher(time_cost=HasherConfig.TIME_COST, 
            memory_cost=HasherConfig.MEMORY_COST, parallelism=HasherConfig.PARALLELISM, 
            hash_len=HasherConfig.HASH_LEN, salt_len=HasherConfig.SALT_LEN
        )

    @staticmethod
    def _convert_coordinates_to_wkt(location_coords: tuple[float, float] = None) -> 'WKTElement | None':
        """ Converts (longitude, latitude) to a WKTElement, or returns None."""
        if location_coords:
            longitude, latitude = location_coords
            if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
                raise ValueError("Invalid longitude or latitude values.")
            return WKTElement(f"POINT({longitude} {latitude})", srid=4326)
        return None

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}', status='{self.account_status.name}')>"
    
    def set_password(self, password: str) -> None: 
        """ 
            Hashes the provided plain-text password using the class-level Argon2 PasswordHasher 
            instance (self.ph) and stores the resulting hash in the hashed_password attribute. 
        """
        ph = self._get_password_hasher()
        self.hashed_password = ph.hash(password)

    def check_password(self, password: str) -> bool: 
        """ Compares the existing password with the provided password """
        ph = self._get_password_hasher()
        try:
            ph.verify(self.hashed_password, password)

            if ph.check_needs_rehash(self.hashed_password):
                self.set_password(password)
            return True
        except VerifyMismatchError:
            return False
        except VerificationError:
            logging.error(f"Invalid hash or verification error for user {self.username}")
            return False


    #=================================
    # Core Class Methods for Data Access
    #=================================
    @classmethod
    def create_user(cls, session: Session, **kwargs) -> 'User':
        """
        Creates a new user with the given attributes.
        Requires username, email, password, date_of_birth, country and display_name.
        """
        required_fields = {"username", "email", "password", "date_of_birth", "country", "display_name"}
        if not required_fields.issubset(kwargs.keys()):
            raise ValueError(f"Missing one or more required fields: {required_fields - set(kwargs.keys())}")

        new_user = cls(username=kwargs["username"], email=kwargs["email"],
            date_of_birth=kwargs["date_of_birth"], country=kwargs["country"],
            display_name=kwargs["display_name"]
        )
        new_user.set_password(kwargs["password"])

        if "location_coords" in kwargs:
            new_user.location = cls._convert_coordinates_to_wkt(kwargs["location_coords"])

        session.add(new_user)
        return new_user
    
    @classmethod
    def update(cls, session: Session, user_id: int, **kwargs) -> 'User | None':
        """
        Refactored: A flexible method to update any user attribute.
        This method is now more generic. The service layer is responsible for
        validating which fields are allowed to be updated.
        Fields: username, email, date_of_birth, country, display_name, location_coords etc..
        """
        user = session.get(cls, user_id)
        if not user:
            return None
        
        # Fields that should never be updated directly via this method.
        forbidden_fields = {
            "id", "public_id", "hashed_password", "created_at", "updated_at", "last_login_at"
        }
        
        for key, value in kwargs.items():
            if key in forbidden_fields:
                # Silently ignore or raise an error, depending on desired behavior.
                # Ignoring is often safer to prevent malicious data injection.
                continue
            
            # Handle special cases
            if key == "password":
                user.set_password(value)
            elif key == "location_coords":
                user.location = cls._convert_coordinates_to_wkt(value)
            # Handle all other standard attributes
            elif hasattr(user, key):
                setattr(user, key, value)
                
        return user
    
    #====== Core Delete Method =====
    @classmethod
    def delete(cls, session: Session, user_id: int) -> bool:
        """Deletes a user record from the database."""
        user = session.get(cls, user_id)
        if user:
            session.delete(user)
            return True
        return False
    
    #========== 1.Specific Finders
    @classmethod
    def get_by_id(cls, session: Session, user_id: int) ->'User | None':
        return session.get(cls, user_id)
    
    @classmethod
    def get_by_public_id(cls, session: Session, public_id: UUID) -> 'User | None':
        query = select(cls).where(cls.public_id == public_id)
        return session.execute(query).scalar_one_or_none()
    
    @classmethod
    def get_by_identifier(cls, session: Session, identifier: str) -> 'User | None':
        """Finds a user by username or email."""
        lower_identifier = identifier.lower()
        return session.execute(
            select(cls).where(
                or_(
                    func.lower(cls.username) == lower_identifier, 
                    func.lower(cls.email) == lower_identifier
                )
            )
        ).scalar_one_or_none()
