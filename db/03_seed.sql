INSERT IGNORE INTO ticket_statuses (code, label, sort_order) VALUES
    ('PENDING', 'Pending', 1),
    ('IN_PROGRESS', 'In Progress', 2),
    ('RESOLVED', 'Resolved', 3),
    ('CLOSED', 'Closed', 4);

INSERT IGNORE INTO ticket_status_transitions (from_status, to_status, requires_diagnosis, requires_comment) VALUES
    ('PENDING', 'IN_PROGRESS', FALSE, FALSE),
    ('PENDING', 'RESOLVED', TRUE, FALSE),
    ('IN_PROGRESS', 'PENDING', FALSE, TRUE),
    ('IN_PROGRESS', 'RESOLVED', TRUE, FALSE),
    ('RESOLVED', 'IN_PROGRESS', FALSE, TRUE),
    ('RESOLVED', 'CLOSED', FALSE, FALSE);

INSERT IGNORE INTO operators (full_name, email) VALUES
    ('Andrea Rojas', 'andrea.rojas@maintenance.local'),
    ('Luis Paredes', 'luis.paredes@maintenance.local'),
    ('Carla Mendoza', 'carla.mendoza@maintenance.local');

DROP PROCEDURE IF EXISTS sp_seed_demo_tickets;

DELIMITER $$

CREATE PROCEDURE sp_seed_demo_tickets()
BEGIN
    DECLARE v_andrea INT;
    DECLARE v_luis INT;
    DECLARE v_ticket INT;

    IF (SELECT COUNT(*) FROM tickets) = 0 THEN
        SELECT id INTO v_andrea FROM operators WHERE email = 'andrea.rojas@maintenance.local';
        SELECT id INTO v_luis FROM operators WHERE email = 'luis.paredes@maintenance.local';

        CALL sp_create_ticket('Air conditioning failure', 'SEDE-LIM', 'Server room temperature above 28 C.', 'Front desk', v_andrea);
        SET v_ticket = (SELECT MAX(id) FROM tickets);
        CALL sp_transition_ticket_status(v_ticket, 'IN_PROGRESS', NULL, NULL, 'Andrea Rojas');
        CALL sp_transition_ticket_status(v_ticket, 'RESOLVED', 'Compressor capacitor replaced.', NULL, 'Andrea Rojas');

        CALL sp_create_ticket('Card reader replacement', 'ATM-0210', 'Card reader rejects every card.', 'Branch manager', v_luis);
        SET v_ticket = (SELECT MAX(id) FROM tickets);
        CALL sp_transition_ticket_status(v_ticket, 'IN_PROGRESS', NULL, NULL, 'Luis Paredes');
        CALL sp_transition_ticket_status(v_ticket, 'RESOLVED', 'Faulty reader module swapped.', NULL, 'Luis Paredes');

        CALL sp_create_ticket('UPS alarm', 'SEDE-ARE', 'UPS beeping every few minutes.', 'Security guard', v_luis);
        SET v_ticket = (SELECT MAX(id) FROM tickets);
        CALL sp_transition_ticket_status(v_ticket, 'IN_PROGRESS', NULL, 'Battery bank under inspection.', 'Luis Paredes');

        CALL sp_create_ticket('ATM out of service', 'ATM-0451', 'Screen does not respond.', 'Customer service', NULL);
        CALL sp_create_ticket('Pipe leak on floor 2', 'SEDE-LIM', 'Water leak near the electrical room.', 'Facilities', NULL);
    END IF;
END$$

DELIMITER ;

CALL sp_seed_demo_tickets();

DROP PROCEDURE IF EXISTS sp_seed_demo_tickets;
