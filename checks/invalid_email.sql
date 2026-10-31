-- check: Invalid email format | severity: warning
SELECT id, email AS detail
FROM customers
WHERE TRIM(email) <> ''
  AND (email NOT LIKE '%_@_%._%'
    OR email LIKE '% %'
    OR email LIKE '%@%@%')
ORDER BY id;
