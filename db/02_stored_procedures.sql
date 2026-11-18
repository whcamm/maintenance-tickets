DROP PROCEDURE IF EXISTS sp_create_ticket;
DROP PROCEDURE IF EXISTS sp_transition_ticket_status;
DROP PROCEDURE IF EXISTS sp_add_ticket_comment;
DROP PROCEDURE IF EXISTS sp_assign_ticket;

DELIMITER $$

CREATE PROCEDURE sp_create_ticket(
    IN p_title VARCHAR(120),
    IN p_asset_code VARCHAR(30),
    IN p_description TEXT,
    IN p_reported_by VARCHAR(100),
    IN p_assigned_operator_id INT
)
BEGIN
    DECLARE v_ticket_id INT;
    DECLARE v_operator_name VARCHAR(100) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF COALESCE(TRIM(p_title), '') = '' OR COALESCE(TRIM(p_asset_code), '') = '' OR COALESCE(TRIM(p_reported_by), '') = '' THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 5422, MESSAGE_TEXT = 'Title, asset code and reporter are required.';
    END IF;

    START TRANSACTION;

    IF p_assigned_operator_id IS NOT NULL THEN
        SELECT full_name INTO v_operator_name FROM operators WHERE id = p_assigned_operator_id;
        IF v_operator_name IS NULL THEN
            SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 5404, MESSAGE_TEXT = 'Operator not found.';
        END IF;
    END IF;

    INSERT INTO tickets (title, asset_code, description, status, reported_by, assigned_operator_id)
    VALUES (TRIM(p_title), UPPER(TRIM(p_asset_code)), NULLIF(TRIM(p_description), ''), 'PENDING', TRIM(p_reported_by), p_assigned_operator_id);

    SET v_ticket_id = LAST_INSERT_ID();

    INSERT INTO ticket_history (ticket_id, event_type, from_status, to_status, comment, actor)
    VALUES (v_ticket_id, 'CREATED', NULL, 'PENDING', 'Ticket reported.', TRIM(p_reported_by));

    IF v_operator_name IS NOT NULL THEN
        INSERT INTO ticket_history (ticket_id, event_type, comment, actor)
        VALUES (v_ticket_id, 'ASSIGNED', CONCAT('Assigned to ', v_operator_name, '.'), TRIM(p_reported_by));
    END IF;

    COMMIT;

    SELECT v_ticket_id AS ticket_id;
END$$

CREATE PROCEDURE sp_transition_ticket_status(
    IN p_ticket_id INT,
    IN p_to_status VARCHAR(20),
    IN p_diagnosis TEXT,
    IN p_comment TEXT,
    IN p_actor VARCHAR(100)
)
BEGIN
    DECLARE v_from_status VARCHAR(20) DEFAULT NULL;
    DECLARE v_current_diagnosis TEXT DEFAULT NULL;
    DECLARE v_rule_found TINYINT DEFAULT 0;
    DECLARE v_requires_diagnosis BOOLEAN DEFAULT FALSE;
    DECLARE v_requires_comment BOOLEAN DEFAULT FALSE;
    DECLARE v_diagnosis TEXT;
    DECLARE v_history_id BIGINT;
    DECLARE v_message VARCHAR(255);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF COALESCE(TRIM(p_actor), '') = '' THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 5422, MESSAGE_TEXT = 'Actor is required.';
    END IF;

    START TRANSACTION;

    SELECT status, diagnosis INTO v_from_status, v_current_diagnosis
    FROM tickets
    WHERE id = p_ticket_id
    FOR UPDATE;

    IF v_from_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 5404, MESSAGE_TEXT = 'Ticket not found.';
    END IF;

    SELECT 1, requires_diagnosis, requires_comment
    INTO v_rule_found, v_requires_diagnosis, v_requires_comment
    FROM ticket_status_transitions
    WHERE from_status = v_from_status AND to_status = p_to_status;

    IF v_rule_found = 0 THEN
        SET v_message = CONCAT('Transition from ', v_from_status, ' to ', COALESCE(p_to_status, 'NULL'), ' is not allowed.');
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 5409, MESSAGE_TEXT = v_message;
    END IF;

    SET v_diagnosis = COALESCE(NULLIF(TRIM(p_diagnosis), ''), v_current_diagnosis);

    IF v_requires_diagnosis AND COALESCE(TRIM(v_diagnosis), '') = '' THEN
        SET v_message = CONCAT('A diagnosis is required to move a ticket from ', v_from_status, ' to ', p_to_status, '.');
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 5422, MESSAGE_TEXT = v_message;
    END IF;

    IF v_requires_comment AND COALESCE(TRIM(p_comment), '') = '' THEN
        SET v_message = CONCAT('A comment is required to move a ticket from ', v_from_status, ' to ', p_to_status, '.');
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 5422, MESSAGE_TEXT = v_message;
    END IF;

    UPDATE tickets
    SET status = p_to_status,
        diagnosis = v_diagnosis
    WHERE id = p_ticket_id;

    INSERT INTO ticket_history (ticket_id, event_type, from_status, to_status, comment, actor)
    VALUES (p_ticket_id, 'STATUS_CHANGED', v_from_status, p_to_status, NULLIF(TRIM(p_comment), ''), TRIM(p_actor));

    SET v_history_id = LAST_INSERT_ID();

    COMMIT;

    SELECT v_history_id AS history_id, v_from_status AS from_status, p_to_status AS to_status;
