CREATE TABLE IF NOT EXISTS logistics_telemetry (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50),
    tracking_id VARCHAR(50),
    shipment_mode VARCHAR(50),
    shipping_address TEXT,
    delivery_date DATE,
    order_value NUMERIC,
    product_description TEXT,
    shipment_status VARCHAR(50),
    order_total NUMERIC,
    product_id VARCHAR(50),
    return_status VARCHAR(50),
    estimated_delivery_date DATE,
    customs_clearance_status VARCHAR(50),
    tracking_events TEXT,
    shipment_cost NUMERIC,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_id VARCHAR(50),
    ingestion_timestamp TIMESTAMP,
    transform_version VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS inventory_levels (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100),
    qty_ordered INT,
    remaining_stock INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exception_logs (
    id SERIAL PRIMARY KEY,
    payload TEXT,
    error_message TEXT,
    status VARCHAR(20) DEFAULT 'PENDING',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id SERIAL PRIMARY KEY,
    payload TEXT,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
