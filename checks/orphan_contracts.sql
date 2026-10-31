-- check: Contracts referencing a missing customer | severity: error
SELECT c.id, 'customer_id=' || c.customer_id AS detail
FROM contracts c
LEFT JOIN customers u ON u.id = c.customer_id
WHERE c.customer_id IS NOT NULL
  AND u.id IS NULL
ORDER BY c.id;
