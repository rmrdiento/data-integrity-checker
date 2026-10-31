-- check: Invalid phone format (expected +<11 digits>) | severity: warning
SELECT id, phone AS detail
FROM customers
WHERE TRIM(phone) <> ''
  AND (phone NOT LIKE '+___________'
    OR REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
         phone, '0', ''), '1', ''), '2', ''), '3', ''), '4', ''), '5', ''), '6', ''), '7', ''), '8', ''), '9', '') <> '+')
ORDER BY id;
