create database billing_software;

use billing_software;

create table admin(
	id Int primary key auto_increment,
    name varchar(50),
    email varchar(50) unique,
    password varchar(50),
    role varchar(20) default "admin"
);

Insert Into admin(id, name, email, password) Values(1, 'Ram', 'ram@ram.com', 'sitaram');

select * from admin;
truncate table admin;
drop table admin;

create table product(
	id Int Primary Key auto_increment,
    name varchar(50),
    sku varchar(50),
	hsn_sac varchar(10),
    unit varchar(10) default "pcs",
    gst_rate Float(10,2) default 0.00,
    unit_price Float(10,2),
    stock_qty Int default 0,
    is_active boolean default True
);

Insert Into product values
(1, "Ball Pen - Blue", "PEN-BLUE-001", "9608", "pcs", 12.00, 10.00, 500, True),
(2, "1 Litre Mineral Water Bottle", "WATER-1L-01", "2201", "bottle", 12.00, 20.00, 1000, False);

truncate product;
drop table product;
select * from product;


Create Table customer(
	id Int Primary key auto_increment,
    name varchar(50),
    phone BigInt,
    email varchar(50),
    gender varchar(10) default "Male",
    gstin varchar(16) default null,
    address varchar(100),
    country varchar(50) default "India",
    state varchar(50),
    city varchar(20),
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

Insert Into customer Value(1, "Sita", 6268795459, "sita@gmail.com", "Female", "22AAAAA1234B1Z5", "Rakesh Nagar", "India", "maharastra", "Mumbai", '2025-08-20');
INSERT INTO customer (name, phone, email, gender, address, state, city)
VALUES ("Sita", 6268795459, "sita@gmail.com", "Female", "Rakesh Nagar", "Maharashtra", "Mumbai");

SET SQL_SAFE_UPDATES = 0;

delete from customer where name = 'ram';
select * from customer;
drop table customer;

# User Table
Create Table user(
	id Int primary key auto_increment,
    name varchar(50),
    email varchar(50) unique,
    password varchar(50),
    role varchar(50) default "User"    
);

insert into user value(1, "Ram", "ram@gmail.com", "sitaram", "User");

select * from user;
drop table user;

Create Table invoice(
	id INT AUTO_INCREMENT PRIMARY KEY,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    customer_id INT,
    place_of_supply VARCHAR(20), -- State code (e.g. 09 for UP)
    subtotal DECIMAL(12,2) DEFAULT 0.00,
    discount_amount DECIMAL(12,2) DEFAULT 0.00,
    cgst DECIMAL(12,2) DEFAULT 0.00,
    sgst DECIMAL(12,2) DEFAULT 0.00,
    igst DECIMAL(12,2) DEFAULT 0.00,
    round_off DECIMAL(12,2) DEFAULT 0.00,
    grand_total DECIMAL(12,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'unpaid',
    user_id INT,
     -- Foreign keys
    CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES customer(id),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES `user`(id)
); 

ALTER TABLE invoice 
ADD COLUMN discount FLOAT(10,2) DEFAULT 0.00,
ADD COLUMN payable FLOAT(10,2) DEFAULT 0.00;

-- Insert sample invoices
INSERT INTO invoice (id, customer_id, place_of_supply, subtotal, discount_amount, cgst, sgst, igst, round_off, grand_total, status, user_id)
VALUES
(1001, 1, '09', 5000.00, 200.00, 135.00, 135.00, 0.00, 0.00, 5070.00, 'unpaid', 1),

(1002, 2, '27', 8000.00, 500.00, 315.00, 315.00, 0.00, -0.50, 8114.50, 'paid', 2),

(1003, 3, '07', 3000.00, 0.00, 0.00, 0.00, 540.00, 0.00, 3540.00, 'unpaid', 1);

-- Error Code: 1442. Can't update table 'invoice' in stored function/trigger because it is already used by statement which invoked this stored function/trigger.-- 


Select * From invoice;
truncate table invoice;
drop table invoice;





truncate table invoice_item;
drop table invoice_item;
CREATE TABLE invoice_item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    product_id INT,
    description VARCHAR(255),
    qty DECIMAL(12,3) NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,
    discount_pct DECIMAL(5,2) DEFAULT 0.00,  -- discount per line in %
    gst_rate DECIMAL(5,2) DEFAULT 0.00,      -- GST % for this line

    line_subtotal DECIMAL(12,2) DEFAULT 0.00,
    line_cgst DECIMAL(12,2) DEFAULT 0.00,
    line_sgst DECIMAL(12,2) DEFAULT 0.00,
    line_igst DECIMAL(12,2) DEFAULT 0.00,
    line_total DECIMAL(12,2) DEFAULT 0.00,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign keys
    CONSTRAINT fk_invoice FOREIGN KEY (invoice_id) REFERENCES invoice(id) ON DELETE CASCADE,
    CONSTRAINT fk_product FOREIGN KEY (product_id) REFERENCES product(id)
);

select * from invoice_item;


CREATE TABLE payment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    method VARCHAR(20),               -- cash / card / upi / netbanking
    -- txn_ref VARCHAR(50),              -- transaction reference (optional)
    paid_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign key
    CONSTRAINT fk_payment_invoice FOREIGN KEY (invoice_id) REFERENCES invoice(id) ON DELETE CASCADE
);

drop table payment;
select * from payment;