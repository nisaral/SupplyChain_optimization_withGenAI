from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import psycopg2
from statsmodels.tsa.statespace.sarimax import SARIMAX
import networkx as nx
import math
from typing import List, Dict, Tuple
from datetime import datetime, timedelta

app = FastAPI(title="Supply Chain API", description="Predictive Engine & Routing API")

DB_CONFIG = {
    'dbname': 'supply_chain',
    'user': 'admin',
    'password': 'adminpassword',
    'host': 'localhost',
    'port': '5432'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

class RouteRequest(BaseModel):
    nodes: List[Dict[str, float]] # e.g., [{"name": "Warehouse", "lat": 40.71, "lon": -74.00}, ...]

def calculate_distance(node1, node2):
    # Simple Euclidean distance for heuristic routing
    return math.sqrt((node1['lat'] - node2['lat'])**2 + (node1['lon'] - node2['lon'])**2)

@app.get("/api/forecast")
def forecast_demand(sku: str = None):
    try:
        conn = get_db_connection()
        query = """
            SELECT delivery_date as date, sum(order_value) as total_sales
            FROM logistics_telemetry
            WHERE delivery_date IS NOT NULL
        """
        if sku:
            query += f" AND product_id = '{sku}'"
            
        query += " GROUP BY delivery_date ORDER BY delivery_date"
        
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty or len(df) < 10:
            raise HTTPException(status_code=400, detail="Not enough historical data to generate forecast")

        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        # Resample to daily to ensure continuous time series
        df = df.resample('D').sum().fillna(0)

        # Fit SARIMA Model (parameters simplified for robustness in API)
        # Using simple ARIMA (1, 1, 1) for fast inference
        model = SARIMAX(df['total_sales'], order=(1, 1, 1), enforce_stationarity=False, enforce_invertibility=False)
        results = model.fit(disp=False)

        # Forecast next 7 days
        forecast = results.get_forecast(steps=7)
        forecast_index = [df.index[-1] + timedelta(days=i) for i in range(1, 8)]
        predicted_means = forecast.predicted_mean.tolist()

        return {
            "sku": sku if sku else "ALL",
            "forecast": [
                {"date": str(date.date()), "predicted_sales": round(value, 2)}
                for date, value in zip(forecast_index, predicted_means)
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimize-route")
def optimize_route(request: RouteRequest):
    nodes = request.nodes
    if len(nodes) < 2:
        return {"route": [node['name'] for node in nodes], "total_distance": 0}

    # Build fully connected graph
    G = nx.Graph()
    for i, node_i in enumerate(nodes):
        for j, node_j in enumerate(nodes):
            if i != j:
                dist = calculate_distance(node_i, node_j)
                G.add_edge(i, j, weight=dist)

    # Use networkx traveling salesperson approximation (Christofides algorithm requires triangle inequality which Euclidean satisfies)
    try:
        tsp_path = nx.approximation.traveling_salesman_problem(G, cycle=True)
    except Exception:
        # Fallback if networkx TSP fails
        tsp_path = list(range(len(nodes))) + [0]
        
    optimized_route = [nodes[i]['name'] for i in tsp_path]
    
    # Calculate total distance
    total_distance = 0
    for i in range(len(tsp_path) - 1):
        total_distance += G[tsp_path[i]][tsp_path[i+1]]['weight']

    return {
        "optimized_route": optimized_route,
        "total_distance": round(total_distance, 4)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
