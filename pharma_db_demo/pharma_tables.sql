-- =====================================================
-- Pharma: Medicine Stock & Expiry Tracker (MySQL 8.0.16+)
-- Run with: mysql -u root -p < pharma_mysql.sql
-- =====================================================

-- Optional reset. WARNING: this deletes all data.
DROP DATABASE IF EXISTS pharma;

CREATE DATABASE pharma
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
USE pharma;

CREATE TABLE medicines (
    medicine_id    INT AUTO_INCREMENT PRIMARY KEY,
    medicine_code  VARCHAR(30)  NOT NULL UNIQUE,
    name           VARCHAR(100) NOT NULL,
    strength       VARCHAR(30)  NOT NULL DEFAULT '',
    dosage_form    ENUM('TABLET','CAPSULE','SYRUP','INJECTION','CREAM','SACHET','OTHER')
                   NOT NULL DEFAULT 'OTHER',
    selling_price  INT          NOT NULL,
    reorder_level  INT          NOT NULL DEFAULT 10,
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_medicine_name_strength UNIQUE (name, strength),
    CONSTRAINT chk_medicine_code  CHECK (CHAR_LENGTH(TRIM(medicine_code)) > 0),
    CONSTRAINT chk_medicine_name  CHECK (CHAR_LENGTH(TRIM(name)) > 0),
    CONSTRAINT chk_selling_price  CHECK (selling_price >= 0),
    CONSTRAINT chk_reorder_level  CHECK (reorder_level >= 0)
) ENGINE=InnoDB;

CREATE TABLE batches (
    batch_id          INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id       INT         NOT NULL,
    batch_number      VARCHAR(30) NOT NULL,
    expiry_date       DATE        NOT NULL,
    quantity_received INT         NOT NULL,
    quantity_on_hand  INT         NOT NULL,
    received_on       DATE        NOT NULL DEFAULT (CURRENT_DATE),
    CONSTRAINT fk_batches_medicine FOREIGN KEY (medicine_id)
        REFERENCES medicines (medicine_id) ON DELETE RESTRICT,
    CONSTRAINT uq_batch_number UNIQUE (medicine_id, batch_number),
    CONSTRAINT chk_batch_number       CHECK (CHAR_LENGTH(TRIM(batch_number)) > 0),
    CONSTRAINT chk_quantity_received  CHECK (quantity_received > 0),
    CONSTRAINT chk_stock_range        CHECK (quantity_on_hand >= 0
                                             AND quantity_on_hand <= quantity_received)
) ENGINE=InnoDB;

CREATE TABLE sales (
    sale_id       INT AUTO_INCREMENT PRIMARY KEY,
    sold_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    customer_name VARCHAR(100) NULL
) ENGINE=InnoDB;

CREATE TABLE sale_items (
    sale_item_id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id      INT NOT NULL,
    batch_id     INT NOT NULL,
    quantity     INT NOT NULL,
    unit_price   INT NOT NULL,
    CONSTRAINT fk_sale_items_sale  FOREIGN KEY (sale_id)
        REFERENCES sales (sale_id) ON DELETE RESTRICT,
    CONSTRAINT fk_sale_items_batch FOREIGN KEY (batch_id)
        REFERENCES batches (batch_id) ON DELETE RESTRICT,
    CONSTRAINT uq_sale_batch  UNIQUE (sale_id, batch_id),
    CONSTRAINT chk_sale_qty   CHECK (quantity > 0),
    CONSTRAINT chk_sale_price CHECK (unit_price >= 0)
) ENGINE=InnoDB;

CREATE TABLE stock_adjustments (
    adjustment_id   INT AUTO_INCREMENT PRIMARY KEY,
    batch_id        INT NOT NULL,
    quantity_change INT NOT NULL,
    reason          ENUM('EXPIRED_WRITE_OFF','DAMAGED','LOST','COUNT_CORRECTION') NOT NULL,
    note            VARCHAR(255) NULL,
    adjusted_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_adjustments_batch FOREIGN KEY (batch_id)
        REFERENCES batches (batch_id) ON DELETE RESTRICT,
    CONSTRAINT chk_adjustment_nonzero CHECK (quantity_change <> 0),
    CONSTRAINT chk_adjustment_sign CHECK (
        (reason IN ('EXPIRED_WRITE_OFF','DAMAGED','LOST') AND quantity_change < 0)
        OR reason = 'COUNT_CORRECTION')
) ENGINE=InnoDB;