import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import chi2_contingency
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeClassifier

# Load the dataset
df = pd.read_excel("/Users/salaudeenn/Documents/PROJECTS/omegapro/E Commerce Dataset (2).xlsx", sheet_name="E Comm")

# Basic info
print(df.columns)
print(df.info())
for col in df.columns:
    if df[col].dtype == 'object':
        print(f'Unique values in column {col}: {df[col].unique()}')
print(df.describe())

# Gender vs Churn
grouped = df.groupby(['Gender', 'Churn']).count()['CustomerID']
grouped.unstack().plot(kind='bar', stacked=False)
plt.xlabel('Gender')
plt.ylabel('Count')
plt.title('Churn by Gender')
plt.show()

# Tenure vs Churn
grouped = df.groupby(['Tenure', 'Churn']).count()['CustomerID']
grouped.unstack().plot(kind='bar', stacked=False)
plt.xlabel('Tenure')
plt.ylabel('Count')
plt.title('Churn by Tenure')
plt.show()

# Payment Mode vs Churn
grouped = df.groupby(['PreferredPaymentMode', 'Churn']).count()['CustomerID']
grouped.unstack().plot(kind='bar', stacked=False)
plt.xlabel('Preferred Payment Method')
plt.ylabel('Count')
plt.title('Churn by Preferred Payment Method')
plt.show()

# Fill missing values
df = df.fillna(df.mode().iloc[0])
print(df.info())

# Correlation heatmap
df = pd.get_dummies(df, columns=df.select_dtypes(include=['object']).columns)
plt.figure(figsize=(15, 10))
sns.heatmap(df.corr(), cmap='coolwarm')
plt.show()

# Drop ID
df = df.drop("CustomerID", axis=1)

# Chi-Square for categorical features
cat_features = df.select_dtypes(include=['object']).columns
for feature in cat_features:
    cross_tab = pd.crosstab(df[feature], df['Churn'])
    stat, p, dof, expected = chi2_contingency(cross_tab)
    print(f"{feature}: Chi-square Statistic = {stat}, p-value = {p}")
    alpha = 0.05
    if p > alpha:
        print(f"{feature} is NOT significantly related to churn")
    else:
        print(f"{feature} is significantly related to churn")

# Final encoding
df = pd.get_dummies(df, columns=df.select_dtypes(['object']).columns)

# Train-test split
X = df.drop('Churn', axis=1)
y = df['Churn']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
print(y_train.value_counts())

# Standardization
sc = StandardScaler()
X_train = sc.fit_transform(X_train)
X_test = sc.transform(X_test)

# Logistic Regression
lr_clf = LogisticRegression(random_state=0)
lr_clf.fit(X_train, y_train)
print('Accuracy on training set:', lr_clf.score(X_train, y_train))
print('Accuracy on test set:', lr_clf.score(X_test, y_test))

# Naive Bayes
nb_clf = GaussianNB()
nb_clf.fit(X_train, y_train)
print('Accuracy on training set:', nb_clf.score(X_train, y_train))
print('Accuracy on test set:', nb_clf.score(X_test, y_test))

# Random Forest
rf_clf = RandomForestRegressor(n_estimators=10, random_state=0)
rf_clf.fit(X_train, y_train)
print('Accuracy on training set:', rf_clf.score(X_train, y_train))
print('Accuracy on test set:', rf_clf.score(X_test, y_test))

# Decision Tree
dec_clf = DecisionTreeClassifier()
dec_clf.fit(X_train, y_train)
print('Accuracy on training set:', dec_clf.score(X_train, y_train))
print('Accuracy on test set:', dec_clf.score(X_test, y_test))



# model = lr_clf
# # model = nb_clf
# # model = dec_clf
# # model = rf_clf
#
# # Test with random data
#
# new_data = pd.DataFrame([{
#     'Tenure': 12,
#     'WarehouseToHome': 10,
#     'NumberOfDeviceRegistered': 3,
#     'SatisfactionScore': 4,
#     'MaritalStatus_Married': 1,
#     'MaritalStatus_Single': 0,
#     'Gender_Female': 1,
#     'Gender_Male': 0,
#     'PreferredPaymentMode_Credit Card': 0,
#     'PreferredPaymentMode_Debit Card': 1,
# }])
#
#
# new_data = new_data.reindex(columns=X.columns, fill_value=0)
# new_data_scaled = sc.transform(new_data)
#
# prediction = model.predict(new_data_scaled)
# print("Predicted Churn:", "Yes" if prediction[0] == 1 else "No")


model = lr_clf  # You can swap with nb_clf, dec_clf, etc.

# Modified input to increase churn likelihood
new_data = pd.DataFrame([{
    'Tenure': 1,                       # Very new customer
    'WarehouseToHome': 20,            # Long delivery time
    'NumberOfDeviceRegistered': 5,    # Many devices
    'SatisfactionScore': 1,           # Very low satisfaction
    'MaritalStatus_Married': 0,
    'MaritalStatus_Single': 1,
    'Gender_Female': 0,
    'Gender_Male': 1,
    'PreferredPaymentMode_Credit Card': 0,
    'PreferredPaymentMode_Debit Card': 0,
    'PreferredPaymentMode_Cash on Delivery': 1,  # If this exists
    'PreferredPaymentMode_UPI': 0,
    'PreferredPaymentMode_E wallet': 0,
    'PreferredPaymentMode_Net Banking': 0,
    # Fill other dummies with 0
}])

# Align columns with training data
new_data = new_data.reindex(columns=X.columns, fill_value=0)
new_data_scaled = sc.transform(new_data)

# Predict churn
prediction = model.predict(new_data_scaled)
print("Predicted Churn:", "Yes" if prediction[0] == 1 else "No")

import joblib

# Save the Logistic Regression model (you can save others similarly)
joblib.dump(lr_clf, 'lr_churn_model.pkl')  # Best practice to use descriptive names

# Save the StandardScaler
joblib.dump(sc, 'churn_scaler.pkl')

# Optionally save other models
joblib.dump(nb_clf, 'nb_churn_model.pkl')
joblib.dump(rf_clf, 'rf_churn_model.pkl')
joblib.dump(dec_clf, 'dt_churn_model.pkl')

# Save the feature columns (important for matching input structure)
import json

print("All feature columns:", list(X.columns))
with open('feature_columns.json', 'w') as f:
    json.dump(list(X.columns), f)
    