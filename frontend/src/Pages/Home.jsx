import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import axios from 'axios';
import { Link } from 'react-router-dom';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const Home = () => {
    const [analytics, setAnalytics] = useState(null);
    
    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                const response = await axios.get('http://localhost:5002/analytics');
                setAnalytics(response.data);
            } catch (error) {
                console.error('Error fetching analytics:', error);
            }
        };
        fetchAnalytics();
    }, []);

    if (!analytics) return <div>Loading analytics...</div>;

    const chartData = {
        labels: analytics.daily_trends.map(day => day._id),
        datasets: [
            {
                label: 'Total Predictions',
                data: analytics.daily_trends.map(day => day.count),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            },
            {
                label: 'Churns',
                data: analytics.daily_trends.map(day => day.churns),
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1
            }
        ]
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold">Analytics Dashboard</h2>
                <Link to="/predict" className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                    New Prediction
                </Link>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="text-gray-500 text-sm">Total Predictions</h3>
                    <p className="text-3xl font-bold">{analytics.total_predictions}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="text-gray-500 text-sm">Overall Churn Rate</h3>
                    <p className="text-3xl font-bold">{analytics.churn_rate}%</p>
                </div>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4">Prediction Trends</h3>
                <Line data={chartData} />
            </div>
        </div>
    );
};

export default Home;