import React, { useState } from 'react';

// Updated LoginPage Component
const LoginPage = ({ onNavigate, onLoginSuccess }: { onNavigate: () => void; onLoginSuccess: () => void; }) => {
  // State for username and password remains the same
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // The login handler function is unchanged
  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // This will still log the credentials to the console
    console.log('Logging in with:', { username, password });
    onLoginSuccess();
  };

  return (
    // Section container with a full black background
    // THEME: The component is now set to a full black theme
    <section className="bg-black">
      <div className="flex flex-col items-center justify-center px-6 py-8 mx-auto md:h-screen lg:py-0">
        {/* Logo and App Name */}
        {/* FONT & COLOR: Text color is white */}
        <a href="#" className="flex items-center mb-6 text-2xl font-semibold text-white">
          {/* New custom logo for DB Chat AI */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="1.5"
            stroke="currentColor"
            className="w-8 h-8 mr-2"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              d="M12 21.75c-4.83 0-8.75-3.92-8.75-8.75S7.17 4.25 12 4.25c4.83 0 8.75 3.92 8.75 8.75 0 1.83-.56 3.54-1.5 4.95M8 11h8m-8 3h4" 
            />
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              d="M12 4.25V2.75M12 2.75c-4.83 0-8.75 1.12-8.75 2.5s3.92 2.5 8.75 2.5 8.75-1.12 8.75-2.5S16.83 2.75 12 2.75z" 
            />
          </svg>
          DB Chat AI
        </a>
        {/* Card container */}
        {/* THEME: Card is now styled for a black theme with a subtle border */}
        <div className="w-full bg-black rounded-lg shadow border border-gray-800 md:mt-0 sm:max-w-md xl:p-0">
          <div className="p-6 space-y-4 md:space-y-6 sm:p-8">
            {/* FONT & COLOR: Heading text is white */}
            <h1 className="text-xl font-bold leading-tight tracking-tight text-white md:text-2xl">
              Sign in to your account
            </h1>
            {/* Form with event handler */}
            <form className="space-y-4 md:space-y-6" onSubmit={handleLogin}>
              {/* Username/Email input */}
              <div>
                {/* FONT & COLOR: Label text is white */}
                <label
                  htmlFor="username"
                  className="block mb-2 text-sm font-medium text-white"
                >
                  Your username
                </label>
                {/* THEME: Input field is styled with a dark gray background */}
                <input
                  type="text"
                  name="username"
                  id="username"
                  className="bg-gray-900 border border-gray-700 text-white rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 placeholder-gray-400"
                  placeholder="your_username"
                  required
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                />
              </div>
              {/* Password input */}
              <div>
                <label
                  htmlFor="password"
                  className="block mb-2 text-sm font-medium text-white"
                >
                  Password
                </label>
                <input
                  type="password"
                  name="password"
                  id="password"
                  placeholder="••••••••"
                  className="bg-gray-900 border border-gray-700 text-white rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 placeholder-gray-400"
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                />
              </div>
              <div className="flex items-center justify-between">
                {/* Remember me checkbox */}
                <div className="flex items-start">
                  <div className="flex items-center h-5">
                    <input
                      id="remember"
                      aria-describedby="remember"
                      type="checkbox"
                      className="w-4 h-4 border border-gray-700 rounded bg-gray-900 focus:ring-3 focus:ring-primary-600 ring-offset-gray-800"
                    />
                  </div>
                  <div className="ml-3 text-sm">
                    <label
                      htmlFor="remember"
                      className="text-gray-300"
                    >
                      Remember me
                    </label>
                  </div>
                </div>
                {/* The "Forgot password?" link has been removed from here */}
              </div>
              {/* Submit Button */}
              {/* THEME: Button is styled for a dark theme */}
              <button
                type="submit"
                className="w-full text-white bg-blue-600 hover:bg-blue-700 focus:ring-4 focus:outline-none focus:ring-primary-800 font-medium rounded-lg text-sm px-5 py-2.5 text-center"
              >
                Sign in
              </button>
              <p className="text-sm font-light text-gray-400">
                Don’t have an account yet?{' '}
                <button
                  type="button"
                  onClick={onNavigate}
                  className="font-medium text-primary-500 hover:underline bg-transparent border-none"
                >
                  Sign up
                </button>
              </p>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
};

export default LoginPage;
