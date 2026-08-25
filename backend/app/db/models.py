from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class QueryTemplate(Base):
    """Stores canonical structural query templates and retrieval embeddings."""

    __tablename__ = "query_templates"

    template_id = Column(String(50), primary_key=True)
    intent = Column(String(100), nullable=False, index=True)
    question_template = Column(Text, nullable=False)
    retrieval_text = Column(Text, nullable=False)
    sql_template = Column(Text, nullable=False)
    result_type = Column(String(50), nullable=False, default="tabular")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    version = Column(Integer, nullable=False, default=1)
    
    # JSON list of float values for vector embedding (768-dim)
    # Compatible with all PostgreSQL servers regardless of pgvector extension installation
    embedding = Column(JSON, nullable=True)
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    placeholders = relationship(
        "QueryTemplatePlaceholder",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="QueryTemplatePlaceholder.display_order"
    )


class QueryTemplatePlaceholder(Base):
    """Metadata for typed placeholders belonging to a query template."""

    __tablename__ = "query_template_placeholders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(
        String(50),
        ForeignKey("query_templates.template_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    placeholder_name = Column(String(50), nullable=False)
    data_type = Column(String(50), nullable=False)  # REFERENCE, ENUM, INTEGER, DATE_RANGE
    input_mode = Column(String(50), nullable=False, default="searchable_dropdown")
    source_table = Column(String(100), nullable=True)
    source_id_column = Column(String(100), nullable=True)
    source_label_column = Column(String(100), nullable=True)
    required = Column(Boolean, nullable=False, default=True)
    display_order = Column(Integer, nullable=False, default=1)

    template = relationship("QueryTemplate", back_populates="placeholders")


class TemplateTestCase(Base):
    """Held-out paraphrase test cases for retrieval accuracy evaluation."""

    __tablename__ = "template_test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nl_question = Column(Text, nullable=False)
    expected_template_id = Column(
        String(50),
        ForeignKey("query_templates.template_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    expected_entities = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


class QueryExecutionLog(Base):
    """Lightweight audit log recording query execution history."""

    __tablename__ = "query_execution_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_text = Column(Text, nullable=False)
    template_id = Column(
        String(50),
        ForeignKey("query_templates.template_id"),
        nullable=False,
        index=True
    )
    template_version = Column(Integer, nullable=False, default=1)
    bound_parameters = Column(JSON, nullable=False)
    result_row_count = Column(Integer, nullable=True)
    execution_time_ms = Column(Float, nullable=True)
    status = Column(String(50), nullable=False, default="SUCCESS")  # SUCCESS, ERROR
    executed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


class ChatSession(Base):
    """Stores chat session threads for multi-chat support."""

    __tablename__ = "chat_sessions"

    id = Column(String(50), primary_key=True)
    title = Column(String(255), nullable=False)
    mode = Column(String(50), nullable=False, default="agent")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    """Stores individual messages within a chat session."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String(50),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    sender = Column(String(20), nullable=False)  # 'user' or 'agent'
    content = Column(Text, nullable=False)
    sql_used = Column(Text, nullable=True)
    execution_time_ms = Column(Float, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    session = relationship("ChatSession", back_populates="messages")

