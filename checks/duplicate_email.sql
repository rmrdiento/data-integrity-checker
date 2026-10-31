-- check: Duplicate emails | severity: error
SELECT id, email AS detail
FROM (
    SELECT id, email,
           ROW_NUMBER() OVER (PARTITION BY LOWER(TRIM(email)) ORDER BY id) AS rn
    FROM customers
    WHERE TRIM(email) <> ''
) numbered
WHERE rn > 1
ORDER BY id;
