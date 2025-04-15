from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timezone
import pandas as pd
import joblib
import json
import io

client = MongoClient(
    'mongodb+srv://salaudeensalu:9535443020@cluster0.8r5k7tl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['churn_analysis']
predictions_collection = db['predictions']

app = Flask(__name__)
CORS(app)

# Load artifacts when the app starts
try:
    model = joblib.load('lr_churn_model.pkl')
    sc = joblib.load('churn_scaler.pkl')
    with open('feature_columns.json', 'r') as f:
        feature_columns = json.load(f)
    print("Model, scaler and features loaded successfully!")
except Exception as e:
    print(f"Error loading artifacts: {e}")
    raise e

def prepare_input_data(data, include_customer_id=False):
    """Helper function to prepare input data for prediction"""
    input_data = pd.DataFrame(columns=feature_columns)
    input_data.loc[0] = 0  # Initialize with zeros

    # Numeric features
    numeric_map = {
        'tenure': 'Tenure',
        'warehouse_to_home': 'WarehouseToHome',
        'num_devices': 'NumberOfDeviceRegistered',
        'satisfaction_score': 'SatisfactionScore'
    }

    for api_name, model_name in numeric_map.items():
        if api_name in data:
            input_data[model_name] = data[api_name]

    # Handle categorical features
    if 'gender' in data:
        gender = data['gender'].title()
        input_data[f'Gender_{gender}'] = 1

    if 'marital_status' in data:
        status = data['marital_status'].title()
        input_data[f'MaritalStatus_{status}'] = 1

    if 'payment_mode' in data:
        payment = data['payment_mode']
        if payment.lower() == "cash on delivery":
            payment = "Cash on Delivery"
        input_data[f'PreferredPaymentMode_{payment}'] = 1
    
    # Only include CustomerID if explicitly requested (for bulk predictions)
    if include_customer_id:
        if 'CustomerID' in data:
            input_data['CustomerID'] = data['CustomerID']
        elif 'customer_id' in data:
            input_data['CustomerID'] = data['customer_id']

    return input_data

@app.route('/predict_churn', methods=['POST'])
def predict_churn():
    try:
        data = request.json
        print("Request data:", data)

        # Prepare input data (exclude CustomerID)
        input_data = prepare_input_data(data, include_customer_id=False)

        # Verify all required columns are present
        missing = set(feature_columns) - set(input_data.columns)
        if missing:
            return jsonify({
                'status': 'error',
                'message': f'Missing features: {missing}'
            })

        # Scale and predict
        scaled_input = sc.transform(input_data)
        prediction = model.predict(scaled_input)
        probability = model.predict_proba(scaled_input)[0][1]

        # Store record with customer_id if provided
        record = {
            'type': 'single',
            'customer_id': data.get('customer_id', data.get('CustomerID', '')),
            'data': data,
            'prediction': int(prediction[0]),
            'probability': float(probability),
            'timestamp': datetime.now(timezone.utc)
        }
        predictions_collection.insert_one(record)

        # Return response with customer_id if provided
        return jsonify({
            'customer_id': data.get('customer_id', data.get('CustomerID', '')),
            'prediction': 'Yes' if prediction[0] == 1 else 'No',
            'probability': float(probability),
            'status': 'success'
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/predict_bulk_churn', methods=['POST'])
def predict_bulk_churn():
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'})

        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No selected file'})

        # Read the file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(file.stream.read().decode('utf-8')))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return jsonify({
                'status': 'error',
                'message': 'Unsupported file format. Please upload CSV or Excel (XLSX/XLS)'
            })

        results = []
        churn_count = 0
        probabilities = []
        error_count = 0

        for _, row in df.iterrows():
            try:
                row_data = row.to_dict()
                # Prepare input data with CustomerID
                input_data = prepare_input_data(row_data, include_customer_id=True)
                
                # Make a copy without CustomerID for prediction
                prediction_data = input_data.drop(columns=['CustomerID'], errors='ignore')
                
                # Scale and predict
                scaled_input = sc.transform(prediction_data)
                prediction = model.predict(scaled_input)
                probability = model.predict_proba(scaled_input)[0][1]

                if prediction[0] == 1:
                    churn_count += 1
                probabilities.append(probability)

                # Get customer ID from the original data
                customer_id = str(row_data.get('CustomerID', row_data.get('customer_id', '')))

                results.append({
                    'customer_id': customer_id,
                    'prediction': 'Yes' if prediction[0] == 1 else 'No',
                    'probability': float(probability),
                    'status': 'success'
                })
            except Exception as e:
                error_count += 1
                customer_id = str(row.get('CustomerID', row.get('customer_id', '')))
                results.append({
                    'customer_id': customer_id,
                    'prediction': '',
                    'probability': 0,
                    'status': f'error: {str(e)}'
                })

        # Calculate analytics
        total_records = len(results)
        success_count = total_records - error_count
        churn_rate = (churn_count / success_count * 100) if success_count > 0 else 0

        # Store bulk records
        bulk_records = []
        for result in results:
            if result['status'] == 'success':
                bulk_records.append({
                    'type': 'bulk',
                    'customer_id': result['customer_id'],
                    'prediction': int(result['prediction'] == 'Yes'),
                    'probability': float(result['probability']),
                    'timestamp': datetime.utcnow()
                })
        if bulk_records:
            predictions_collection.insert_many(bulk_records)

        return jsonify({
            'results': results,
            'analytics': {
                'summary': {
                    'total_records': total_records,
                    'successful_predictions': success_count,
                    'failed_predictions': error_count,
                    'churn_count': churn_count,
                    'churn_rate': round(churn_rate, 2),
                    'success_rate': round((success_count / total_records * 100), 2)
                },
                'probability_stats': {
                    'average': pd.Series(probabilities).mean(),
                    'median': pd.Series(probabilities).median(),
                    'min': pd.Series(probabilities).min(),
                    'max': pd.Series(probabilities).max(),
                    'std_dev': pd.Series(probabilities).std()
                },
                'risk_segmentation': {
                    'low_risk': len([p for p in probabilities if p < 0.3]),
                    'medium_risk': len([p for p in probabilities if 0.3 <= p < 0.7]),
                    'high_risk': len([p for p in probabilities if p >= 0.7])
                },
                'churn_distribution': {
                    'will_churn': churn_count,
                    'will_not_churn': success_count - churn_count
                }
            },
            'status': 'success'
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/analytics', methods=['GET'])
def get_analytics():
    total = predictions_collection.count_documents({})
    churn_count = predictions_collection.count_documents({'prediction': 1})
    churn_rate = (churn_count / total * 100) if total > 0 else 0

    daily_data = list(predictions_collection.aggregate([
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
            "count": {"$sum": 1},
            "churns": {"$sum": {"$cond": [{"$eq": ["$prediction", 1]}, 1, 0]}}
        }},
        {"$sort": {"_id": 1}}
    ]))

    return jsonify({
        'total_predictions': total,
        'churn_rate': round(churn_rate, 2),
        'daily_trends': daily_data,
        'status': 'success'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)