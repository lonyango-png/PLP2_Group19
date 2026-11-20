DELIMITER $$

-- 1. Before a sale line is saved: the batch must exist, must not be expired,
--    and must have enough stock.
CREATE TRIGGER trg_sale_items_guard
BEFORE INSERT ON sale_items
FOR EACH ROW
BEGIN
    DECLARE v_expiry DATE;
    DECLARE v_on_hand INT;

    IF NOT EXISTS (SELECT 1 FROM batches WHERE batch_id = NEW.batch_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Batch does not exist';
    END IF;

    SELECT expiry_date, quantity_on_hand
      INTO v_expiry, v_on_hand
      FROM batches
     WHERE batch_id = NEW.batch_id;

    IF v_expiry < CURDATE() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot sell an expired batch';
    END IF;

    IF v_on_hand < NEW.quantity THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Not enough stock in this batch';
    END IF;
END$$

-- 2. After a sale line is saved: reduce the batch. The CHECK constraint on
--    batches is the final guard against negative stock.
CREATE TRIGGER trg_sale_items_apply
AFTER INSERT ON sale_items
FOR EACH ROW
UPDATE batches
   SET quantity_on_hand = quantity_on_hand - NEW.quantity
 WHERE batch_id = NEW.batch_id$$

-- 3. After a stock adjustment: apply the change to its batch.
CREATE TRIGGER trg_adjustments_apply
AFTER INSERT ON stock_adjustments
FOR EACH ROW
UPDATE batches
   SET quantity_on_hand = quantity_on_hand + NEW.quantity_change
 WHERE batch_id = NEW.batch_id$$

-- 4. Sales are permanent.
CREATE TRIGGER trg_sale_items_no_update
BEFORE UPDATE ON sale_items
FOR EACH ROW
SIGNAL SQLSTATE '45000'
SET MESSAGE_TEXT = 'Sales are permanent; record a stock adjustment instead'$$

CREATE TRIGGER trg_sale_items_no_delete
BEFORE DELETE ON sale_items
FOR EACH ROW
SIGNAL SQLSTATE '45000'
SET MESSAGE_TEXT = 'Sales cannot be deleted'$$

DELIMITER ;