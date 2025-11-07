import re

# This is the Python-compatible regex pattern
# We compile it once for efficiency.
MENTION_REGEX = re.compile(r"@([\w.-]*[\w-])")
