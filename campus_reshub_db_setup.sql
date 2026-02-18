-- ============================================================================
-- Campus Resource Management System (Campus ResHub)
-- Complete MySQL Database Setup Script
-- ============================================================================
-- IMPORTANT NOTE:
-- This script is for REFERENCE and MANUAL VERIFICATION purposes.
-- The RECOMMENDED approach is to let Django's makemigrations/migrate handle
-- table creation. See the note at the bottom of this script.
-- ============================================================================

-- Step 1: Create Database
CREATE DATABASE IF NOT EXISTS campus_reshub
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE campus_reshub;

-- ============================================================================
-- Table 1: users
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(150) NOT NULL,
    phone VARCHAR(20) DEFAULT NULL,
    password VARCHAR(128) NOT NULL,
    role ENUM('STUDENT', 'FACULTY', 'STAFF', 'ADMIN') NOT NULL DEFAULT 'STUDENT',
    account_status ENUM('ACTIVE', 'INACTIVE') NOT NULL DEFAULT 'ACTIVE',
    approval_status ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
    rejection_reason TEXT DEFAULT NULL,
    is_email_verified TINYINT(1) NOT NULL DEFAULT 0,
    verification_token VARCHAR(255) DEFAULT NULL,
    verified_at DATETIME DEFAULT NULL,
    reset_token VARCHAR(255) DEFAULT NULL,
    reset_token_expiry DATETIME DEFAULT NULL,
    is_staff TINYINT(1) NOT NULL DEFAULT 0,
    is_superuser TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    is_deleted TINYINT(1) NOT NULL DEFAULT 0,
    deleted_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login DATETIME DEFAULT NULL,

    UNIQUE INDEX idx_users_email (email),
    INDEX idx_users_role (role),
    INDEX idx_users_account_status (account_status),
    INDEX idx_users_approval_status (approval_status),
    INDEX idx_users_account_approval (account_status, approval_status),
    INDEX idx_users_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Table 2: role_change_requests
