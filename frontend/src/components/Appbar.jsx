import { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Moon, Sun, History, UserCircle, X } from "lucide-react";
import ABC from '../assets/abc.png'; 

export const Appbar = () => {
  const [darkMode, setDarkMode] = useState(
    localStorage.getItem("theme") === "dark"
  );
  const [userDetails, setUserDetails] = useState(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [showAlert, setShowAlert] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

  // Handle clicks outside dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isDropdownOpen && dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isDropdownOpen]);

  // Extract token from query parameters
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const jwtToken = urlParams.get("jwt");
    
    if (jwtToken) {
      localStorage.setItem("token", jwtToken);
      navigate("/");
    }
  }, [location, navigate]);

  const getRandomColor = () => {
    const colors = ['bg-blue-600', 'bg-green-600', 'bg-purple-600', 'bg-red-600', 'bg-yellow-600'];
    return colors[Math.floor(Math.random() * colors.length)];
  };

  const checkToken = () => {
    const token = localStorage.getItem("token");
    
    if (token) {
      try {
        const tokenParts = token.split(".");
        if (tokenParts.length === 3) {
          const decodedPayload = JSON.parse(atob(tokenParts[1]));
          setUserDetails({
            email: decodedPayload.email || 'user@example.com',
            avatarColor: getRandomColor()
          });
        }
      } catch (error) {
        console.error("Error decoding JWT:", error);
        setUserDetails(null);
      }
    } else {
      setUserDetails(null);
    }
  };

  useEffect(() => {
    checkToken();
    window.addEventListener("storage", checkToken);
    return () => {
      window.removeEventListener("storage", checkToken);
    };
  }, []);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [darkMode]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    setUserDetails(null);
    setIsDropdownOpen(false);
    navigate("/signin");
  };

  const handleHistoryClick = () => {
    if (!userDetails) {
      setShowAlert(true);
      setTimeout(() => {
        setShowAlert(false);
        navigate("/signin");
      }, 2000);
    } else {
      navigate("/history");
    }
  };

  return (
    <>
      {/* ✅ Custom Alert */}
      {showAlert && (
        <div className="fixed top-4 right-4 z-50 bg-red-100 dark:bg-red-900 border border-red-300 dark:border-red-700 p-4 rounded-lg shadow-lg flex items-center">
          <span className="text-red-800 dark:text-red-200 text-sm">
            Please sign in to access history.
          </span>
          <button onClick={() => setShowAlert(false)} className="ml-4 text-red-800 dark:text-red-200">
            <X size={18} />
          </button>
        </div>
      )}
      
      <nav className="flex items-center p-4 shadow-md bg-lightBg dark:bg-darkBg">
        <img src={ABC} className="w-8 h-8"/>
        <h2 onClick={() => navigate("/")} className="text-2xl font-bold text-lightText dark:text-darkText cursor-pointer pl-4 ">
          AudioToLang
        </h2>

        <div className="flex items-center gap-4">
          
       

          <div className="px-96"></div>
          <div className="px-40"></div>
          <div className="h-5 w-[1px] bg-gray-400 dark:bg-gray-600"></div>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-1 rounded-full bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            {darkMode ? <Sun className="text-yellow-400" /> : <Moon />}
          </button>

          <div className="h-5 w-[1px] bg-gray-400 dark:bg-gray-600"></div>

          {userDetails ? (
            <div className="relative" ref={dropdownRef}>
              <button 
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="flex items-center gap-2 px-3 py-1 rounded-full bg-gray-200 dark:bg-gray-700 text-sm font-medium"
              >
                <div className={`w-8 h-8 rounded-full ${userDetails.avatarColor} flex items-center justify-center`}>
                  <span className="text-white text-lg font-medium">
                    {userDetails.email.charAt(0).toUpperCase()}
                  </span>
                </div>
                <span className="text-gray-700 dark:text-gray-300">
                  {userDetails.email}
                </span>
              </button>
              {isDropdownOpen && (
                <div className="absolute right-0 bg-white dark:bg-gray-800 text-black dark:text-white shadow-lg rounded-md mt-2 w-full z-50">
                  <button 
                    onClick={handleLogout} 
                    className="px-4 py-2 w-full text-left hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
            </>
          )}
        </div>
      </nav>
    </>
  );
};
