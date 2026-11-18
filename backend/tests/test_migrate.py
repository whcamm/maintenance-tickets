from app.db.migrate import split_statements


def test_split_statements_handles_custom_delimiters():
    script = """
-- comment
DROP PROCEDURE IF EXISTS sp_demo;

DELIMITER $$

CREATE PROCEDURE sp_demo()
BEGIN
    SELECT 1;
    SELECT 2;
END$$

DELIMITER ;

CALL sp_demo();
"""

    statements = split_statements(script)

    assert statements[0] == "DROP PROCEDURE IF EXISTS sp_demo"
    assert statements[1].startswith("CREATE PROCEDURE sp_demo()")
    assert statements[1].endswith("END")
    assert "SELECT 2;" in statements[1]
    assert statements[2] == "CALL sp_demo()"
