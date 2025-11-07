from enum import Enum

class UserStatus(Enum):
    ACTIVE = 'active'
    PENDING_VERIFICATION = 'pending_verification'
    SUSPENDED = 'suspended'
    DEACTIVATED_BY_USER = 'deactivated_by_user' 
    DEACTIVATED_BY_ADMIN = 'deactivated_by_admin'

class PostVisibility(Enum):
    PUBLIC = "public"
    FOLLOWERS_ONLY = "followers_only"
    PRIVATE = "private"

class StatFields(Enum):
    LIKE_COUNT = "like_count"
    COMMENT_COUNT = "comment_count"
    RESHARE_COUNT = "reshare_count"

class HasherConfig():
    TIME_COST = 3 
    MEMORY_COST = 65536   # Memory cost (m): Memory usage in KiB. Higher is more secure but uses more memory.
    PARALLELISM = 4   # 64 MB   # Parallelism (p): Number of parallel threads.
    HASH_LEN = 32     # Hash length (output size in bytes)
    SALT_LEN = 16     # Salt length (random salt generated per password, in bytes)

class PostType(Enum):
    REGULAR = "REGULAR"
    RATE_POST = "RATE_POST"