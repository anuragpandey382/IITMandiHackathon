'use client';

import React from 'react';

interface CsvViewerProps {
  csvData: string;
}

const CsvViewer: React.FC<CsvViewerProps> = ({ csvData }) => {
  const parseCsv = (csv: string): string[][] => {
    return csv
      .trim()
      .split('\n')
      .map((row) =>
        row
          .trim()
          .split(/[,;<>():]+/)
          .map((cell) => cell.trim())
          .filter(Boolean)
      )
      .filter((row) => row.length > 0);
  };

  const rows = parseCsv(csvData);
  const headers = rows[0] || [];
  const bodyRows = rows.slice(1);

  return (
    <div className="border rounded-lg overflow-auto shadow-inner">
      <table className="w-full caption-bottom text-sm">
        <thead>
          <tr className="bg-gradient-to-r from-[#1E3A8A] to-[#3B82F6] text-white">
            {headers.map((header, idx) => (
              <th key={idx} className="h-12 px-4 text-left align-middle font-medium">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {bodyRows.map((row, rowIdx) => (
            <tr key={rowIdx} className="border-b transition-colors hover:bg-gray-100">
              {row.map((cell, colIdx) => (
                <td key={colIdx} className="p-4 align-middle">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CsvViewer;
