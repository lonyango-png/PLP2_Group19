-- All medicines with usable stock
SELECT * FROM v_medicine_stock ORDER BY name;

-- Search by part of the name or by exact code
-- (the default collation is case-insensitive)
SELECT medicine_id, medicine_code, name, strength
FROM medicines
WHERE is_active = TRUE
  AND (name LIKE '%para%' OR medicine_code = 'PAR500')
ORDER BY name;

-- Low-stock medicines
SELECT name, strength, usable_stock, reorder_level
FROM v_low_stock
ORDER BY usable_stock;

-- Batches expiring within 30 days
SELECT name, batch_number, expiry_date, days_left, quantity_on_hand
FROM v_expiring_soon
ORDER BY expiry_date;

-- Expired stock to remove from shelves
SELECT name, batch_number, expiry_date, quantity_on_hand
FROM v_expired_stock;

-- Choose a batch to sell from: earliest expiry first (FEFO).
-- Lock the row so two sales cannot take the same stock.
START TRANSACTION;
SELECT batch_id, quantity_on_hand, expiry_date
FROM batches
WHERE medicine_id = 1
  AND expiry_date >= CURDATE()
  AND quantity_on_hand > 0
ORDER BY expiry_date, batch_id
LIMIT 1
FOR UPDATE;
COMMIT;

-- Record a sale: all statements succeed or none do
START TRANSACTION;
INSERT INTO sales (customer_name) VALUES ('Walk-in');
SET @sale_id = LAST_INSERT_ID();
SELECT m.selling_price INTO @price
FROM batches AS b
JOIN medicines AS m ON m.medicine_id = b.medicine_id
WHERE b.batch_id = 1
FOR UPDATE;
INSERT INTO sale_items (sale_id, batch_id, quantity, unit_price)
VALUES (@sale_id, 1, 3, @price);
COMMIT;

-- Write off an expired batch
INSERT INTO stock_adjustments (batch_id, quantity_change, reason, note)
VALUES (3, -60, 'EXPIRED_WRITE_OFF', 'Destroyed under pharmacy procedure');

-- Sales history for the last seven days
SELECT sale_id, sold_at, customer_name, medicine, strength,
       batch_number, quantity, unit_price, line_total
FROM v_sale_history
WHERE sold_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
ORDER BY sold_at DESC;

-- Total per sale (calculated, not stored)
SELECT sale_id, sold_at, SUM(line_total) AS sale_total
FROM v_sale_history
GROUP BY sale_id, sold_at
ORDER BY sold_at DESC;

-- Integrity audit: stored stock must equal received − sold + adjusted.
-- This query should return no rows.
SELECT *
FROM (
    SELECT b.batch_id,
           b.quantity_on_hand AS recorded,
           b.quantity_received
             - COALESCE((SELECT SUM(si.quantity)
                         FROM sale_items AS si
                         WHERE si.batch_id = b.batch_id), 0)
             + COALESCE((SELECT SUM(sa.quantity_change)
                         FROM stock_adjustments AS sa
                         WHERE sa.batch_id = b.batch_id), 0) AS expected
    FROM batches AS b
) AS audit
WHERE recorded <> expected;