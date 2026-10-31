-- check: Customers with missing required fields | severity: error
SELECT id,
       TRIM(CASE WHEN COALESCE(TRIM(full_name), '') = '' THEN 'full_name ' ELSE '' END
         || CASE WHEN COALESCE(TRIM(email), '') = '' THEN 'email ' ELSE '' END
         || CASE WHEN COALESCE(TRIM(phone), '') = '' THEN 'phone' ELSE '' END) AS detail
FROM customers
WHERE COALESCE(TRIM(full_name), '') = ''
   OR COALESCE(TRIM(email), '') = ''
   OR COALESCE(TRIM(phone), '') = ''
ORDER BY id;
