import React from 'react';
import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="bg-white shadow-sm">
      <div className="container mx-auto px-4 py-3">
        <div className="flex justify-between items-center">
          <Link to="/" className="text-xl font-bold text-blue-600">
            ChurnPredict
          </Link>
          <div className="flex space-x-4">
            <a href="#" className="text-gray-600 hover:text-blue-600">
              Documentation
            </a>
            <a href="#" className="text-gray-600 hover:text-blue-600">
              About
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;