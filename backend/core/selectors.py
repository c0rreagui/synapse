"""
TikTok UI Selectors Constants
Centralized mapping for data-e2e and CSS selectors to ensure system resilience.
"""

# Profile Branding & Identification
AVATAR_IMG = '[data-e2e="user-user-img"]'
FOLLOWERS_COUNT = '[data-e2e="followers-count"]'
FOLLOWING_COUNT = '[data-e2e="following-count"]'
LIKES_COUNT = '[data-e2e="likes-count"]'
USER_BIO = '[data-e2e="user-bio"]'
USER_TITLE = '[data-e2e="user-title"]'

# Video Feed & Grid
VIDEO_ITEM = '[data-e2e="user-post-item"]'
VIDEO_VIEWS = '[data-e2e="video-views"]'
VIDEO_FEED_FALLBACK = '[class*="DivVideoFeed"] > div'

# Comments
COMMENT_ITEM = '[data-e2e="comment-level-1"]'
COMMENT_CONTENT = '[data-e2e="comment-level-1-content"]'
COMMENT_USERNAME = '[data-e2e="comment-username"]'

# TikTok Studio / Upload
STUDIO_UPLOAD_INPUT = 'input[type="file"]'
STUDIO_SELECT_BUTTON = 'button:has-text("Selecionar")'
STUDIO_CAPTION_TEXTAREA = '.notranslate.public-DraftEditor-content'
STUDIO_POST_BUTTON = 'button:has-text("Postar"), button:has-text("Publicar")'
STUDIO_SCHEDULE_TOGGLE = '.tiktok-switch'
STUDIO_PRIVACY_DROPDOWN = '[class*="PrivacySelection"]'

# Search / Trends
CREATIVE_CENTER_MUSIC_ROW = '[class*="MusicRow"]'
CREATIVE_CENTER_HASHTAG_ROW = '[class*="HashtagRow"]'
