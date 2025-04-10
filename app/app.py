from flask import Flask, request, jsonify
from flask_cors import CORS

import pandas as pd
import joblib
import json
import io

app = Flask(__name__)
CORS(app)

# Load artifacts when the app starts
try:
    # Load the model
    model = joblib.load('lr_churn_model.pkl')

    # Load the scaler
    sc = joblib.load('churn_scaler.pkl')

    # Load feature columns
    with open('feature_columns.json', 'r') as f:
        feature_columns = json.load(f)

    print("Model, scaler and features loaded successfully!")
except Exception as e:
    print(f"Error loading artifacts: {e}")
    raise e


def prepare_input_data(data):
    """Helper function to prepare input data for prediction"""
    # Create empty DataFrame with correct columns
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

    # Handle categorical features with exact matching
    if 'gender' in data:
        gender = data['gender'].title()  # Converts to "Male" or "Female"
        input_data[f'Gender_{gender}'] = 1

    if 'marital_status' in data:
        status = data['marital_status'].title()  # "Single" or "Married"
        input_data[f'MaritalStatus_{status}'] = 1

    if 'payment_mode' in data:
        # Standardize to match training data format
        payment = data['payment_mode']
        if payment.lower() == "cash on delivery":
            payment = "Cash on Delivery"  # Exact match
        input_data[f'PreferredPaymentMode_{payment}'] = 1

    return input_data


@app.route('/predict_churn', methods=['POST'])
def predict_churn():
    try:
        data = request.json
        
        # Prepare input data
        input_data = prepare_input_data(data)

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

        return jsonify({
            'prediction': 'Yes' if prediction[0] == 1 else 'No',
            'probability': float(probability),
            'status': 'success'
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/predict_bulk_churn', methods=['POST'])
def predict_bulk_churn():
    try:
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No selected file'})
        
        # Read the file based on extension
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
        
        # Process each row
        for _, row in df.iterrows():
            try:
                # Prepare input data
                input_data = prepare_input_data(row.to_dict())
                
                # Scale and predict
                scaled_input = sc.transform(input_data)
                prediction = model.predict(scaled_input)
                probability = model.predict_proba(scaled_input)[0][1]
                
                if prediction[0] == 1:
                    churn_count += 1
                probabilities.append(probability)
                
                results.append({
                    'customer_id': row.get('customer_id', ''),
                    'prediction': 'Yes' if prediction[0] == 1 else 'No',
                    'probability': float(probability),
                    'status': 'success'
                })
            except Exception as e:
                error_count += 1
                results.append({
                    'customer_id': row.get('customer_id', ''),
                    'prediction': '',
                    'probability': 0,
                    'status': f'error: {str(e)}'
                })
        
        # Calculate analytics
        total_records = len(results)
        success_count = total_records - error_count
        churn_rate = (churn_count / success_count * 100) if success_count > 0 else 0
        
        # Probability distribution
        prob_series = pd.Series(probabilities)
        prob_stats = {
            'average': prob_series.mean(),
            'median': prob_series.median(),
            'min': prob_series.min(),
            'max': prob_series.max(),
            'std_dev': prob_series.std()
        }
        
        # Risk segmentation
        risk_segments = {
            'low_risk': len([p for p in probabilities if p < 0.3]),
            'medium_risk': len([p for p in probabilities if 0.3 <= p < 0.7]),
            'high_risk': len([p for p in probabilities if p >= 0.7])
        }
        
        # Top features analysis (example - would need your model's feature importance)
        top_features = [
            {'feature': 'Tenure', 'importance': 0.25},
            {'feature': 'SatisfactionScore', 'importance': 0.20},
            {'feature': 'WarehouseToHome', 'importance': 0.15}
        ]
        
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
                'probability_stats': prob_stats,
                'risk_segmentation': risk_segments,
                'top_features': top_features,
                'churn_distribution': {
                    'will_churn': churn_count,
                    'will_not_churn': success_count - churn_count
                }
            },
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# @app.route('/predict_bulk_churn', methods=['POST'])
# def predict_bulk_churn():
#     try:
#         # Check if a file was uploaded
#         if 'file' not in request.files:
#             return jsonify({'status': 'error', 'message': 'No file uploaded'})
        
#         file = request.files['file']
#         if file.filename == '':
#             return jsonify({'status': 'error', 'message': 'No selected file'})
        
#         # Read the file based on extension
#         if file.filename.endswith('.csv'):
#             df = pd.read_csv(io.StringIO(file.stream.read().decode('utf-8')))
#         elif file.filename.endswith(('.xlsx', '.xls')):
#             df = pd.read_excel(file)
#         else:
#             return jsonify({
#                 'status': 'error',
#                 'message': 'Unsupported file format. Please upload CSV or Excel (XLSX/XLS)'
#             })
        
#         results = []
        
#         # Process each row
#         for _, row in df.iterrows():
#             try:
#                 # Prepare input data
#                 input_data = prepare_input_data(row.to_dict())
                
#                 # Scale and predict
#                 scaled_input = sc.transform(input_data)
#                 prediction = model.predict(scaled_input)
#                 probability = model.predict_proba(scaled_input)[0][1]
                
#                 results.append({
#                     'customer_id': row.get('customer_id', ''),
#                     'prediction': 'Yes' if prediction[0] == 1 else 'No',
#                     'probability': float(probability),
#                     'status': 'success'
#                 })
#             except Exception as e:
#                 results.append({
#                     'customer_id': row.get('customer_id', ''),
#                     'prediction': '',
#                     'probability': 0,
#                     'status': f'error: {str(e)}'
#                 })
        
#         return jsonify({
#             'results': results,
#             'total_records': len(results),
#             'successful_predictions': sum(1 for r in results if r['status'] == 'success'),
#             'status': 'success'
#         })
        
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)