-- CSE 412 - Automotive Shop Management System
-- run this second to populate the tables with sample data

-- owners
INSERT INTO owner (name, phone) VALUES
    ('Freddie Mercury', '928-555-0101'),
    ('Janis Joplin',    '602-555-0234'),
    ('David Bowie',     '480-555-0387'),
    ('Stevie Nicks',    '623-555-0412'),
    ('Jim Morrison',    NULL);

-- vehicles (insert owners first since vehicles reference them)
INSERT INTO vehicle (vin, make, model, year, color, ownerid) VALUES
    ('1HGBH41JXMN109186', 'Ford',    'Edge',     2021, 'White', 1),
    ('2T1BURHE0JC062733', 'Chevy',   'HHR',      2018, 'White', 2),
    ('3VWFE21C04M000001', 'Ford',    'Ranger',   1997, 'Blue',  1),
    ('1FTFW1ET5EKE08234', 'Ford',    'F-150',    2019, 'Black', 3),
    ('5YJSA1DN1DFP14985', 'Toyota',  '4-Runner', 2023, 'Blue',  4),
    ('ODNFA80PNFD123456', 'Mercury', 'Coupe',    1952, 'Red',   5),
    ('9ONCSPJM9EA123456', 'Ford',    'Courier',  1954, 'Red',   5);

-- service records (insert vehicles first since records reference them)
INSERT INTO service_record (servicedate, mileage, description, laborhours, partscost, vin) VALUES
    ('2023-06-12', 22400,  'Oil change and tire rotation',  1.00, 45.99,  '1HGBH41JXMN109186'),
    ('2024-01-08', 31200,  'Coolant flush',                 1.50, 72.00,  '1HGBH41JXMN109186'),
    ('2023-09-15', 87500,  'Oil change',                    0.75, 38.99,  '2T1BURHE0JC062733'),
    ('2024-03-22', 94100,  'New battery',                   0.50, 129.99, '2T1BURHE0JC062733'),
    ('2024-11-05', 101300, 'Transmission fluid change',     1.50, 89.99,  '2T1BURHE0JC062733'),
    ('2024-02-14', 198400, 'Oil change',                    0.75, 34.99,  '3VWFE21C04M000001'),
    ('2024-08-30', 204700, 'New windshield wipers',         0.25, 24.99,  '3VWFE21C04M000001'),
    ('2023-12-01', 55600,  'Oil change and tire rotation',  1.00, 49.99,  '1FTFW1ET5EKE08234'),
    ('2024-07-19', 63200,  'Detail cleaning',               2.00, 0.00,   '1FTFW1ET5EKE08234'),
    ('2024-05-10', 18900,  'Oil change',                    0.75, 52.99,  '5YJSA1DN1DFP14985'),
    ('2025-01-25', 27400,  'Coolant flush and new battery', 1.75, 185.00, '5YJSA1DN1DFP14985'),
    ('2024-09-03', 74200,  'Oil change',                    1.00, 29.99,  'ODNFA80PNFD123456');
