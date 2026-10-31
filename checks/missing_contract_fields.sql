-- check: Contracts with missing required fields | severity: error
SELECT id,
       TRIM(CASE WHEN COALESCE(TRIM(contract_number), '') = '' THEN 'contract_number ' ELSE '' END
         || CASE WHEN customer_id IS NULL THEN 'customer_id ' ELSE '' END
         || CASE WHEN COALESCE(TRIM(start_date), '') = '' THEN 'start_date ' ELSE '' END
         || CASE WHEN amount IS NULL THEN 'amount' ELSE '' END) AS detail
FROM contracts
WHERE COALESCE(TRIM(contract_number), '') = ''
   OR customer_id IS NULL
   OR COALESCE(TRIM(start_date), '') = ''
   OR amount IS NULL
ORDER BY id;
