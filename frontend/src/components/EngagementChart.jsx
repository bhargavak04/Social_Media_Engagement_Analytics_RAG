import { useState } from 'react';

// Note: In a real application, you'd use a charting library like Chart.js or Recharts
// This component simulates a chart with a simple UI since we're focusing on structure
const EngagementChart = ({ title, type = 'bar' }) => {
  const [chartType, setChartType] = useState(type);
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">{title}</h3>
        <select
          value={chartType}
          onChange={(e) => setChartType(e.target.value)}
          className="rounded border-gray-300 text-sm"
        >
          <option value="bar">Bar Chart</option>
          <option value="line">Line Chart</option>
          <option value="pie">Pie Chart</option>
        </select>
      </div>
      
      <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
        {chartType === 'bar' && (
          <div className="flex items-end h-48 space-x-4 px-8">
            <div className="flex flex-col items-center">
              <div className="w-12 bg-indigo-500 rounded-t h-32"></div>
              <span className="text-xs mt-1">Reels</span>
            </div>
            <div className="flex flex-col items-center">
              <div className="w-12 bg-indigo-400 rounded-t h-16"></div>
              <span className="text-xs mt-1">Images</span>
            </div>
            <div className="flex flex-col items-center">
              <div className="w-12 bg-indigo-300 rounded-t h-24"></div>
              <span className="text-xs mt-1">Carousels</span>
            </div>
            <div className="flex flex-col items-center">
              <div className="w-12 bg-indigo-200 rounded-t h-20"></div>
              <span className="text-xs mt-1">Videos</span>
            </div>
          </div>
        )}
        
        {chartType === 'line' && (
          <div className="w-full h-48 px-4 relative">
            <div className="absolute inset-0 flex items-center">
              <svg className="w-full h-32" viewBox="0 0 400 100">
                <path
                  d="M 0,80 L 100,30 L 200,60 L 300,10 L 400,50"
                  fill="none"
                  stroke="rgb(79, 70, 229)"
                  strokeWidth="3"
                />
              </svg>
            </div>
          </div>
        )}
        
        {chartType === 'pie' && (
          <div className="w-32 h-32 relative">
            <svg viewBox="0 0 32 32">
              <circle r="16" cx="16" cy="16" fill="rgb(79, 70, 229)" />
              <circle r="16" cx="16" cy="16" fill="transparent" 
                stroke="rgb(129, 140, 248)" strokeWidth="32" 
                strokeDasharray="20 100" />
              <circle r="16" cx="16" cy="16" fill="transparent" 
                stroke="rgb(165, 180, 252)" strokeWidth="32" 
                strokeDasharray="15 100" strokeDashoffset="-20" />
              <circle r="16" cx="16" cy="16" fill="transparent" 
                stroke="rgb(224, 231, 255)" strokeWidth="32" 
                strokeDasharray="10 100" strokeDashoffset="-35" />
            </svg>
          </div>
        )}
      </div>
    </div>
  );
};

export default EngagementChart;