-- ============================================================================
CREATE TABLE IF NOT EXISTS role_change_requests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    current_role ENUM('STUDENT', 'FACULTY', 'STAFF', 'ADMIN') NOT NULL,
    requested_role ENUM('STUDENT', 'FACULTY', 'STAFF', 'ADMIN') NOT NULL,
    status ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
    rejection_reason TEXT DEFAULT NULL,
    reviewed_by_id BIGINT DEFAULT NULL,
    reviewed_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_rcr_user_id (user_id),
    INDEX idx_rcr_status (status),
    INDEX idx_rcr_reviewed_by (reviewed_by_id),

    CONSTRAINT fk_rcr_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_rcr_reviewer FOREIGN KEY (reviewed_by_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Table 3: resources
-- ============================================================================
CREATE TABLE IF NOT EXISTS resources (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    type ENUM('LAB', 'CLASSROOM', 'EVENT_HALL') NOT NULL,
    capacity INT NOT NULL DEFAULT 0,
    total_quantity INT NOT NULL DEFAULT 1,
    location VARCHAR(255) DEFAULT NULL,
    description TEXT DEFAULT NULL,
    resource_status ENUM('AVAILABLE', 'UNAVAILABLE') NOT NULL DEFAULT 'AVAILABLE',
    approval_type ENUM('AUTO_APPROVE', 'STAFF_APPROVE', 'ADMIN_APPROVE') NOT NULL DEFAULT 'AUTO_APPROVE',
    managed_by_id BIGINT NOT NULL,
    is_deleted TINYINT(1) NOT NULL DEFAULT 0,
    deleted_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_resources_type (type),
    INDEX idx_resources_status (resource_status),
    INDEX idx_resources_managed_by (managed_by_id),
    INDEX idx_resources_is_deleted (is_deleted),
    FULLTEXT INDEX idx_resources_search (name, location),

    CONSTRAINT fk_resources_managed_by FOREIGN KEY (managed_by_id) REFERENCES users (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Table 4: resource_addition_requests
-- ============================================================================
CREATE TABLE IF NOT EXISTS resource_addition_requests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    requested_by_id BIGINT NOT NULL,
    proposed_name VARCHAR(200) NOT NULL,
    proposed_type ENUM('LAB', 'CLASSROOM', 'EVENT_HALL') NOT NULL,
    proposed_capacity INT NOT NULL DEFAULT 0,
    proposed_total_quantity INT NOT NULL DEFAULT 1,
    proposed_location VARCHAR(255) DEFAULT NULL,
    proposed_description TEXT DEFAULT NULL,
    proposed_approval_type ENUM('AUTO_APPROVE', 'STAFF_APPROVE', 'ADMIN_APPROVE') NOT NULL DEFAULT 'AUTO_APPROVE',
    justification TEXT NOT NULL,
    status ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
    rejection_reason TEXT DEFAULT NULL,
    reviewed_by_id BIGINT DEFAULT NULL,
    reviewed_at DATETIME DEFAULT NULL,
    created_resource_id BIGINT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_rar_requested_by (requested_by_id),
    INDEX idx_rar_status (status),
    INDEX idx_rar_reviewed_by (reviewed_by_id),
    INDEX idx_rar_created_resource (created_resource_id),

    CONSTRAINT fk_rar_requested_by FOREIGN KEY (requested_by_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_rar_reviewer FOREIGN KEY (reviewed_by_id) REFERENCES users (id) ON DELETE SET NULL,
    CONSTRAINT fk_rar_created_resource FOREIGN KEY (created_resource_id) REFERENCES resources (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Table 5: resource_weekly_schedules
-- ============================================================================
CREATE TABLE IF NOT EXISTS resource_weekly_schedules (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    resource_id BIGINT NOT NULL,
    day_of_week SMALLINT NOT NULL COMMENT '0=Monday, 1=Tuesday, ..., 6=Sunday',
    start_time TIME NOT NULL DEFAULT '08:00:00',
    end_time TIME NOT NULL DEFAULT '19:00:00',
    is_working TINYINT(1) NOT NULL DEFAULT 1,

    UNIQUE INDEX idx_rws_resource_day (resource_id, day_of_week),
    INDEX idx_rws_resource_id (resource_id),

    CONSTRAINT fk_rws_resource FOREIGN KEY (resource_id) REFERENCES resources (id) ON DELETE CASCADE,
    CONSTRAINT chk_rws_day_range CHECK (day_of_week >= 0 AND day_of_week <= 6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Table 6: calendar_overrides
-- ============================================================================
CREATE TABLE IF NOT EXISTS calendar_overrides (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    override_date DATE NOT NULL,
    override_type ENUM('HOLIDAY', 'WORKING_DAY') NOT NULL,
    description VARCHAR(255) DEFAULT NULL,
    created_by_id BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE INDEX idx_co_override_date (override_date),
    INDEX idx_co_created_by (created_by_id),

    CONSTRAINT fk_co_created_by FOREIGN KEY (created_by_id) REFERENCES users (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Table 7: bookings
-- ============================================================================
CREATE TABLE IF NOT EXISTS bookings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    resource_id BIGINT NOT NULL,
    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    quantity_requested INT NOT NULL DEFAULT 1,
    status ENUM('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED') NOT NULL DEFAULT 'PENDING',
    is_special_request TINYINT(1) NOT NULL DEFAULT 0,
    special_request_reason TEXT DEFAULT NULL,
    cancellation_reason TEXT DEFAULT NULL,
    cancelled_by_id BIGINT DEFAULT NULL,
    cancelled_at DATETIME DEFAULT NULL,
    approved_by_id BIGINT DEFAULT NULL,
    approved_at DATETIME DEFAULT NULL,
    rejected_by_id BIGINT DEFAULT NULL,
    rejection_reason TEXT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_bookings_user_id (user_id),
    INDEX idx_bookings_resource_id (resource_id),
    INDEX idx_bookings_status (status),
    INDEX idx_bookings_date (booking_date),
    INDEX idx_bookings_availability (resource_id, booking_date, start_time, status),
    INDEX idx_bookings_cancelled_by (cancelled_by_id),
    INDEX idx_bookings_approved_by (approved_by_id),
    INDEX idx_bookings_rejected_by (rejected_by_id),

    CONSTRAINT fk_bookings_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_bookings_resource FOREIGN KEY (resource_id) REFERENCES resources (id) ON DELETE CASCADE,
    CONSTRAINT fk_bookings_cancelled_by FOREIGN KEY (cancelled_by_id) REFERENCES users (id) ON DELETE SET NULL,
    CONSTRAINT fk_bookings_approved_by FOREIGN KEY (approved_by_id) REFERENCES users (id) ON DELETE SET NULL,
    CONSTRAINT fk_bookings_rejected_by FOREIGN KEY (rejected_by_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Table 8: user_notifications
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_notifications (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    message_type ENUM(
        'BOOKING_APPROVED',
        'BOOKING_REJECTED',
        'BOOKING_CANCELLED',
        'BOOKING_AUTO_CANCELLED',
        'REGISTRATION_APPROVED',
        'REGISTRATION_REJECTED',
        'ROLE_CHANGE_APPROVED',
        'ROLE_CHANGE_REJECTED',
        'GENERAL'
    ) NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    related_entity_type VARCHAR(50) DEFAULT NULL,
    related_entity_id BIGINT DEFAULT NULL,
    is_read TINYINT(1) NOT NULL DEFAULT 0,
    is_email_sent TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_un_user_read_created (user_id, is_read, created_at DESC),
    INDEX idx_un_user_id (user_id),
    INDEX idx_un_message_type (message_type),

    CONSTRAINT fk_un_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Table 9: audit_logs (APPEND-ONLY: no UPDATE or DELETE permitted)
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    actor_id BIGINT DEFAULT NULL,
    actor_email VARCHAR(255) DEFAULT NULL,
    action VARCHAR(100) NOT NULL,
    target_entity_type VARCHAR(50) NOT NULL,
    target_entity_id BIGINT DEFAULT NULL,
    previous_state JSON DEFAULT NULL,
    new_state JSON DEFAULT NULL,
    metadata JSON DEFAULT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_al_action (action),
    INDEX idx_al_actor_id (actor_id),
    INDEX idx_al_target_entity_type (target_entity_type),
    INDEX idx_al_timestamp (timestamp),
    INDEX idx_al_target (target_entity_type, target_entity_id),
    INDEX idx_al_actor_email (actor_email),

    CONSTRAINT fk_al_actor FOREIGN KEY (actor_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- NOTE ON simplejwt token_blacklist TABLES:
-- The tables for djangorestframework-simplejwt token blacklist
-- (token_blacklist_outstandingtoken, token_blacklist_blacklistedtoken)
-- are AUTOMATICALLY created by Django migrations when you run:
--     uv run python manage.py migrate
-- after adding 'rest_framework_simplejwt.token_blacklist' to INSTALLED_APPS.
-- Do NOT create them manually here.
-- ============================================================================

-- ============================================================================
-- RECOMMENDATION: DJANGO MIGRATIONS vs MANUAL SQL
-- ============================================================================
-- RECOMMENDED APPROACH: Use Django migrations (NOT this script directly).
--
-- Reasons:
-- 1. Django tracks migration state in django_migrations table. Running raw SQL
--    bypasses this tracking, causing makemigrations to generate duplicate
--    table-creation migrations that will fail.
-- 2. Django auto-creates its internal tables (auth_user groups, sessions,
--    content types, admin log, simplejwt blacklist) during migrate. You need
--    those tables and they must be migration-consistent.
-- 3. Django ORM maps Python model field types to DB column types. Letting
--    Django create tables ensures exact type matching (e.g., Django BooleanField
--    maps to TINYINT(1), Django JSONField maps to JSON, etc.).
--
-- HOW TO USE THIS SCRIPT:
-- Option A (recommended): Use it as a REFERENCE while writing your Django
--   models. After defining all models, run:
--     uv run python manage.py makemigrations
--     uv run python manage.py migrate
--   Then compare the actual DB schema to this script for verification.
--
-- Option B (manual pre-creation): If you must pre-create the database:
--   1. Run ONLY the CREATE DATABASE block at the top.
--   2. Let Django handle all table creation via migrate.
--   3. Use this script to VERIFY the final schema matches expectations.
--
-- Option C (full manual): Run this entire script first, then use
--   --fake-initial on Django migrate to skip table creation:
--     uv run python manage.py migrate --fake-initial
--   WARNING: This is fragile. Any mismatch between this script and Django's
--   model definitions will cause runtime errors. Not recommended.
-- ============================================================================