END$$

CREATE PROCEDURE sp_add_ticket_comment(
    IN p_ticket_id INT,
    IN p_comment TEXT,
    IN p_actor VARCHAR(100)
)
BEGIN
    DECLARE v_status VARCHAR(20) DEFAULT NULL;
    DECLARE v_history_id BIGINT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF COALESCE(TRIM(p_comment), '') = '' OR COALESCE(TRIM(p_actor), '') = '' THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 5422, MESSAGE_TEXT = 'Comment and actor are required.';
    END IF;

    START TRANSACTION;

    SELECT status INTO v_status FROM tickets WHERE id = p_ticket_id FOR UPDATE;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 5404, MESSAGE_TEXT = 'Ticket not found.';
    END IF;

    IF v_status = 'CLOSED' THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 5410, MESSAGE_TEXT = 'Closed tickets cannot receive comments.';
    END IF;

    INSERT INTO ticket_history (ticket_id, event_type, comment, actor)
    VALUES (p_ticket_id, 'COMMENT', TRIM(p_comment), TRIM(p_actor));

    SET v_history_id = LAST_INSERT_ID();

    COMMIT;

    SELECT v_history_id AS history_id;
END$$

CREATE PROCEDURE sp_assign_ticket(
    IN p_ticket_id INT,
    IN p_operator_id INT,
    IN p_actor VARCHAR(100)
)
BEGIN
    DECLARE v_status VARCHAR(20) DEFAULT NULL;
    DECLARE v_current_operator_id INT DEFAULT NULL;
    DECLARE v_operator_name VARCHAR(100) DEFAULT NULL;
    DECLARE v_history_id BIGINT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF COALESCE(TRIM(p_actor), '') = '' THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 5422, MESSAGE_TEXT = 'Actor is required.';
    END IF;

    START TRANSACTION;

    SELECT status, assigned_operator_id INTO v_status, v_current_operator_id
    FROM tickets
    WHERE id = p_ticket_id
    FOR UPDATE;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 5404, MESSAGE_TEXT = 'Ticket not found.';
    END IF;

    IF v_status = 'CLOSED' THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 5410, MESSAGE_TEXT = 'Closed tickets cannot be reassigned.';
    END IF;

    SELECT full_name INTO v_operator_name FROM operators WHERE id = p_operator_id;

    IF v_operator_name IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 5404, MESSAGE_TEXT = 'Operator not found.';
    END IF;

    IF v_current_operator_id <=> p_operator_id THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 5410, MESSAGE_TEXT = 'Ticket is already assigned to this operator.';
    END IF;

    UPDATE tickets SET assigned_operator_id = p_operator_id WHERE id = p_ticket_id;

    INSERT INTO ticket_history (ticket_id, event_type, comment, actor)
    VALUES (p_ticket_id, 'ASSIGNED', CONCAT('Assigned to ', v_operator_name, '.'), TRIM(p_actor));

    SET v_history_id = LAST_INSERT_ID();

    COMMIT;

    SELECT v_history_id AS history_id;
END$$

DELIMITER ;
