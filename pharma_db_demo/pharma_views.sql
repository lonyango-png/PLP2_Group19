-- Status of every batch. A batch expiring today is still usable.
CREATE OR REPLACE VIEW v_batch_status AS
SELECT b.batch_id,
       b.medicine_id,
       m.medicine_code,
       m.name,
       m.strength,
       b.batch_number,
       b.expiry_date,
       b.quantity_on_hand,
       DATEDIFF(b.expiry_date, CURDATE()) AS days_left,
       CASE
           WHEN b.expiry_date < CURDATE()                                  THEN 'EXPIRED'
           WHEN b.expiry_date <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)      THEN 'NEARING_EXPIRY'
           ELSE 'OK'
       END AS status
FROM batches AS b
JOIN medicines AS m ON m.medicine_id = b.medicine_id;

CREATE OR REPLACE VIEW v_sellable_batches AS
SELECT *
FROM v_batch_status
WHERE status IN ('OK', 'NEARING_EXPIRY')
  AND quantity_on_hand > 0;

CREATE OR REPLACE VIEW v_medicine_stock AS
SELECT m.medicine_id,
       m.medicine_code,
       m.name,
       m.strength,
       m.reorder_level,
       COALESCE(SUM(s.quantity_on_hand), 0) AS usable_stock
FROM medicines AS m
LEFT JOIN v_sellable_batches AS s ON s.medicine_id = m.medicine_id
WHERE m.is_active = TRUE
GROUP BY m.medicine_id, m.medicine_code, m.name, m.strength, m.reorder_level;

CREATE OR REPLACE VIEW v_low_stock AS
SELECT *
FROM v_medicine_stock
WHERE usable_stock < reorder_level;

CREATE OR REPLACE VIEW v_expiring_soon AS
SELECT *
FROM v_batch_status
WHERE status = 'NEARING_EXPIRY'
  AND quantity_on_hand > 0;

CREATE OR REPLACE VIEW v_expired_stock AS
SELECT *
FROM v_batch_status
WHERE status = 'EXPIRED'
  AND quantity_on_hand > 0;

CREATE OR REPLACE VIEW v_sale_history AS
SELECT s.sale_id,
       s.sold_at,
       s.customer_name,
       m.name       AS medicine,
       m.strength,
       b.batch_number,
       si.quantity,
       si.unit_price,
       si.quantity * si.unit_price AS line_total
FROM sales AS s
JOIN sale_items AS si ON si.sale_id = s.sale_id
JOIN batches    AS b  ON b.batch_id = si.batch_id
JOIN medicines  AS m  ON m.medicine_id = b.medicine_id;