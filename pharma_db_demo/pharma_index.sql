CREATE INDEX idx_batches_medicine_expiry ON batches (medicine_id, expiry_date);
CREATE INDEX idx_batches_expiry          ON batches (expiry_date);
CREATE INDEX idx_sales_sold_at           ON sales (sold_at);