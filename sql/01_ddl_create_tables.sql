-- CSE 412 - Automotive Shop Management System
-- run this first to create the three tables

DROP TABLE IF EXISTS service_record CASCADE;
DROP TABLE IF EXISTS vehicle CASCADE;
DROP TABLE IF EXISTS owner CASCADE;

CREATE TABLE owner (
    ownerid   SERIAL        PRIMARY KEY,
    name      VARCHAR(100)  NOT NULL,
    phone     VARCHAR(20)
);

CREATE TABLE vehicle (
    vin       VARCHAR(17)   PRIMARY KEY,
    make      VARCHAR(50)   NOT NULL,
    model     VARCHAR(50)   NOT NULL,
    year      INT           NOT NULL CHECK (year >= 1900 AND year <= 2100),
    color     VARCHAR(30),
    ownerid   INT           NOT NULL,
    CONSTRAINT fk_vehicle_owner FOREIGN KEY (ownerid)
        REFERENCES owner (ownerid)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE service_record (
    serviceid    SERIAL          PRIMARY KEY,
    servicedate  DATE            NOT NULL,
    mileage      INT             NOT NULL CHECK (mileage >= 0),
    description  TEXT            NOT NULL,
    laborhours   DECIMAL(5, 2)   NOT NULL CHECK (laborhours >= 0),
    partscost    DECIMAL(10, 2)  NOT NULL DEFAULT 0.00 CHECK (partscost >= 0),
    vin          VARCHAR(17)     NOT NULL,
    CONSTRAINT fk_record_vehicle FOREIGN KEY (vin)
        REFERENCES vehicle (vin)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);
