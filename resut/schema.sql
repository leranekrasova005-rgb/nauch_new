-- Экспорт из SQLite: db.sqlite3
-- Дата: 2026-05-19 14:34:28
-- Для импорта в PostgreSQL

CREATE TABLE IF NOT EXISTS django_migrations (
    id INTEGER,
    app VARCHAR,
    name VARCHAR,
    applied TIMESTAMP
);

CREATE TABLE IF NOT EXISTS django_content_type (
    id INTEGER,
    app_label VARCHAR,
    model VARCHAR
);

CREATE TABLE IF NOT EXISTS auth_group_permissions (
    id INTEGER,
    group_id INTEGER,
    permission_id INTEGER
);

CREATE TABLE IF NOT EXISTS auth_permission (
    id INTEGER,
    content_type_id INTEGER,
    codename VARCHAR,
    name VARCHAR
);

CREATE TABLE IF NOT EXISTS auth_group (
    id INTEGER,
    name VARCHAR
);

CREATE TABLE IF NOT EXISTS users_user_groups (
    id INTEGER,
    user_id TEXT,
    group_id INTEGER
);

CREATE TABLE IF NOT EXISTS users_user_user_permissions (
    id INTEGER,
    user_id TEXT,
    permission_id INTEGER
);

CREATE TABLE IF NOT EXISTS django_admin_log (
    id INTEGER,
    object_id TEXT NOT NULL,
    object_repr VARCHAR,
    action_flag TEXT,
    change_message TEXT,
    content_type_id INTEGER NOT NULL,
    user_id TEXT,
    action_time TIMESTAMP
);

CREATE TABLE IF NOT EXISTS core_activitylog (
    id INTEGER,
    action VARCHAR,
    details TEXT,
    ip_address CHAR NOT NULL,
    timestamp TIMESTAMP,
    user_id TEXT NOT NULL,
    publication_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS core_deleterequest (
    id INTEGER,
    reason TEXT,
    status VARCHAR,
    reviewed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP,
    requester_id TEXT NOT NULL,
    reviewed_by_id TEXT NOT NULL,
    publication_id TEXT
);

CREATE TABLE IF NOT EXISTS core_publisher (
    id INTEGER,
    city VARCHAR,
    country VARCHAR,
    website VARCHAR,
    email VARCHAR,
    phone VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    name TEXT
);

CREATE TABLE IF NOT EXISTS core_publication (
    id INTEGER,
    title TEXT,
    author TEXT,
    circulation TEXT,
    head VARCHAR,
    executors TEXT,
    location VARCHAR,
    event_name VARCHAR,
    funding_source VARCHAR,
    volume VARCHAR,
    note TEXT,
    students_names TEXT,
    year INTEGER,
    students_count TEXT,
    pages_count TEXT,
    result VARCHAR,
    department VARCHAR,
    event_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    status VARCHAR,
    owner_id TEXT NOT NULL,
    keywords VARCHAR,
    moderated_at TIMESTAMP NOT NULL,
    moderated_by_id TEXT NOT NULL,
    moderation_comment TEXT,
    moderation_status VARCHAR,
    citation_db VARCHAR,
    author_status VARCHAR,
    doi VARCHAR,
    edn_code VARCHAR,
    elibrary_id VARCHAR,
    printed_sheets TEXT,
    publication_scope VARCHAR,
    publication_type VARCHAR,
    reporting_period VARCHAR,
    reporting_year VARCHAR,
    publisher_id TEXT NOT NULL,
    is_archived TEXT,
    entry_month INTEGER
);

CREATE TABLE IF NOT EXISTS django_session (
    session_key VARCHAR,
    session_data TEXT,
    expire_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users_department (
    id INTEGER,
    code VARCHAR,
    full_name VARCHAR,
    short_name VARCHAR,
    description TEXT,
    email VARCHAR,
    phone VARCHAR,
    achievements TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    head_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users_department_staff (
    id INTEGER,
    department_id TEXT,
    user_id TEXT
);

CREATE TABLE IF NOT EXISTS users_user (
    id INTEGER,
    password VARCHAR,
    last_login TIMESTAMP NOT NULL,
    is_superuser TEXT,
    username VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    email VARCHAR,
    is_staff TEXT,
    is_active TEXT,
    date_joined TIMESTAMP,
    phone VARCHAR,
    department VARCHAR,
    role VARCHAR
);

