
import React, { useState } from 'react';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';

// Main App Component to manage navigation and authentication state
const App = () => {
  // State to track the current page ('login' or 'signup')
  const [currentPage, setCurrentPage] = useState('login');
  // State to track if the user is authenticated
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Function to navigate to a specific page
  const navigate = (page: 'login' | 'signup') => {
    setCurrentPage(page);
  };

  // Function to handle successful login/signup
  const handleAuthSuccess = () => {
    setIsAuthenticated(true);
  };

  // Function to handle logout
  const handleLogout = () => {
    setIsAuthenticated(false);
    // Optional: redirect to login page after logout
    setCurrentPage('login');
  };

  // Conditionally render the correct page based on the state
  return (
    <div>
      {isAuthenticated ? (
        <DashboardPage onLogout={handleLogout} />
      ) : currentPage === 'login' ? (
        <LoginPage onNavigate={() => navigate('signup')} onLoginSuccess={handleAuthSuccess} />
      ) : (
        <SignupPage onNavigate={() => navigate('login')} onSignupSuccess={handleAuthSuccess} />
      )}
    </div>
  );
};

// A simple Dashboard page shown after login/signup
const DashboardPage = ({ onLogout }: { onLogout: () => void }) => {
  return (
    <section className="bg-black text-white min-h-screen flex flex-col items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Welcome to DB Chat AI</h1>
        <p className="text-lg text-gray-400 mb-8">You have successfully logged in.</p>
        <button
          onClick={onLogout}
          className="text-white bg-red-600 hover:bg-red-700 focus:ring-4 focus:outline-none focus:ring-red-800 font-medium rounded-lg text-sm px-5 py-2.5 text-center"
        >
          Logout
        </button>
      </div>
    </section>
  );
};

export default App;