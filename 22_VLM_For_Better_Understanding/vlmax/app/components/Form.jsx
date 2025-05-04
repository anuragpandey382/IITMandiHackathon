"use client";
import { useState, useEffect } from 'react';
import Papa from 'papaparse';
import Folder from '@/ReactBits/Folder/Folder';
import { CiChat1 } from "react-icons/ci";

export default function Form({setModalOpen, setModalUrl, setModalType}) {
  const [files, setFiles] = useState([]);
  const [previewUrls, setPreviewUrls] = useState([]);
  const [visible, setVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [processingResults, setProcessingResults] = useState(null);
  const [selectedTableKey, setSelectedTableKey] = useState("");
  const [csvData, setCsvData] = useState(null);

  const openModal = (url, type) => {
    setModalUrl(url)
    setModalType(type)
    setModalOpen(true)
  }
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(true);
    }, 100);
    
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (processingResults && Object.keys(processingResults).length > 0) {
      setSelectedTableKey(Object.keys(processingResults)[0]);
    }
  }, [processingResults]);

  useEffect(() => {
    if (processingResults && selectedTableKey && processingResults[selectedTableKey]?.csv) {
      const csvUrl = processingResults[selectedTableKey].csv;
      
      fetch(csvUrl)
        .then(response => response.text())
        .then(text => {
          const parsedResults = Papa.parse(text, {
            delimiter: ",",
            skipEmptyLines: true,
            header: false
          });
          
          if (parsedResults.data && parsedResults.data.length > 0) {
            setCsvData(parsedResults.data);
          }
        })
        .catch(error => {
          console.error('Error loading CSV file:', error);
          setCsvData(null);
        });
    } 
    else {
      setCsvData(null);
    }
  }, [processingResults, selectedTableKey]);

  const formatTableKey = (key) => {
    return key
      .split('_')
      .map((part, index) => {
        if (index % 2 === 0) {
          return part.charAt(0).toUpperCase() + part.slice(1);
        }
        return part;
      })
      .join(' ');
  };

  const generatePreview = (file) => {
    return new Promise((resolve) => {
      if (file.type.includes('image')) {
        const fileReader = new FileReader();
        fileReader.onload = () => {
          resolve({ url: fileReader.result, type: 'image', name: file.name });
        };
        fileReader.readAsDataURL(file);
      } 
      else if (file.type === 'application/pdf') {
        resolve({ url: '/pdf-icon.png', type: 'pdf', name: file.name });
      } 
      else {
        resolve({ url: '/file-icon.png', type: 'file', name: file.name });
      }
    });
  };

  const handleFileChange = async (e) => {
    const selectedFiles = Array.from(e.target.files);

    if (selectedFiles.length > 0) {
      const validFiles = selectedFiles.filter(
        file => file.type.includes('image') || file.type === 'application/pdf'
      );
      
      if (validFiles.length > 0) {
        const previews = await Promise.all(validFiles.map(file => generatePreview(file)));
        
        setFiles(prevFiles => [...prevFiles, ...validFiles]);
        setPreviewUrls(prevUrls => [...prevUrls, ...previews]);
        setProcessingResults(null);
      }
    }
    e.target.value = '';
  };

  const handleRemoveFile = (index) => {
    setFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
    setPreviewUrls(prevPreviews => prevPreviews.filter((_, i) => i !== index));
  };

  const handleClearAllFiles = () => {
    setFiles([]);
    setPreviewUrls([]);
    setProcessingResults(null);
  };

  const handleClearProcessingResults = async () => {
    setProcessingResults(null);
    setSelectedTableKey("");
    setCsvData(null);

    const response = await fetch('/api/clean', {
      method: 'GET',
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Failed to clear results');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (files.length > 0) {
        try {
            setIsLoading(true);
            setProcessingResults(null);
            setCsvData(null);

            const formData = new FormData();
            files.forEach(file => {
                formData.append('files', file);
            })

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to upload files');
            }
            setProcessingResults(data.results);
            // console.log(processingResults);

            setFiles([]);
            setPreviewUrls([]);
            e.target.reset();
        }
        catch (error) {
            alert(`Upload failed: ${error.message || "An error occurred"}`);
        }
        finally {
            setIsLoading(false);
        }
    } 
    else {
        alert("Please select an file to upload.");
        return ;
    }
  };

  return (
    <div 
      className={`transition-all duration-700 ease-out ${
        visible 
          ? 'opacity-100 translate-y-0' 
          : 'opacity-0 translate-y-10'
      }`}
    >
      <div className="w-2xl h-2xl bg-zinc-900 rounded-lg shadow-md p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label 
              htmlFor="file-upload" 
              className="block text-sm font-medium text-gray-300"
            >
              Upload Image(s)/PDF
            </label>
            
            <label 
              htmlFor="file-upload" 
              className="group cursor-pointer flex items-center justify-center border-2 border-dashed border-gray-600 rounded-md p-6 hover:border-indigo-500 transition-colors"
            >
              <div className="space-y-1 text-center">
                <div className = 'h-24 mx-14'>
                  <Folder size={0.85} color="#00d8ff" className="custom-folder" />
                </div>
                <div className="flex text-sm text-center justify-center">
                  <span className="relative font-medium text-indigo-600 hover:text-indigo-500">
                    Choose a file
                  </span>
                  <p className="pl-1 text-gray-400">or drag and drop</p>
                </div>
                <p className="text-xs text-gray-500">
                  PNG, JPG, JPEG, PDF
                </p>
              </div>
              <input 
                id="file-upload" 
                name="files" 
                type="file"
                multiple 
                accept="image/*, application/pdf" 
                className="sr-only" 
                onChange={handleFileChange}
              />
            </label>
          </div>

          {previewUrls.length > 0 && (
            <div 
              className="mt-4 transition-all duration-500 ease-out"
              style={{ 
                animation: "fadeIn 0.5s ease-out" 
              }}
            >
                <div className="flex items-center justify-between mb-2"> 
                    <p className="text-sm font-medium text-gray-300 mb-2"> Preview:</p>
                    <button
                        type="button"
                        onClick={handleClearAllFiles}
                        className=" text-gray-300 hover:text-white bg-gray-600 rounded-full w-20 h-7 flex items-center justify-center hover:cursor-pointer"
                        title="Clear All"
                    >
                      {previewUrls.length > 1 ? 'Clear All' : 'Clear'}
                    </button>
                </div>


                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {previewUrls.map((preview, index) => (
                  <div key={index} className="relative bg-gray-800 rounded-md p-2">
                    <div className="relative w-full h-32 rounded-md overflow-hidden flex items-center justify-center">
                      {preview.type === 'image' ? (
                        <img 
                          src={preview.url} 
                          alt={`Preview ${index + 1}`} 
                          className="w-full h-full object-contain"
                        />
                      ) : (
                        <div className="flex flex-col items-center justify-center">
                          <svg className="w-12 h-12 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                          </svg>
                          <span className="text-xs text-gray-300 mt-2">{preview.name}</span>
                        </div>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveFile(index)}
                      className="absolute top-2 right-2 text-gray-300 hover:text-white bg-gray-700 rounded-full w-6 h-6 flex items-center justify-center hover:cursor-pointer"
                      title="Remove file"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div>
            <button
              type="submit"
              className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-indigo-500 disabled:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 hover:cursor-pointer disabled:cursor-default disabled:opacity-50 transition-colors duration-200"
              disabled={files.length === 0 || isLoading}
            >
                {isLoading ? 'Uploading...' : 'Upload Image(s)/PDF'}
            </button>
          </div>
        </form>

        {processingResults && (
          <div className="mt-6 border border-gray-700 rounded-md p-4 relative">
            <div className='flex items-center justify-between'> 
            <h3 className="text-lg font-medium text-gray-300 mb-2">
                Processed Results
              </h3>
              <button
                type="button"
                onClick={handleClearProcessingResults}
                className="text-gray-300 hover:text-white bg-gray-600 rounded-full w-32 h-6 flex items-center justify-center hover:cursor-pointer"
                title="Clear results"
              >
                {Object.keys(processingResults).length > 1 ? 'Clear Results' : 'Clear Result'}
              </button>
            </div>

            {processingResults && Object.keys(processingResults).length > 0 ? (
              <div className="space-y-4">
                <div className="relative">
                  <select
                    value={selectedTableKey}
                    onChange={(e) => setSelectedTableKey(e.target.value)}
                    className="block w-full px-4 py-2 pr-8 bg-gray-800 border border-gray-700 rounded-md text-gray-300 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    {Object.keys(processingResults).map((key) => (
                      <option key={key} value={key}>
                        {formatTableKey(key)}
                      </option>
                    ))}
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-400">
                    <svg className="h-4 w-4 fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                      <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                    </svg>
                  </div>
                </div>

                {selectedTableKey && processingResults[selectedTableKey] && (
                  <div className="border border-gray-700 rounded-md p-3">
                    <div className="flex justify-between items-center mb-3">
                      <h4 className="text-md font-medium text-gray-300">
                        {formatTableKey(selectedTableKey)}
                      </h4>
                    </div>
                    
                    <div className="space-y-6">
                      {processingResults[selectedTableKey].main && (
                        <div className="space-y-2">
                          <h5 className="text-sm font-medium text-gray-300">Table Image:</h5>
                          <div className="bg-gray-800 p-2 rounded-md flex justify-center"
                            onClick = {() => openModal(processingResults[selectedTableKey].main, 'image')}>
                            <img 
                              src={processingResults[selectedTableKey].main} 
                              alt="Table image" 
                              className="max-h-60 object-contain" 
                            />
                          </div>
                        </div>
                      )}

                      {processingResults[selectedTableKey].boxes && (
                        <div className="space-y-2">
                          <h5 className="text-sm font-medium text-gray-300">Boxes Visualization:</h5>
                          <div className="bg-gray-800 p-2 rounded-md flex justify-center" onClick = {() => openModal(processingResults[selectedTableKey].boxes, 'image')}>
                            <img 
                              src={processingResults[selectedTableKey].boxes} 
                              alt="Boxes visualization" 
                              className="max-h-60 object-contain" 
                            />
                          </div>
                        </div>
                      )}

                      {processingResults[selectedTableKey].struct && (
                        <div className="space-y-2">
                          <h5 className="text-sm font-medium text-gray-300">Table Structure:</h5>
                          <div className="bg-gray-800 p-2 rounded-md flex justify-center" onClick = {() => openModal(processingResults[selectedTableKey].struct, 'image')}>
                            <img 
                              src={processingResults[selectedTableKey].struct} 
                              alt="Table structure" 
                              className="max-h-60 object-contain" 
                            />
                          </div>
                        </div>
                      )}
                      
                      {csvData && csvData.length > 0 && (
                        <div className="space-y-2">
                          <div className="flex justify-between items-center">
                            <h5 className="text-sm font-medium text-gray-300">Table Data:</h5>
                            <a 
                              href={processingResults[selectedTableKey].csv} 
                              download
                              className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center"
                            >
                              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                              </svg>
                              Download CSV
                            </a>
                          </div>
                          <div className="bg-gray-800 p-2 rounded-md overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-700">
                              <thead>
                                <tr>
                                  {csvData[0]?.map((header, i) => (
                                    <th 
                                      key={i}
                                      className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider"
                                    >
                                      {header}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-gray-700">
                                {csvData.slice(1).map((row, rowIndex) => (
                                  <tr key={rowIndex}>
                                    {row.map((cell, cellIndex) => (
                                      <td 
                                        key={cellIndex}
                                        className="px-3 py-1.5 text-xs text-gray-300"
                                      >
                                        {cell}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                      
                      {processingResults[selectedTableKey].html && (
                        <div className="space-y-2">
                          <div className="flex justify-between items-center">
                            <h5 className="text-sm font-medium text-gray-300">HTML Preview:</h5>
                            <a 
                              href={processingResults[selectedTableKey].html} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center"
                            >
                              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                              </svg>
                              Open HTML
                            </a>
                          </div>
                          <div className="bg-white rounded-md overflow-hidden h-60">
                            <iframe 
                              src={processingResults[selectedTableKey].html}
                              className="w-full h-full border-0"
                              title="HTML Preview"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                <button
                  onClick={() => window.open(`http://localhost:${window.location.port}/chat`, '_blank')}
                  className="text-gray-300 hover:text-white bg-gray-600 rounded-full w-12 h-12 flex items-center justify-center hover:cursor-pointer mt-2 group"
                >
                  <CiChat1 
                  size = {30}
                  className="transition-transform duration-300 ease-in-out group-hover:scale-125"
                  />
                </button>

              </div>
            ) : (
              <pre className="bg-gray-800 p-3 rounded-md overflow-auto text-sm text-gray-300">
                {JSON.stringify(processingResults, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
      
      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}