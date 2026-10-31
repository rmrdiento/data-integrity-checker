-- check: Duplicate contract numbers | severity: error
SELECT id, contract_number AS detail
FROM (
    SELECT id, contract_number,
           ROW_NUMBER() OVER (PARTITION BY LOWER(TRIM(contract_number)) ORDER BY id) AS rn
    FROM contracts
    WHERE TRIM(contract_number) <> ''
) numbered
WHERE rn > 1
ORDER BY id;
