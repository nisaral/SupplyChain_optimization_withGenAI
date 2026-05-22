venv\Scripts\activate
import random
import string
import pandas as pd

# Helper function to generate random string for IDs and names
def random_string(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Generate order data
def generate_order_data(order_ids):
    order_data = []
    for order_id in order_ids:
        order_data.append({
            'Order ID': order_id,
            'Order Date': random.choice(['2023-12-01', '2023-12-10', '2023-12-15']),
            'Customer Name': f'Customer_{random_string(5)}',
            'Order Status': random.choice(['Processing', 'Shipped', 'Delivered']),
            'Delivery Date': random.choice(['2023-12-10', '2023-12-15', '2023-12-20']),
            'Shipment Mode': random.choice(['Air', 'Sea', 'Land']),
            'Order Value': round(random.uniform(10.0, 500.0), 2),
            'Product Description': f'Product_{random_string(5)}',
            'Project Code': random_string(5),
            'Tracking ID': random_string(),
            'Shipping Address': f'{random_string(10)} Street, City, Country',
            'Payment Status': random.choice(['Paid', 'Unpaid']),
            'Order Total': round(random.uniform(50.0, 1000.0), 2),
            'Order Priority': random.choice(['High', 'Medium', 'Low']),
            'Customer Rating': random.randint(1, 5),
            'Product ID': random_string(),
            'Shipping Cost': round(random.uniform(5.0, 50.0), 2),
            'Payment Method': random.choice(['Credit Card', 'PayPal', 'Bank Transfer']),
            'Billing Address': f'{random_string(10)} Street, City, Country',
            'Estimated Delivery Date': random.choice(['2023-12-10', '2023-12-15', '2023-12-20']),
            'Tracking Status': random.choice(['In Transit', 'Out for Delivery', 'Delivered'])
        })
    return order_data

# Generate shipment data
def generate_shipment_data(order_ids):
    shipment_data = []
    for order_id in order_ids:
        shipment_data.append({
            'Order ID': order_id,
            'Tracking ID': random_string(),
            'Shipment Mode': random.choice(['Air', 'Sea', 'Land']),
            'Shipping Address': f'{random_string(10)} Street, City, Country',
            'Delivery Date': random.choice(['2023-12-10', '2023-12-15', '2023-12-20']),
            'Order Value': round(random.uniform(50.0, 500.0), 2),
            'Product Description': f'Product_{random_string(5)}',
            'Shipment Status': random.choice(['Shipped', 'In Transit', 'Delivered']),
            'Order Total': round(random.uniform(50.0, 1000.0), 2),
            'Product ID': random_string(),
            'Return Status': random.choice(['Returned', 'Not Returned']),
            'Estimated Delivery Date': random.choice(['2023-12-10', '2023-12-15', '2023-12-20']),
            'Customs Clearance Status': random.choice(['Cleared', 'Pending']),
            'Tracking Events': f'Event_{random_string(5)}',
            'Shipment Cost': round(random.uniform(10.0, 50.0), 2)
        })
    return shipment_data

# Generate product data
def generate_product_data(order_ids):
    product_data = []
    for order_id in order_ids:
        product_data.append({
            'Product ID': random_string(),
            'Product Name': random.choice(['Laptop', 'Smartphone', 'Headphones', 'Monitor']),
            'Product Category': random.choice(['Electronics', 'Home Appliances', 'Clothing']),
            'Product Description': f'Product_{random_string(5)}',
            'Price': round(random.uniform(10.0, 500.0), 2),
            'Stock Quantity': random.randint(1, 100),
            'Warranty Period': random.randint(1, 3),
            'Product Dimensions': f'{random.randint(5, 20)}x{random.randint(5, 20)}x{random.randint(5, 20)} cm',
            'Manufacturing Date': random.choice(['2023-01-01', '2023-03-15', '2023-07-30']),
            'Expiration Date': random.choice(['2024-01-01', '2025-01-01', '2026-01-01']),
            'SKU': random_string(6),
            'Product Tags': f'{random_string(3)},{random_string(3)}',
            'Color/Size Variations': random.choice(['Red/Small', 'Blue/Medium', 'Green/Large']),
            'Product Ratings': random.randint(1, 5),
        })
    return product_data

# Generate common order_ids
order_ids = [random_string(10) for _ in range(10000)]

order_data = generate_order_data(order_ids)
shipment_data = generate_shipment_data(order_ids)
product_data = generate_product_data(order_ids)

# Save to CSV files
order_df = pd.DataFrame(order_data)
shipment_df = pd.DataFrame(shipment_data)
product_df = pd.DataFrame(product_data)

# Specify file paths
base_path = "Databases/Chatbot_Knowledge_base/" 
orders_file = base_path + 'orders.csv'
shipments_file = base_path + 'shipments.csv'
products_file = base_path + 'products.csv'

# Save DataFrames to CSV files
order_df.to_csv(orders_file, index=False)
shipment_df.to_csv(shipments_file, index=False)
product_df.to_csv(products_file, index=False)

# Print paths to saved files
print(f"Orders file saved to: {orders_file}")
print(f"Shipments file saved to: {shipments_file}")
print(f"Products file saved to: {products_file}")
