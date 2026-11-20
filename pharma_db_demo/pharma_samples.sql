INSERT INTO medicines (medicine_code, name, strength, dosage_form, selling_price, reorder_level) VALUES
('PAR500',  'Paracetamol',             '500 mg',    'TABLET',  150,  50),  -- id 1
('AMX250',  'Amoxicillin',             '250 mg',    'CAPSULE', 400,  30),  -- id 2
('ORS200',  'Oral rehydration salts',  '200 ml',    'SACHET',  200,  40),  -- id 3
('ALU2012', 'Artemether-lumefantrine', '20/120 mg', 'TABLET',  1500, 20),  -- id 4
('IBU400',  'Ibuprofen',               '400 mg',    'TABLET',  200,  30),  -- id 5
('COU100',  'Cough syrup',             '100 ml',    'SYRUP',   1800, 10);  -- id 6

INSERT INTO batches (medicine_id, batch_number, expiry_date, quantity_received, quantity_on_hand) VALUES
(1, 'PX2601', '2026-12-15', 200, 200),  -- batch 1, expires in 25 days
(1, 'PX2605', '2027-08-31', 300, 300),  -- batch 2
(2, 'AM2603', '2026-10-31', 60,  60),   -- batch 3, EXPIRED, cannot be sold
(2, 'AM2611', '2027-03-31', 120, 120),  -- batch 4
(3, 'OR2517', '2026-12-28', 40,  40),   -- batch 5, outside the 30-day window
(4, 'AL2609', '2026-12-10', 25,  25),   -- batch 6, expires in 20 days
(5, 'IB2701', '2027-05-31', 100, 100),  -- batch 7
(6, 'CS2604', '2026-12-05', 12,  12);   -- batch 8, expires in 15 days

INSERT INTO sales (sold_at, customer_name) VALUES
('2026-11-18 09:30:00', 'Walk-in'),              -- sale 1
('2026-11-19 14:05:00', 'Kirehe Health Post'),   -- sale 2
('2026-11-20 08:45:00', 'Walk-in');              -- sale 3

INSERT INTO sale_items (sale_id, batch_id, quantity, unit_price) VALUES
(1, 1, 10, 150),   -- paracetamol
(1, 4, 5,  400),   -- amoxicillin
(2, 6, 10, 1500),  -- artemether-lumefantrine
(2, 8, 4,  1800),  -- cough syrup
(3, 7, 2,  200),   -- ibuprofen
(3, 5, 6,  200);   -- ORS

INSERT INTO stock_adjustments (batch_id, quantity_change, reason, note) VALUES
(2, -5, 'DAMAGED', 'Cracked bottles found during shelf check');