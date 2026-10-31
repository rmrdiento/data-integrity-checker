-- check: End date earlier than start date | severity: error
SELECT id, 'start=' || start_date || ' end=' || end_date AS detail
FROM contracts
WHERE start_date LIKE '____-__-__'
  AND end_date LIKE '____-__-__'
  AND end_date < start_date
ORDER BY id;
