CREATE TABLE IF NOT EXISTS operators (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT uq_operators_email UNIQUE (email)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS ticket_statuses (
    code VARCHAR(20) PRIMARY KEY,
    label VARCHAR(50) NOT NULL,
    sort_order TINYINT NOT NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS ticket_status_transitions (
    from_status VARCHAR(20) NOT NULL,
    to_status VARCHAR(20) NOT NULL,
    requires_diagnosis BOOLEAN NOT NULL DEFAULT FALSE,
    requires_comment BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (from_status, to_status),
    CONSTRAINT fk_transitions_from_status FOREIGN KEY (from_status) REFERENCES ticket_statuses (code),
    CONSTRAINT fk_transitions_to_status FOREIGN KEY (to_status) REFERENCES ticket_statuses (code),
    CONSTRAINT chk_transitions_distinct CHECK (from_status <> to_status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(120) NOT NULL,
    asset_code VARCHAR(30) NOT NULL,
    description TEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    diagnosis TEXT NULL,
    reported_by VARCHAR(100) NOT NULL,
    assigned_operator_id INT NULL,
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    CONSTRAINT fk_tickets_status FOREIGN KEY (status) REFERENCES ticket_statuses (code),
    CONSTRAINT fk_tickets_operator FOREIGN KEY (assigned_operator_id) REFERENCES operators (id) ON DELETE SET NULL,
    CONSTRAINT chk_tickets_title CHECK (CHAR_LENGTH(TRIM(title)) > 0),
    CONSTRAINT chk_tickets_asset_code CHECK (CHAR_LENGTH(TRIM(asset_code)) > 0),
    INDEX ix_tickets_status (status),
    INDEX ix_tickets_created_at (created_at),
    INDEX ix_tickets_operator (assigned_operator_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 AUTO_INCREMENT = 1028;

CREATE TABLE IF NOT EXISTS ticket_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    event_type ENUM ('CREATED', 'STATUS_CHANGED', 'COMMENT', 'ASSIGNED') NOT NULL,
    from_status VARCHAR(20) NULL,
    to_status VARCHAR(20) NULL,
    comment TEXT NULL,
    actor VARCHAR(100) NOT NULL,
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT fk_history_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (id) ON DELETE RESTRICT,
    CONSTRAINT fk_history_from_status FOREIGN KEY (from_status) REFERENCES ticket_statuses (code),
    CONSTRAINT fk_history_to_status FOREIGN KEY (to_status) REFERENCES ticket_statuses (code),
    INDEX ix_history_ticket_created (ticket_id, created_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS notifications (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    history_id BIGINT NOT NULL,
    recipient VARCHAR(150) NOT NULL,
    channel VARCHAR(30) NOT NULL DEFAULT 'EMAIL_SIMULATED',
    message VARCHAR(255) NOT NULL,
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT fk_notifications_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (id) ON DELETE RESTRICT,
    CONSTRAINT fk_notifications_history FOREIGN KEY (history_id) REFERENCES ticket_history (id) ON DELETE RESTRICT,
    INDEX ix_notifications_created (created_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;
