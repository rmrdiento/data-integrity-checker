-- check: Negative contract amount | severity: error
SELECT id, 'amount=' || amount AS detail
FROM contracts
WHERE amount < 0
ORDER BY id;
