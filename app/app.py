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

    # Unified field name mapping (handles both form and Excel column names)
    field_mapping = {
        # Numeric fields
        'tenure': 'Tenure',
        'Tenure': 'Tenure',
        'city_tier': 'CityTier',
        'CityTier': 'CityTier',
        'warehouse_to_home': 'WarehouseToHome',
        'WarehouseToHome': 'WarehouseToHome',
        'hour_spend_on_app': 'HourSpendOnApp',
        'HourSpendOnApp': 'HourSpendOnApp',
        'num_devices': 'NumberOfDeviceRegistered',
        'NumberOfDeviceRegistered': 'NumberOfDeviceRegistered',
        'satisfaction_score': 'SatisfactionScore',
        'SatisfactionScore': 'SatisfactionScore',
        'num_address': 'NumberOfAddress',
        'NumberOfAddress': 'NumberOfAddress',
        'complain': 'Complain',
        'Complain': 'Complain',
        'order_amount_hike': 'OrderAmountHikeFromlastYear',
        'OrderAmountHikeFromlastYear': 'OrderAmountHikeFromlastYear',
        'coupon_used': 'CouponUsed',
        'CouponUsed': 'CouponUsed',
        'order_count': 'OrderCount',
        'OrderCount': 'OrderCount',
        'days_since_last_order': 'DaySinceLastOrder',
        'DaySinceLastOrder': 'DaySinceLastOrder',
        'cashback_amount': 'CashbackAmount',
        'CashbackAmount': 'CashbackAmount',
        
        # Categorical fields
        'preferred_login_device': 'PreferredLoginDevice',
        'PreferredLoginDevice': 'PreferredLoginDevice',
        'payment_mode': 'PreferredPaymentMode',
        'PreferredPaymentMode': 'PreferredPaymentMode',
        'gender': 'Gender',
        'Gender': 'Gender',
        'preferred_order_category': 'PreferedOrderCat',
        'PreferedOrderCat': 'PreferedOrderCat',
        'marital_status': 'MaritalStatus',
        'MaritalStatus': 'MaritalStatus'
    }

    # Process numeric fields
    for source_name, target_name in field_mapping.items():
        if source_name in data and target_name in feature_columns:
            try:
                # Skip categorical fields (handled below)
                if target_name in ['Tenure', 'CityTier', 'WarehouseToHome', 'HourSpendOnApp',
                                  'NumberOfDeviceRegistered', 'SatisfactionScore', 'NumberOfAddress',
                                  'Complain', 'OrderAmountHikeFromlastYear', 'CouponUsed',
                                  'OrderCount', 'DaySinceLastOrder', 'CashbackAmount']:
                    input_data[target_name] = float(data[source_name])
            except (ValueError, TypeError):
                input_data[target_name] = 0

    # Process categorical fields
    categorical_mappings = {
        'PreferredLoginDevice': {
            'Mobile Phone': 'Mobile Phone',
            'Computer': 'Computer',
            'Phone': 'Phone'
        },
        'PreferredPaymentMode': {
            'Credit Card': 'Credit Card',
            'Debit Card': 'Debit Card',
            'Cash on Delivery': 'Cash on Delivery',
            'Digital Wallet': 'E wallet',
            'UPI': 'UPI',
            'COD': 'Cash on Delivery',
            'CC': 'Credit Card'
        },
        'Gender': {
            'Male': 'Male',
            'Female': 'Female'
        },
        'PreferedOrderCat': {
            'Laptop & Accessory': 'Laptop & Accessory',
            'Mobile': 'Mobile',
            'Fashion': 'Fashion',
            'Grocery': 'Grocery',
            'Mobile Phone': 'Mobile',
            'Others': 'Others'
        },
        'MaritalStatus': {
            'Single': 'Single',
            'Married': 'Married',
            'Divorced': 'Divorced'
        }
    }

    for category, values in categorical_mappings.items():
        source_fields = [k for k,v in field_mapping.items() if v == category]
        for source_field in source_fields:
            if source_field in data:
                value = str(data[source_field]).strip().title()
                mapped_value = values.get(value, None)
                if mapped_value:
                    col_name = f"{category}_{mapped_value}"
                    if col_name in input_data.columns:
                        input_data[col_name] = 1

    # Include CustomerID if requested
    if include_customer_id:
        customer_id = data.get('customer_id', data.get('CustomerID', 0))
        input_data['CustomerID'] = int(customer_id) if str(customer_id).isdigit() else 0

    # Fill missing values with 0 for numeric columns
    input_data.fillna(0, inplace=True)

    # Debug print - show only non-zero columns
    non_zero_cols = input_data.columns[(input_data != 0).any(axis=0)]
    print("Prepared input data (non-zero columns):")
    print(input_data[non_zero_cols].to_string())

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