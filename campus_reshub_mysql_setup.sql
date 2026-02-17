-- ============================================================
-- Campus Resource Management System
-- MySQL Database Setup Script
-- ============================================================
-- Run this in MySQL Workbench after connecting to Azure MySQL
-- ============================================================

-- Step 1: Create Database
CREATE DATABASE IF NOT EXISTS campus_reshub_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Step 2: Use the Database
USE campus_reshub_db;

-- ============================================================
-- Module 1: User Management
-- ============================================================
CREATE TABLE users (
    id          BIGINT          AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(150)    NOT NULL,
    email       VARCHAR(254)    NOT NULL UNIQUE,
    phone       VARCHAR(15)     DEFAULT NULL,
    role        ENUM('STUDENT', 'STAFF')            NOT NULL DEFAULT 'STUDENT',
    status      ENUM('ACTIVE', 'INACTIVE')          NOT NULL DEFAULT 'ACTIVE',
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Module 2: Resource Management
-- ============================================================
CREATE TABLE resources (
    id          BIGINT          AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(200)    NOT NULL,
    type        ENUM('LAB', 'CLASSROOM', 'EVENT_HALL') NOT NULL,
    capacity    INT UNSIGNED    NOT NULL,
    status      ENUM('AVAILABLE', 'UNAVAILABLE')       NOT NULL DEFAULT 'AVAILABLE'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Module 3: Booking Module
-- ============================================================
CREATE TABLE bookings (
    id              BIGINT      AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT      NOT NULL,
    resource_id     BIGINT      NOT NULL,
    booking_date    DATE        NOT NULL,
    time_slot       VARCHAR(50) NOT NULL,
    status          ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'PENDING',

    -- Foreign Keys
    CONSTRAINT fk_booking_user
        FOREIGN KEY (user_id)     REFERENCES users(id)     ON DELETE CASCADE,
    CONSTRAINT fk_booking_resource
        FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE,

    -- Prevent double-booking: same resource + same date + same time slot
    CONSTRAINT uq_no_double_booking
        UNIQUE (resource_id, booking_date, time_slot)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Verify: Show all tables
-- ============================================================
SHOW TABLES;

-- ============================================================
-- Verify: Show columns of each table
-- ============================================================
DESCRIBE users;
DESCRIBE resources;
DESCRIBE bookings;
