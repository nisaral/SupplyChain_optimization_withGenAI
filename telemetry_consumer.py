import json
import psycopg2
from psycopg2.extras import execute_values
from kafka import KafkaConsumer
from pydantic import BaseModel, ValidationError, Field, field_validator
from typing import Optional
from datetime import date

KAFKA_BROKER = 'localhost:9092'
TOPIC_NAME = 'supply_chain_events'

DB_CONFIG = {
    'dbname': 'supply_chain',
    'user': 'admin',
    'password': 'adminpassword',
    'host': 'localhost',
    'port': '5432'
}

# Pydantic Schemas for Validation
class LogisticsTelemetry(BaseModel):
    order_id: str = Field(alias="Order ID")
    tracking_id: Optional[str] = Field(alias="Tracking ID", default=None)
    shipment_mode: Optional[str] = Field(alias="Shipment Mode", default=None)
    shipping_address: Optional[str] = Field(alias="Shipping Address", default=None)
    delivery_date: Optional[date] = Field(alias="Delivery Date", default=None)
    order_value: float = Field(alias="Order Value")
    product_description: Optional[str] = Field(alias="Product Description", default=None)
    shipment_status: Optional[str] = Field(alias="Shipment Status", default=None)
    order_total: Optional[float] = Field(alias="Order Total", default=None)
    product_id: Optional[str] = Field(alias="Product ID", default=None)
    return_status: Optional[str] = Field(alias="Return Status", default=None)
    estimated_delivery_date: Optional[date] = Field(alias="Estimated Delivery Date", default=None)
    customs_clearance_status: Optional[str] = Field(alias="Customs Clearance Status", default=None)
    tracking_events: Optional[str] = Field(alias="Tracking Events", default=None)
    shipment_cost: Optional[float] = Field(alias="Shipment Cost", default=None)

    @field_validator('delivery_date', 'estimated_delivery_date', mode='before')
    def parse_dates(cls, value):
        if value == '' or value is None:
            return None
        return value

    @field_validator('order_value', 'order_total', 'shipment_cost', mode='before')
    def parse_floats(cls, value):
        if value == '' or value is None:
            return None
        return value

class InventoryLevel(BaseModel):
    category: str
    qty_ordered: int
    remaining_stock: int
    
    @field_validator('qty_ordered', 'remaining_stock', mode='before')
    def parse_ints(cls, value):
        if value == '' or value is None:
            return 0
        return int(value)

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def log_exception(conn, payload, error_message):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO exception_logs (payload, error_message) VALUES (%s, %s)",
                (json.dumps(payload), str(error_message))
            )
        conn.commit()
        print(f"Logged exception for payload: {payload}")
    except Exception as e:
        print(f"Failed to log exception: {e}")
        conn.rollback()

def insert_logistics_telemetry(conn, data):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO logistics_telemetry (
                    order_id, tracking_id, shipment_mode, shipping_address, delivery_date,
                    order_value, product_description, shipment_status, order_total, product_id,
                    return_status, estimated_delivery_date, customs_clearance_status, tracking_events, shipment_cost
                ) VALUES (
                    %(order_id)s, %(tracking_id)s, %(shipment_mode)s, %(shipping_address)s, %(delivery_date)s,
                    %(order_value)s, %(product_description)s, %(shipment_status)s, %(order_total)s, %(product_id)s,
                    %(return_status)s, %(estimated_delivery_date)s, %(customs_clearance_status)s, %(tracking_events)s, %(shipment_cost)s
                )
            """, data.model_dump())
        conn.commit()
        print(f"Inserted logistics_telemetry: {data.order_id}")
    except Exception as e:
        conn.rollback()
        raise e

def insert_inventory_level(conn, data):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO inventory_levels (category, qty_ordered, remaining_stock)
                VALUES (%(category)s, %(qty_ordered)s, %(remaining_stock)s)
            """, data.model_dump())
        conn.commit()
        print(f"Inserted inventory_level for category: {data.category}")
    except Exception as e:
        conn.rollback()
        raise e

def consume_events():
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='etl_group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    conn = get_db_connection()
    print("Listening for events on Kafka topic...")

    try:
        for message in consumer:
            payload = message.value
            event_type = payload.get("event_type")
            data_raw = payload.get("data")
            
            if not event_type or not data_raw:
                log_exception(conn, payload, "Missing event_type or data in payload")
                continue
                
            try:
                if event_type == "logistics_telemetry":
                    validated_data = LogisticsTelemetry(**data_raw)
                    insert_logistics_telemetry(conn, validated_data)
                elif event_type == "inventory_levels":
                    validated_data = InventoryLevel(**data_raw)
                    insert_inventory_level(conn, validated_data)
                else:
                    log_exception(conn, payload, f"Unknown event_type: {event_type}")
            except ValidationError as e:
                # Catch Pydantic validation errors and route to exception_logs
                log_exception(conn, payload, e.json())
            except Exception as e:
                # Catch DB errors
                log_exception(conn, payload, str(e))
                
    except KeyboardInterrupt:
        print("Stopping consumer...")
    finally:
        consumer.close()
        conn.close()

if __name__ == "__main__":
    consume_events()
