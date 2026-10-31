-- check: Invalid date format (expected YYYY-MM-DD) | severity: error
WITH dates AS (
    SELECT id, 'start_date' AS field, start_date AS val FROM contracts
    UNION ALL
    SELECT id, 'end_date', end_date FROM contracts
)
SELECT id, field || '=' || val AS detail
FROM dates
WHERE TRIM(val) <> ''
  AND (val NOT LIKE '____-__-__'
    OR REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
         val, '0', ''), '1', ''), '2', ''), '3', ''), '4', ''), '5', ''), '6', ''), '7', ''), '8', ''), '9', '') <> '--'
    OR SUBSTR(val, 6, 2) NOT BETWEEN '01' AND '12'
    OR SUBSTR(val, 9, 2) NOT BETWEEN '01' AND '31')
ORDER BY id, field;
