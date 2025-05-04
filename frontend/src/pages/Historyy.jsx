import { useState, useEffect } from "react";
import { Appbar } from "../components/Appbar";
import { Grid, List } from "lucide-react";

export const Historyy = () => {
  const [view, setView] = useState("grid");
  const [search, setSearch] = useState("");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
        const token = localStorage.getItem("token");
        
        if (!token) {
            setError("You must be logged in to view history");
            setLoading(false);
            return;
        }
        
        try {
            const response = await fetch("https://my-app.b22023.workers.dev/api/user/history", {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                throw new Error("Failed to fetch history");
            }
            
            const data = await response.json();
            setHistory(data.history || []);
            setLoading(false);
        } catch (error) {
            console.error("Error fetching history:", error);
            setError("Failed to load your scan history");
            setLoading(false);
        }
    };
    
    fetchHistory();
  }, []);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const filteredData = history.filter((item) =>
    item.fileName && item.fileName.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="bg-lightBg dark:bg-darkBg min-h-screen flex flex-col">
      <Appbar />
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-lightText dark:text-darkText">
            History
          </h2>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Total Elements in History: {filteredData.length}
          </span>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-40">
            <p className="text-lg text-gray-600 dark:text-gray-400">Loading your scan history...</p>
          </div>
        ) : error ? (
          <div className="bg-red-100 dark:bg-red-900 p-4 rounded-lg text-red-700 dark:text-red-300">
            {error}
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-6">
              <input
                type="text"
                placeholder="Search history..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="px-4 py-2 dark:text-white w-full md:w-1/3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex space-x-4">
                <button
                  onClick={() => setView("grid")}
                  className={`p-2 rounded-lg shadow-md transition ${
                    view === "grid"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 dark:bg-gray-400"
                  }`}>
                  <Grid size={20} />
                </button>
                <button
                  onClick={() => setView("list")}
                  className={`p-2 rounded-lg shadow-md transition ${
                    view === "list"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 dark:bg-gray-400"
                  }`}>
                  <List size={20} />
                </button>
              </div>
            </div>

            {filteredData.length === 0 ? (
              <div className="text-center p-8">
                <p className="text-lg text-gray-600 dark:text-gray-400">No scan history found.</p>
              </div>
            ) : view === "grid" ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {filteredData.map((item) => (
                  <div
                    key={item.id}
                    className="p-6 bg-white dark:bg-gray-800 shadow-lg rounded-lg cursor-pointer hover:shadow-xl transition"
                  >
                    <h3 className="text-lg font-semibold text-lightText dark:text-darkText">
                      {item.fileName}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                      Malicious: {item.mal === 1 ? "Yes" : "No"}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                      Date: {formatDate(item.Date)}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr>
                    <th className="p-3 bg-white dark:bg-gray-800 text-lightText dark:text-darkText">
                      File/URL
                    </th>
                    <th className="p-3 bg-white dark:bg-gray-800 text-lightText dark:text-darkText">
                      Malicious
                    </th>
                    <th className="p-3 bg-white dark:bg-gray-800 text-lightText dark:text-darkText">
                      Date
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((item) => (
                    <tr
                      key={item.id}
                      className="cursor-pointer bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 shadow-lg rounded-lg transition"
                    >
                      <td className="p-3 text-lightText dark:text-gray-400">{item.fileName}</td>
                      <td className="p-3 text-lightText dark:text-gray-400">{item.mal === 1 ? "Yes" : "No"}</td>
                      <td className="p-3 text-lightText dark:text-gray-400">{formatDate(item.Date)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        )}
      </div>
    </div>
  );
};