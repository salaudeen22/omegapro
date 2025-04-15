import React, { useState } from "react";
import { useDropzone } from "react-dropzone";
import { toast } from "react-hot-toast";
import axios from "axios";

function PredictPage() {
  const [predictions, setPredictions] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("single");

  // Single prediction form state
  const [formData, setFormData] = useState({
    customer_id: 0,
    tenure: 0,
    warehouse_to_home: 0,
    num_devices: 0,
    satisfaction_score: 0,
    gender: "male",
    marital_status: "single",

    payment_mode: "Credit Card",
    city_tier: 0,
    hour_spend_on_app: 0,
    num_address: 0,
    complain: 0,
    order_amount_hike: 0,
    coupon_used: 0,
    order_count: 0,
    days_since_last_order: 0,
    cashback_amount: 0,
    preferred_login_device: "Mobile Phone",
    preferred_order_category: "Laptop & Accessory",
  });
  // Handle single prediction form change
  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  // Handle single prediction submit
  const handleSingleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    const payload = {
      ...formData,
      customer_id: Number(formData.customer_id),
      tenure: Number(formData.tenure),
      warehouse_to_home: Number(formData.warehouse_to_home),
      num_devices: Number(formData.num_devices),
      satisfaction_score: Number(formData.satisfaction_score),
      city_tier: Number(formData.city_tier),
      hour_spend_on_app: Number(formData.hour_spend_on_app),
      num_address: Number(formData.num_address),
      complain: Number(formData.complain),
      order_amount_hike: Number(formData.order_amount_hike),
      coupon_used: Number(formData.coupon_used),
      order_count: Number(formData.order_count),
      days_since_last_order: Number(formData.days_since_last_order),
      cashback_amount: Number(formData.cashback_amount),
      // Capitalize categorical values
      gender:
        formData.gender.charAt(0).toUpperCase() + formData.gender.slice(1),
      marital_status:
        formData.marital_status.charAt(0).toUpperCase() +
        formData.marital_status.slice(1),
    };

    try {
      const response = await axios.post(
        "http://localhost:5002/predict_churn",
        payload
      );
      setPredictions([{ 
        customer_id: formData.customer_id,
        ...response.data 
      }]);
      toast.success("Prediction successful!");
    } catch (error) {
      toast.error(error.response?.data?.message || "Prediction failed");
    } finally {
      setIsLoading(false);
    }
  };

  // Bulk prediction dropzone
  const { getRootProps, getInputProps } = useDropzone({
    accept: {
      "text/csv": [".csv"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
    },
    maxFiles: 1,
    onDrop: async (acceptedFiles) => {
      if (acceptedFiles.length === 0) return;

      setIsLoading(true);
      const file = acceptedFiles[0];
      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await axios.post(
          "http://localhost:5002/predict_bulk_churn",
          formData,
          {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          }
        );
        setPredictions(response.data.results);
        setAnalytics(response.data.analytics);
        toast.success(
          `Processed ${response.data.analytics.summary.total_records} records`
        );
      } catch (error) {
        toast.error(error.response?.data?.message || "Bulk prediction failed");
      } finally {
        setIsLoading(false);
      }
    },
  });

  // Download template
  const downloadTemplate = () => {
    const csvContent =
      "customer_id,tenure,warehouse_to_home,num_devices,satisfaction_score,gender,marital_status,payment_mode\n1,12,5,3,4,male,single,Credit Card";
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "churn_prediction_template.csv";
    link.click();
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        Customer Churn Prediction
      </h1>

      {/* Tabs */}
      <div className="flex border-b mb-6">
        <button
          className={`py-2 px-4 font-medium ${
            activeTab === "single"
              ? "text-blue-600 border-b-2 border-blue-600"
              : "text-gray-500"
          }`}
          onClick={() => setActiveTab("single")}
        >
          Single Prediction
        </button>
        <button
          className={`py-2 px-4 font-medium ${
            activeTab === "bulk"
              ? "text-blue-600 border-b-2 border-blue-600"
              : "text-gray-500"
          }`}
          onClick={() => setActiveTab("bulk")}
        >
          Bulk Prediction
        </button>
      </div>

      {activeTab === "single" ? (
        <form onSubmit={handleSingleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Existing fields */}
            {/* Tenure */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Customer ID
              </label>
              <input
                type="number"
                name="customer_id"
                value={formData.customer_id}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tenure (months)
              </label>
              <input
                type="number"
                name="tenure"
                value={formData.tenure}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Gender
              </label>
              <select
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Marital Status
              </label>
              <select
                name="marital_status"
                value={formData.marital_status}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="single">Single</option>
                <option value="married">Married</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Payment Mode
              </label>
              <select
                name="payment_mode"
                value={formData.payment_mode}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="Credit Card">Credit Card</option>
                <option value="Debit Card">Debit Card</option>
                <option value="Cash on Delivery">Cash on Delivery</option>
                <option value="Digital Wallet">Digital Wallet</option>
              </select>
            </div>

            {/* Warehouse to Home */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Warehouse to Home Distance (km)
              </label>
              <input
                type="number"
                name="warehouse_to_home"
                value={formData.warehouse_to_home}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>

            {/* Add all new fields */}
            {/* City Tier */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                City Tier
              </label>
              <select
                name="city_tier"
                value={formData.city_tier}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              >
                <option value={1}>Tier 1</option>
                <option value={2}>Tier 2</option>
                <option value={3}>Tier 3</option>
              </select>
            </div>

            {/* Hours Spent on App */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Hours Spent on App
              </label>
              <input
                type="number"
                name="hour_spend_on_app"
                value={formData.hour_spend_on_app}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>

            {/* Number of Addresses */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Number of Addresses
              </label>
              <input
                type="number"
                name="num_address"
                value={formData.num_address}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>

            {/* Complain */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Complain
              </label>
              <select
                name="complain"
                value={formData.complain}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              >
                <option value="0">No</option>
                <option value="1">Yes</option>
              </select>
            </div>

            {/* Order Amount Hike */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Order Amount Hike (%)
              </label>
              <input
                type="number"
                name="order_amount_hike"
                value={formData.order_amount_hike}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>

            {/* Coupon Used */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Coupon Used
              </label>
              <input
                type="number"
                name="coupon_used"
                value={formData.coupon_used}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>

            {/* Order Count */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Order Count
              </label>
              <input
                type="number"
                name="order_count"
                value={formData.order_count}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>

            {/* Days Since Last Order */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Days Since Last Order
              </label>
              <input
                type="number"
                name="days_since_last_order"
                value={formData.days_since_last_order}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>

            {/* Cashback Amount */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cashback Amount
              </label>
              <input
                type="number"
                name="cashback_amount"
                value={formData.cashback_amount}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>

            {/* Preferred Login Device */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Preferred Login Device
              </label>
              <select
                name="preferred_login_device"
                value={formData.preferred_login_device}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              >
                <option value="Mobile Phone">Mobile Phone</option>
                <option value="Computer">Computer</option>
                <option value="Phone">Phone</option>
              </select>
            </div>

            {/* Preferred Order Category */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Preferred Order Category
              </label>
              <select
                name="preferred_order_category"
                value={formData.preferred_order_category}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              >
                <option value="Laptop & Accessory">Laptop & Accessory</option>
                <option value="Mobile">Mobile</option>
                <option value="Fashion">Fashion</option>
                <option value="Grocery">Grocery</option>
              </select>
            </div>
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-blue-300"
          >
            {isLoading ? "Predicting..." : "Predict Churn"}
          </button>
        </form>
      ) : (
        <div>
          <div
            {...getRootProps()}
            className="border-2 border-dashed border-gray-300 rounded-md p-8 text-center cursor-pointer hover:border-blue-500"
          >
            <input {...getInputProps()} />
            <p className="text-gray-600">
              Drag & drop a CSV or Excel file here, or click to select
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Supports .csv, .xls, .xlsx files
            </p>
          </div>
          <div className="mt-4 text-center">
            <button
              onClick={downloadTemplate}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              Download CSV Template
            </button>
          </div>
        </div>
      )}

      {/* Results Section */}
      {predictions && (
        <div className="mt-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Prediction Results
          </h2>

          {/* Analytics Dashboard */}
          {analytics && (
            <div className="bg-gray-50 p-4 rounded-lg mb-6">
              <h3 className="text-lg font-medium text-gray-700 mb-3">
                Bulk Prediction Analytics
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="bg-white p-4 rounded shadow">
                  <h4 className="text-sm font-medium text-gray-500">
                    Total Records
                  </h4>
                  <p className="text-2xl font-bold">
                    {analytics.summary.total_records}
                  </p>
                </div>
                <div className="bg-white p-4 rounded shadow">
                  <h4 className="text-sm font-medium text-gray-500">
                    Churn Rate
                  </h4>
                  <p className="text-2xl font-bold">
                    {analytics.summary.churn_rate}%
                  </p>
                </div>
                <div className="bg-white p-4 rounded shadow">
                  <h4 className="text-sm font-medium text-gray-500">
                    Success Rate
                  </h4>
                  <p className="text-2xl font-bold">
                    {analytics.summary.success_rate}%
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white p-4 rounded shadow">
                  <h4 className="text-sm font-medium text-gray-500 mb-2">
                    Risk Segmentation
                  </h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>High Risk</span>
                      <span className="font-medium">
                        {analytics.risk_segmentation.high_risk}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Medium Risk</span>
                      <span className="font-medium">
                        {analytics.risk_segmentation.medium_risk}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Low Risk</span>
                      <span className="font-medium">
                        {analytics.risk_segmentation.low_risk}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="bg-white p-4 rounded shadow">
                  <h4 className="text-sm font-medium text-gray-500 mb-2">
                    Probability Stats
                  </h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Average</span>
                      <span className="font-medium">
                        {analytics.probability_stats.average.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Max</span>
                      <span className="font-medium">
                        {analytics.probability_stats.max.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Min</span>
                      <span className="font-medium">
                        {analytics.probability_stats.min.toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="bg-white p-4 rounded shadow">
                  <h4 className="text-sm font-medium text-gray-500 mb-2">
                    Churn Distribution
                  </h4>
                  <div className="flex justify-between items-center">
                    <div className="w-1/2 text-center">
                      <div className="text-2xl font-bold text-red-500">
                        {analytics.churn_distribution.will_churn}
                      </div>
                      <div className="text-sm">Will Churn</div>
                    </div>
                    <div className="w-1/2 text-center">
                      <div className="text-2xl font-bold text-green-500">
                        {analytics.churn_distribution.will_not_churn}
                      </div>
                      <div className="text-sm">Will Not Churn</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Results Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white">
              <thead>
                <tr className="bg-gray-100">
                  <th className="py-2 px-4 border">Customer ID</th>
                  <th className="py-2 px-4 border">Prediction</th>
                  <th className="py-2 px-4 border">Probability</th>
                  <th className="py-2 px-4 border">Status</th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((pred, index) => (
                  <tr
                    key={index}
                    className={index % 2 === 0 ? "bg-gray-50" : ""}
                  >
                    <td className="py-2 px-4 border">
                      {pred.customer_id || "-"}
                    </td>
                    <td className="py-2 px-4 border">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          pred.prediction === "Yes"
                            ? "bg-red-100 text-red-800"
                            : pred.prediction === "No"
                            ? "bg-green-100 text-green-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {pred.prediction || "N/A"}
                      </span>
                    </td>
                    <td className="py-2 px-4 border">
                      {pred.probability ? (
                        <div className="w-full bg-gray-200 rounded-full h-2.5">
                          <div
                            className={`h-2.5 rounded-full ${
                              pred.probability >= 0.7
                                ? "bg-red-600"
                                : pred.probability >= 0.3
                                ? "bg-yellow-500"
                                : "bg-green-600"
                            }`}
                            style={{ width: `${pred.probability * 100}%` }}
                          ></div>
                        </div>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td className="py-2 px-4 border">
                      <span
                        className={`text-xs font-medium ${
                          pred.status === "success"
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {pred.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default PredictPage;
