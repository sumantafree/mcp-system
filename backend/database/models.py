"""
MCP System — Database Models (PostgreSQL / SQLAlchemy)
Full schema covering all 9 MCP modules.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Enum, JSON, Float, BigInteger
)
from sqlalchemy.orm import relationship
import enum
from database.database import Base


# ─────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────

class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    admin = "admin"
    member = "member"
    viewer = "viewer"


class TaskPriority(str, enum.Enum):
    urgent = "urgent"
    high = "high"
    medium = "medium"
    low = "low"


class TaskStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    review = "review"
    done = "done"
    cancelled = "cancelled"


class ContentStatus(str, enum.Enum):
    draft = "draft"
    review = "review"
    published = "published"
    archived = "archived"


class LeadStatus(str, enum.Enum):
    new = "new"
    contacted = "contacted"
    qualified = "qualified"
    proposal = "proposal"
    won = "won"
    lost = "lost"


class NotificationType(str, enum.Enum):
    email = "email"
    whatsapp = "whatsapp"
    in_app = "in_app"


# ─────────────────────────────────────────
# 1. USERS & AUTH
# ─────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True)
    full_name = Column(String(255))
    hashed_password = Column(String(255))
    avatar_url = Column(Text)
    role = Column(Enum(UserRole), default=UserRole.member)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    google_id = Column(String(255), unique=True, nullable=True)
    phone = Column(String(20))
    whatsapp_number = Column(String(20))
    timezone = Column(String(50), default="Asia/Kolkata")
    preferences = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    tasks = relationship("Task", back_populates="owner", foreign_keys="Task.owner_id")
    activity_logs = relationship("ActivityLog", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


# ─────────────────────────────────────────
# 2. TASK MANAGER MCP
# ─────────────────────────────────────────

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    priority = Column(Enum(TaskPriority), default=TaskPriority.medium)
    status = Column(Enum(TaskStatus), default=TaskStatus.todo)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    tags = Column(JSON, default=[])
    attachments = Column(JSON, default=[])
    ai_summary = Column(Text)
    estimated_hours = Column(Float)
    actual_hours = Column(Float)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    parent_task_id = Column(Integer, ForeignKey("tasks.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="tasks", foreign_keys=[owner_id])
    project = relationship("Project", back_populates="tasks")
    subtasks = relationship("Task", backref="parent", remote_side=[id])


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    color = Column(String(7), default="#3B82F6")
    icon = Column(String(50))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    deadline = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="project")


# ─────────────────────────────────────────
# 3. SEO MCP
# ─────────────────────────────────────────

class SEOKeyword(Base):
    __tablename__ = "seo_keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(500), nullable=False, index=True)
    cluster_name = Column(String(255))
    search_volume = Column(Integer)
    difficulty = Column(Float)
    cpc = Column(Float)
    language = Column(String(10), default="en")
    intent = Column(String(50))  # informational, commercial, transactional, navigational
    related_keywords = Column(JSON, default=[])
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class SEOMeta(Base):
    __tablename__ = "seo_meta"

    id = Column(Integer, primary_key=True, index=True)
    page_url = Column(Text, nullable=False)
    meta_title = Column(String(70))
    meta_description = Column(String(160))
    og_title = Column(String(255))
    og_description = Column(Text)
    og_image = Column(Text)
    focus_keyword = Column(String(255))
    schema_markup = Column(JSON)
    language = Column(String(10), default="en")
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BrokenLink(Base):
    __tablename__ = "broken_links"

    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(Text)
    broken_url = Column(Text, nullable=False)
    status_code = Column(Integer)
    redirect_to = Column(Text)
    is_fixed = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    detected_at = Column(DateTime, default=datetime.utcnow)
    fixed_at = Column(DateTime)


# ─────────────────────────────────────────
# 4. CONTENT MCP
# ─────────────────────────────────────────

class ContentPost(Base):
    __tablename__ = "content_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    slug = Column(String(500), unique=True, index=True)
    content = Column(Text)
    excerpt = Column(Text)
    content_type = Column(String(50))  # blog, news, social, caption, script
    language = Column(String(10), default="en")
    target_keyword = Column(String(255))
    word_count = Column(Integer)
    readability_score = Column(Float)
    seo_score = Column(Float)
    status = Column(Enum(ContentStatus), default=ContentStatus.draft)
    platform = Column(String(50))  # website, instagram, twitter, youtube
    ai_model_used = Column(String(100))
    prompt_used = Column(Text)
    tags = Column(JSON, default=[])
    meta = Column(JSON, default={})
    owner_id = Column(Integer, ForeignKey("users.id"))
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────
# 5. SOCIAL MEDIA MCP
# ─────────────────────────────────────────

class SocialPost(Base):
    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False)  # instagram, twitter, linkedin, facebook
    caption = Column(Text)
    hashtags = Column(JSON, default=[])
    media_urls = Column(JSON, default=[])
    scheduled_at = Column(DateTime)
    published_at = Column(DateTime)
    status = Column(String(20), default="draft")  # draft, scheduled, published, failed
    engagement = Column(JSON, default={})  # likes, comments, shares, views
    ai_suggested = Column(Boolean, default=False)
    trend_tags = Column(JSON, default=[])
    owner_id = Column(Integer, ForeignKey("users.id"))
    content_post_id = Column(Integer, ForeignKey("content_posts.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False)
    account_name = Column(String(255))
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    follower_count = Column(BigInteger, default=0)
    is_active = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────
# 6. YOUTUBE MCP
# ─────────────────────────────────────────

class YouTubeVideo(Base):
    __tablename__ = "youtube_videos"

    id = Column(Integer, primary_key=True, index=True)
    youtube_id = Column(String(20), unique=True)
    title = Column(String(500))
    description = Column(Text)
    tags = Column(JSON, default=[])
    thumbnail_url = Column(Text)
    script = Column(Text)
    shorts_script = Column(Text)
    status = Column(String(20), default="draft")
    views = Column(BigInteger, default=0)
    likes = Column(BigInteger, default=0)
    comments = Column(BigInteger, default=0)
    duration_seconds = Column(Integer)
    published_at = Column(DateTime)
    ai_title_suggestions = Column(JSON, default=[])
    ai_thumbnail_prompts = Column(JSON, default=[])
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────
# 7. CRM + WHATSAPP MCP
# ─────────────────────────────────────────

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(20))
    whatsapp = Column(String(20))
    company = Column(String(255))
    source = Column(String(100))  # website, whatsapp, social, referral
    status = Column(Enum(LeadStatus), default=LeadStatus.new)
    deal_value = Column(Float)
    notes = Column(Text)
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    ai_score = Column(Float)  # AI lead scoring 0-100
    last_contacted_at = Column(DateTime)
    next_follow_up = Column(DateTime)
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("WhatsAppMessage", back_populates="lead")
    follow_ups = relationship("FollowUp", back_populates="lead")


class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    direction = Column(String(10))  # inbound | outbound
    message = Column(Text, nullable=False)
    media_url = Column(Text)
    status = Column(String(20), default="sent")  # sent, delivered, read, failed
    twilio_sid = Column(String(100))
    sent_at = Column(DateTime, default=datetime.utcnow)
    is_ai_generated = Column(Boolean, default=False)

    lead = relationship("Lead", back_populates="messages")


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    channel = Column(String(20))  # email | whatsapp | call
    message = Column(Text)
    scheduled_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime)
    status = Column(String(20), default="pending")  # pending, sent, failed, cancelled
    is_ai_generated = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="follow_ups")


# ─────────────────────────────────────────
# 8. WEBSITE MCP
# ─────────────────────────────────────────

class WebsiteScan(Base):
    __tablename__ = "website_scans"

    id = Column(Integer, primary_key=True, index=True)
    website_url = Column(Text, nullable=False)
    total_pages = Column(Integer)
    broken_links_count = Column(Integer, default=0)
    avg_load_time_ms = Column(Float)
    performance_score = Column(Float)
    seo_score = Column(Float)
    accessibility_score = Column(Float)
    scan_result = Column(JSON, default={})
    status = Column(String(20), default="pending")
    owner_id = Column(Integer, ForeignKey("users.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class AutoPage(Base):
    __tablename__ = "auto_pages"

    id = Column(Integer, primary_key=True, index=True)
    page_title = Column(String(500))
    page_slug = Column(String(500))
    page_content = Column(Text)
    page_type = Column(String(50))  # landing, blog, product, faq
    target_keyword = Column(String(255))
    status = Column(String(20), default="draft")
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────
# 9. ANALYTICS MCP
# ─────────────────────────────────────────

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)
    module = Column(String(50))  # task, seo, content, social, etc.
    user_id = Column(Integer, ForeignKey("users.id"))
    meta_data = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True, index=True)
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=False)
    report_data = Column(JSON, default={})
    ai_insights = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    generated_at = Column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────
# 10. SYSTEM — NOTIFICATIONS & LOGS
# ─────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text)
    type = Column(Enum(NotificationType), default=NotificationType.in_app)
    is_read = Column(Boolean, default=False)
    action_url = Column(Text)
    meta_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(255), nullable=False)
    module = Column(String(50))
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    details = Column(JSON, default={})
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="activity_logs")


class AIMemory(Base):
    """Stores context memory per user/module for multi-step AI reasoning."""
    __tablename__ = "ai_memory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    module = Column(String(50), nullable=False)  # task, seo, content, etc.
    memory_key = Column(String(255), nullable=False)
    memory_value = Column(Text)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
