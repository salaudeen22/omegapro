// App.js
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./Pages/Home";

import PredictPage from "./Pages/PredictPage.jsx";
import Navbar from "./Components/Navbar";
import { Toaster } from "react-hot-toast";

function App() {
    return (
        <Router>
            <div className="min-h-screen bg-gray-50">
                <Navbar />
                <Toaster position="top-right" />
                <div className="container mx-auto px-4 py-8">
                    <Routes>
                        <Route path="/" element={<Home />} />
                        <Route path="/predict" element={<PredictPage />} />
                     
                    </Routes>
                </div>
            </div>
        </Router>
    );
}
export default App;