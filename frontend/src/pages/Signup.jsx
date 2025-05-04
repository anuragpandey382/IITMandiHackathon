import { useNavigate } from 'react-router-dom';
import Google from '../assets/google.png';
import Cyber from '../assets/security.png';
import { useEffect, useState } from 'react';

export const Signup = () => {
    const navigate = useNavigate();
    const [darkMode, setDarkMode] = useState(false);

    useEffect(() => {
        // 🔹 Load dark mode preference from localStorage
        const savedTheme = localStorage.getItem("theme");
        if (savedTheme === "dark") {
            document.documentElement.classList.add("dark");
            setDarkMode(true);
        } else {
            document.documentElement.classList.remove("dark");
            setDarkMode(false);
        }
    }, []);
    
    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const jwtToken = urlParams.get("jwt");

        if (jwtToken) {
            // Store token
            localStorage.setItem("token", jwtToken);
            
            // Instead of dispatching storage event, we'll use a custom event
            window.dispatchEvent(new Event("tokenUpdate"));
            
            // Clear URL and redirect
            window.history.replaceState({}, "", "/");
            navigate("/");
        }
    }, [navigate]);


    const handleGoogleSignup = () => {
        window.location.href = "https://my-app.b22023.workers.dev/google/login"; 
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-lightBg dark:bg-darkBg p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-6xl w-full">
                
                <div className="flex flex-col justify-center items-center p-6 bg-white dark:bg-gray-800 shadow-lg rounded-lg">
                    <h2 className="text-2xl font-bold text-lightText dark:text-darkText mb-4">
                        Sign Up to AudioToLanguage
                    </h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                        Secure your account with Google.
                    </p>

                    <button
                        onClick={handleGoogleSignup}
                        className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md hover:bg-blue-500 transition-colors"
                    >
                        <img src={Google} alt="Google Logo" className="w-6 h-6" />
                        Sign up with Google
                    </button>

                    <div className='text-sm text-gray-600 dark:text-gray-400 mb-6 mt-4'>
                        Already have an account?  
                        <span 
                            className='text-blue-600 dark:text-blue-400 underline cursor-pointer hover:text-blue-700 dark:hover:text-blue-300 transition-colors'
                            onClick={() => navigate('/signin')}
                        >
                            Sign In
                        </span>
                    </div>
                </div>

                <div className="flex flex-col justify-center items-center p-6">
                    <img src={Cyber} alt="Cybersecurity" className="w-full max-w-md mb-6"/>
                    <h3 className="text-xl font-semibold text-lightText dark:text-darkText">
                        Stay Safe in the Digital World
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-4 text-center">
                        Anaware protects your data with state-of-the-art security practices. Your account is always encrypted and secure.
                    </p>
                </div>
            </div>
        </div>
    );
};
