"""
    A package for managing resources
"""

from typing import TYPE_CHECKING
from utils.app_utils import CustomApi

from .account_management import (
    ChangePasswordResource, ChangeUsernameResource, ConfirmEmailChangeResource, 
    RequestEmailChangeResource, CreatePasswordResource
)

from .auth import (
    LoginResource, LogoutResource, AuthCheckResource, RefreshTokenResource, GoogleLoginResource
)


from .health_check.health_check import ReadinessProbe, LivenessProbe

from .media import ProfilePictureResource

from .notitifications import NotificationListResource, MarkNotificationsAsReadResource

from .posts import (
    UserPostListResource, PostListResource, CreatePostResource, DeletePostResource, UpdatePostResource, 
    UserPostResource
)


from .social_interactions import (
    FollowResource, PostLikeResource, 
)

from .user_management import  (
    RegisterResource, RequestPasswordResetResource, ResetPasswordResource, OnboardingResource, UserProfileResource, 
    UserSettingsResource, VerifyEmailResource, ResendVerificationEmailResource, 
    ResendVerificationForAuthenticatedUserResource, FollowerListResource, FollowingListResource
)

if TYPE_CHECKING:
    from flask import Flask

def initialize_routes(app: 'Flask') -> None:
    api = CustomApi(app)

    # ----- Account Management Endpoints -----
    api.add_resource(ChangeUsernameResource, '/settings/username')
    api.add_resource(ChangePasswordResource, '/settings/password')
    api.add_resource(ConfirmEmailChangeResource, '/settings/email/confirm-change')
    api.add_resource(CreatePasswordResource, '/settings/password/create')
    api.add_resource(RequestEmailChangeResource, '/settings/email/request-change')
    api.add_resource(ResendVerificationForAuthenticatedUserResource, '/settings/email/resend-verification')

    # ----- Auth Endpoints -----
    api.add_resource(AuthCheckResource, '/auth-check')
    api.add_resource(GoogleLoginResource, '/login/google')
    api.add_resource(LoginResource, '/login')
    api.add_resource(LogoutResource, '/logout')
    api.add_resource(RefreshTokenResource, '/refresh-token')

    # ----- Health Check Endpoints -----
    api.add_resource(LivenessProbe, '/live')
    api.add_resource(ReadinessProbe, '/ready')

    # -----  Media Endpoints -----
    api.add_resource(ProfilePictureResource, '/settings/profile-picture')

    # ----- Notification Endpoints -----
    api.add_resource(NotificationListResource, '/notifications')
    api.add_resource(MarkNotificationsAsReadResource, '/notifications/mark-as-read')

    # ----- Social Interaction Endpoints -----
    api.add_resource(FollowResource, '/users/<string:username>/follow')
    api.add_resource(PostLikeResource, '/posts/<uuid:public_id>/like')

    # ----- Posts Endpoints -----
    api.add_resource(CreatePostResource, '/create-post')
    api.add_resource(DeletePostResource, '/posts/<uuid:public_id>')
    api.add_resource(PostListResource, '/feeds')
    api.add_resource(UpdatePostResource, '/posts/<uuid:public_id>')
    api.add_resource(UserPostResource, '/posts/<uuid:public_id>')
    api.add_resource(UserPostListResource, '/users/<string:username>/posts')

    # ----- User Management Endpoints -----
    api.add_resource(FollowerListResource, '/profile/<string:username>/followers')
    api.add_resource(FollowingListResource, '/profile/<string:username>/following')
    api.add_resource(OnboardingResource, '/onboarding/complete')
    api.add_resource(RegisterResource, '/register')
    api.add_resource(RequestPasswordResetResource, '/request-password-reset')
    api.add_resource(ResendVerificationEmailResource, '/resend-verification')
    api.add_resource(ResetPasswordResource, '/reset-password/<string:token>')
    api.add_resource(UserProfileResource, '/users/<string:username>')
    api.add_resource(UserSettingsResource, '/settings')
    api.add_resource(VerifyEmailResource, '/verify-email')