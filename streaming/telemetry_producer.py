import csv
import json
import time
import os
from kafka import KafkaProducer

# Configure Kafka Producer
KAFKA_BROKER = 'localhost:9092'
TOPIC_NAME = 'supply_chain_events'

def get_producer():
    return KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

def stream_csv_to_kafka(filepath, event_type, producer):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    import datetime
    with open(filepath, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            row['source_id'] = "SAP_ERP_01" if event_type == "logistics_telemetry" else "WMS_01"
            row['ingestion_timestamp'] = datetime.datetime.utcnow().isoformat()
            row['transform_version'] = "v1.1"
            
            payload = {
                "event_type": event_type,
                "data": row
            }
            # Simulate streaming delay
            time.sleep(0.5)
            producer.send(TOPIC_NAME, value=payload)
            print(f"Sent {event_type} event: {payload}")
            
            # To avoid running forever in the simulation, we'll just send 10 rows per file for demo
            if reader.line_num > 10:
                break

if __name__ == "__main__":
    print(f"Connecting to Kafka at {KAFKA_BROKER}")
    # Give Kafka some time to start up if we are running right after docker-compose up
    time.sleep(5)
    
    try:
        producer = get_producer()
        print("Successfully connected to Kafka.")
        
        # Paths to the CSV files
        base_dir = os.path.join("..", "Databases", "Chatbot_Knowledge_base")
        shipments_csv = os.path.join(base_dir, "shipments.csv")
        inventory_csv = os.path.join(base_dir, "category_stock_inventoryy.csv")
        
        # Introduce a bad data scenario manually for the exception_logs demonstration
        bad_payload = {
            "event_type": "logistics_telemetry",
            "data": {
                "Order ID": "BAD_ORDER",
                "Order Value": "NotANumber" # This should fail Pydantic validation
            }
        }
        producer.send(TOPIC_NAME, value=bad_payload)
        print("Sent intentional bad event for testing exception handling.")

        # Stream valid data
        print(f"Streaming from {shipments_csv}...")
        stream_csv_to_kafka(shipments_csv, "logistics_telemetry", producer)
        
        print(f"Streaming from {inventory_csv}...")
        stream_csv_to_kafka(inventory_csv, "inventory_levels", producer)
        
        producer.flush()
        print("Finished streaming events.")
    except Exception as e:
        print(f"Error connecting to Kafka or streaming data: {e}")
