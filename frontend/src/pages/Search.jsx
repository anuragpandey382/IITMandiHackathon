import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Appbar } from "../components/Appbar";

const SecurityVendorRow = ({ vendor, result }) => {
  const isClean = result?.category === "harmless" && result?.result === "clean";
  const status = result?.category || "undetected";
  
  return (
    <div className="flex items-center justify-between py-3 px-4 border-b border-gray-100 dark:border-gray-700">
      <div className="text-sm text-gray-900 dark:text-gray-100">{vendor}</div>
      <div className="flex items-center gap-2">
        <svg 
          className={`w-4 h-4 ${isClean ? 'text-green-500' : 'text-gray-400'}`} 
          viewBox="0 0 20 20" 
          fill="currentColor"
        >
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
      </div>
    </div>
  );
};

// New component for displaying file analysis results
const FileAnalysisResult = ({ fileData }) => {
  const { benign_probability, malicious_probability, confidence, prediction } = fileData;
  
  // Convert probabilities to percentages
  const benignPercent = (benign_probability * 100).toFixed(2);
  const maliciousPercent = (malicious_probability * 100).toFixed(2);
  const confidencePercent = (confidence * 100).toFixed(2);
  
  // Determine status color
  const isBenign = prediction === 'benign';
  const statusColor = isBenign ? 'text-green-500' : 'text-red-500';
  const bgColor = isBenign ? 'bg-green-100 dark:bg-green-900' : 'bg-red-100 dark:bg-red-900';
  const borderColor = isBenign ? 'border-green-200 dark:border-green-800' : 'border-red-200 dark:border-red-800';
  
  return (
    <div className="p-6">
      {/* Status Badge */}
      <div className={`inline-flex items-center px-4 py-2 rounded-full ${bgColor} ${statusColor} ${borderColor} border mb-6`}>
        <svg className="w-5 h-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
          {isBenign ? (
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          ) : (
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          )}
        </svg>
        <span className="font-medium">
          {isBenign ? 'File appears to be safe' : 'File may be malicious'}
        </span>
      </div>

      {/* Probability Gauges */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium mb-3 dark:text-white">Analysis Result</h3>
          <div className="space-y-6">
            {/* Benign Probability */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-green-600 dark:text-green-400">Benign Probability</span>
                <span className="text-sm font-medium text-green-600 dark:text-green-400">{benignPercent}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
                <div className="bg-green-500 h-2.5 rounded-full" style={{ width: `${benignPercent}%` }}></div>
              </div>
            </div>
            
            {/* Malicious Probability */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-red-600 dark:text-red-400">Malicious Probability</span>
                <span className="text-sm font-medium text-red-600 dark:text-red-400">{maliciousPercent}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
                <div className="bg-red-500 h-2.5 rounded-full" style={{ width: `${maliciousPercent}%` }}></div>
              </div>
            </div>
            
            {/* Confidence */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-blue-600 dark:text-blue-400">Confidence Score</span>
                <span className="text-sm font-medium text-blue-600 dark:text-blue-400">{confidencePercent}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
                <div className="bg-blue-500 h-2.5 rounded-full" style={{ width: `${confidencePercent}%` }}></div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium mb-3 dark:text-white">About This Analysis</h3>
          <div className="text-gray-600 dark:text-gray-300 space-y-3">
            <p>
              This file has been analyzed using Anaware's local machine learning model, 
              which examines file characteristics to determine if it's potentially malicious.
            </p>
            <p>
              <span className="font-medium">Prediction:</span> 
              <span className={statusColor}> {prediction.charAt(0).toUpperCase() + prediction.slice(1)}</span>
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
              Note: This is a preliminary analysis. For comprehensive security assessment, 
              consider submitting suspicious files to multiple scanning engines.
            </p>
          </div>
        </div>
      </div>
      
      {/* Recommendation Section */}
      <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-100 dark:border-blue-800">
        <h3 className="text-lg font-medium mb-2 text-blue-700 dark:text-blue-300">
          Recommendations
        </h3>
        <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 space-y-2">
          <li>
            {isBenign 
              ? "While this file appears safe, always exercise caution when running unknown files."
              : "This file shows suspicious characteristics. We recommend not executing it."}
          </li>
          <li>Keep your antivirus software up to date for ongoing protection.</li>
          <li>Consider submitting suspicious files to additional security vendors for thorough analysis.</li>
        </ul>
      </div>
    </div>
  );
};

export const Search = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('DETECTION');
  const [scanData, setScanData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isFileAnalysis, setIsFileAnalysis] = useState(false);
  
  useEffect(() => {
    // Retrieve scan data from sessionStorage when component mounts
    const storedData = sessionStorage.getItem('scanData');
    if (storedData) {
      const parsedData = JSON.parse(storedData);
      setScanData(parsedData);
      
      // Check if this is file analysis data (has benign_probability field)
      setIsFileAnalysis(parsedData.hasOwnProperty('benign_probability'));
    } else {
      // Redirect back to dashboard if no scan data is found
      navigate('/');
    }
    setLoading(false);
  }, [navigate]);

  if (loading) {
    return (
      <div className="bg-gray-50 dark:bg-gray-900 min-h-screen flex flex-col">
        <Appbar />
        <div className="flex items-center justify-center flex-grow">
          <div className="text-blue-600 text-xl">Loading results...</div>
        </div>
      </div>
    );
  }

  if (!scanData) {
    return (
      <div className="bg-gray-50 dark:bg-gray-900 min-h-screen flex flex-col">
        <Appbar />
        <div className="flex items-center justify-center flex-grow">
          <div className="text-red-600 text-xl">No scan data found. Please return to the dashboard and try again.</div>
        </div>
      </div>
    );
  }
  
  // Handle both URL/search and file analysis formats
  let attributes, analysisResults, stats, type, identifier, lastAnalysisDate, score, totalVendors;
  
  if (!isFileAnalysis) {
    // Process URL or search data
    attributes = scanData?.data?.[0]?.attributes || {};
    analysisResults = attributes?.last_analysis_results || {};
    stats = attributes?.last_analysis_stats || {};
    
    // Determine the type of data and identifier based on response
    type = attributes.url ? 'URL' : attributes.type || 'Unknown';
    identifier = attributes.url || attributes.id || 'N/A';
    lastAnalysisDate = attributes.last_analysis_date;
    score = stats.malicious || 0;
    totalVendors = Object.values(stats).reduce((a, b) => a + b, 0);
  } else {
    // Process file analysis data
    type = 'File';
    identifier = sessionStorage.getItem('fileName') || 'Uploaded File';
    score = scanData.prediction === 'benign' ? 0 : 1;
    totalVendors = 1; // Only our analysis for files
  }

  const formatDate = (timestamp) => {
    if (!timestamp) return '';
    return new Date(timestamp * 1000).toLocaleString();
  };

  const handleNewScan = () => {
    // Clear the stored scan data and redirect to dashboard
    sessionStorage.removeItem('scanData');
    sessionStorage.removeItem('fileName');
    navigate('/');
  };

  // Determine score color (green for 0, red for > 0)
  const scoreColor = score > 0 ? 'border-red-500' : 'border-green-500'; 
  const scoreTextColor = score > 0 ? 'text-red-600' : 'text-green-600';

  return (
    <div className="bg-gray-50 dark:bg-gray-900 min-h-screen flex flex-col">
      <Appbar />
      
      <div className="max-w-[1400px] mx-auto w-full px-4 py-6">
        <div className="mb-4">
          <button 
            onClick={handleNewScan}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            New Scan
          </button>
        </div>
        
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Score Circle */}
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm w-full sm:w-32 mx-auto lg:mx-0">
            <div className="relative">
              <div className={`w-16 h-16 mx-auto rounded-full border-4 ${scoreColor} flex items-center justify-center`}>
                <span className="text-2xl dark:text-gray-200 font-semibold">{score}</span>
              </div>
              <div className="text-center mt-2 text-xs text-gray-600 dark:text-gray-400">
                Detection<br />Score
                <span className="text-xs text-gray-400">/{totalVendors}</span>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
            <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-t-lg flex flex-wrap gap-2 justify-between">
              <div className={`flex items-center gap-2 ${scoreTextColor} dark:${scoreTextColor}`}>
                <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>
                  {score === 0 
                    ? `No security vendors flagged this ${type} as malicious`
                    : `${score} security vendors flagged this ${type} as malicious`}
                </span>
              </div>
            </div>

            <div className="p-3">
              <div className="text-sm font-mono text-gray-600 dark:text-gray-400 break-all">
                {identifier}
              </div>
              {!isFileAnalysis && (
                <div className="mt-1 text-sm text-gray-500">
                  Last analyzed: {formatDate(lastAnalysisDate)}
                </div>
              )}
              {!isFileAnalysis && attributes.reputation !== undefined && (
                <div className="mt-1 text-sm text-gray-500">
                  Reputation Score: {attributes.reputation}
                </div>
              )}
            </div>

            <div className="border-t dark:border-gray-700">
              {isFileAnalysis ? (
                // File Analysis View
                <div className="flex border-b dark:border-gray-700">
                  {['DETECTION', 'DETAILS'].map((tab) => (
                    <button
                      key={tab}
                      className={`px-6 py-2 text-sm font-medium ${
                        activeTab === tab
                          ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400'
                          : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                      }`}
                      onClick={() => setActiveTab(tab)}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              ) : (
                // URL/Search Analysis View
                <div className="flex border-b dark:border-gray-700">
                  {['DETECTION', 'DETAILS'].map((tab) => (
                    <button
                      key={tab}
                      className={`px-6 py-2 text-sm font-medium ${
                        activeTab === tab
                          ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400'
                          : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                      }`}
                      onClick={() => setActiveTab(tab)}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              )}

              <div className="p-4">
                {isFileAnalysis ? (
                  // File Analysis Content
                  <>
                    {activeTab === 'DETECTION' && (
                      <FileAnalysisResult fileData={scanData} />
                    )}
                    
                    {activeTab === 'DETAILS' && (
                      <div className="flex flex-col items-center justify-center py-10 text-center">
                        <svg className="w-16 h-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                        <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Detailed Analysis Not Available
                        </h3>
                        <p className="text-gray-500 dark:text-gray-400 max-w-md">
                          Detailed analysis is only available for URLs and network indicators. 
                          For files, we provide a machine learning-based assessment of potential threats.
                        </p>
                      </div>
                    )}
                  </>
                ) : (
                  // URL/Search Analysis Content
                  <>
                    {activeTab === 'DETECTION' && (
                      <div className="overflow-x-auto">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-sm dark:text-white font-medium flex items-center gap-2">
                            Security vendors' analysis
                          </h3>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                          {Object.entries(analysisResults).map(([vendor, result], index) => (
                            <SecurityVendorRow 
                              key={index}
                              vendor={vendor}
                              result={result}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {activeTab === 'DETAILS' && (
                      <div className="text-sm dark:bg-gray-900 dark:text-gray-200 p-4 rounded-lg">
                        <h3 className="font-medium mb-4">Analysis Statistics</h3>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                          {Object.entries(stats).map(([key, value]) => (
                            <div key={key}>
                              <div className="text-gray-500 dark:text-gray-400 capitalize">{key}</div>
                              <div className="dark:text-gray-300">{value}</div>
                            </div>
                          ))}
                        </div>
                        {attributes.categories && (
                          <div className="mt-6">
                            <h3 className="font-medium mb-2">Categories</h3>
                            <div className="flex flex-wrap gap-2">
                              {Object.entries(attributes.categories).map(([provider, category]) => (
                                <div key={provider} className="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-xs">
                                  {category}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};