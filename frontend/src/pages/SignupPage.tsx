import React, { useState } from 'react';

// Updated SignupPage Component
const SignupPage = ({ onNavigate, onSignupSuccess }: { onNavigate: () => void; onSignupSuccess: () => void; }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleSignup = (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
        console.error("Passwords do not match!");
        return;
    }
    console.log('Signing up with:', { username, password });
    // Simulate a successful signup
    onSignupSuccess();
  };

  return (
    <section className="bg-black">
      <div className="flex flex-col items-center justify-center px-6 py-8 mx-auto md:h-screen lg:py-0">
        <a href="#" className="flex items-center mb-6 text-2xl font-semibold text-white">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="w-8 h-8 mr-2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 21.75c-4.83 0-8.75-3.92-8.75-8.75S7.17 4.25 12 4.25c4.83 0 8.75 3.92 8.75 8.75 0 1.83-.56 3.54-1.5 4.95M8 11h8m-8 3h4" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.25V2.75M12 2.75c-4.83 0-8.75 1.12-8.75 2.5s3.92 2.5 8.75 2.5 8.75-1.12 8.75-2.5S16.83 2.75 12 2.75z" />
          </svg>
          DB Chat AI
        </a>
        <div className="w-full bg-black rounded-lg shadow border border-gray-800 md:mt-0 sm:max-w-md xl:p-0">
          <div className="p-6 space-y-4 md:space-y-6 sm:p-8">
            <h1 className="text-xl font-bold leading-tight tracking-tight text-white md:text-2xl">
              Create an account
            </h1>
            <form className="space-y-4 md:space-y-6" onSubmit={handleSignup}>
              <div>
                <label htmlFor="username" className="block mb-2 text-sm font-medium text-white">Your username</label>
                <input type="text" name="username" id="username" className="bg-gray-900 border border-gray-700 text-white rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 placeholder-gray-400" placeholder="your_username" required value={username} onChange={e => setUsername(e.target.value)} />
              </div>
              <div>
                <label htmlFor="password" className="block mb-2 text-sm font-medium text-white">Password</label>
                <input type="password" name="password" id="password" placeholder="••••••••" className="bg-gray-900 border border-gray-700 text-white rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 placeholder-gray-400" required value={password} onChange={e => setPassword(e.target.value)} />
              </div>
              <div>
                <label htmlFor="confirm-password" className="block mb-2 text-sm font-medium text-white">Confirm password</label>
                <input type="password" name="confirm-password" id="confirm-password" placeholder="••••••••" className="bg-gray-900 border border-gray-700 text-white rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 placeholder-gray-400" required value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} />
              </div>
              <button type="submit" className="w-full text-white bg-blue-600 hover:bg-blue-700 focus:ring-4 focus:outline-none focus:ring-primary-800 font-medium rounded-lg text-sm px-5 py-2.5 text-center">Create an account</button>
              <p className="text-sm font-light text-gray-400">
                Already have an account?{' '}
                <button type="button" onClick={onNavigate} className="font-medium text-primary-500 hover:underline focus:outline-none bg-transparent">Login here</button>
              </p>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
};

export default SignupPage;
