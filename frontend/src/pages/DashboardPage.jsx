import { useState, useEffect } from 'react';
import { useUser } from '@clerk/clerk-react';
import Navbar from '../components/Navbar';
import EngagementChart from '../components/EngagementChart';
import { analyticsService } from '../services/apiService';

const DashboardPage = () => {
  const [dateRange, setDateRange] = useState('30');
  const [metrics, setMetrics] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const { isSignedIn } = useUser();

  useEffect(() => {
    const loadDashboardData = async () => {
      if (isSignedIn) {
        setIsLoading(true);
        try {
          // Fetch metrics summary
          const metricsData = await analyticsService.getMetricsSummary();
          
          if (metricsData) {
            // Format metrics for display
            const formattedMetrics = [
              { 
                name: 'Total Engagements', 
                value: `${(metricsData.total_likes + metricsData.total_comments + metricsData.total_shares) / 1000}K`, 
                change: '+12.3%', 
                positive: true 
              },
              { 
                name: 'Avg. Engagement Rate', 
                value: `${metricsData.avg_engagement_rate}%`, 
                change: '+0.7%', 
                positive: true 
              },
              { 
                name: 'Best Post Type', 
                value: metricsData.best_post_type, 
                change: '', 
                positive: true 
              },
              { 
                name: 'Best Posting Time', 
                value: metricsData.best_time_overall, 
                change: '', 
                positive: true 
              },
            ];
            
            setMetrics(formattedMetrics);
          }
          
          // Fetch recommendations
          const recommendationsData = await analyticsService.getRecommendations();
          if (recommendationsData) {
            setRecommendations(recommendationsData);
          }
        } catch (error) {
          console.error('Error loading dashboard data:', error);
        } finally {
          setIsLoading(false);
        }
      }
    };
    
    loadDashboardData();
  }, [isSignedIn, dateRange]);

  const handleDateRangeChange = (e) => {
    setDateRange(e.target.value);
    // This will trigger the useEffect to reload data
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold text-gray-900">Social Media Analytics Dashboard</h1>
          <div className="flex space-x-2">
            <select
              value={dateRange}
              onChange={handleDateRangeChange}
              className="rounded-md border-gray-300 py-2 pl-3 pr-10 text-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
              <option value="365">Last year</option>
            </select>
            <button className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700">
              Export
            </button>
          </div>
        </div>
        
        {isLoading ? (
          // Loading state
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <>
            {/* Metrics Overview */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {metrics.map((metric) => (
                <div key={metric.name} className="bg-white rounded-lg shadow-md p-6">
                  <div className="text-sm font-medium text-gray-500">{metric.name}</div>
                  <div className="mt-1 flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">{metric.value}</div>
                    {metric.change && (
                      <span className={`ml-2 text-sm font-medium ${metric.positive ? 'text-green-600' : 'text-red-600'}`}>
                        {metric.change}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <EngagementChart title="Engagement by Post Type" type="bar" />
              <EngagementChart title="Engagement Trends" type="line" />
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <EngagementChart title="Post Type Distribution" type="pie" />
              <EngagementChart title="Best Posting Times" type="bar" />
            </div>
            
            {/* Recommendations Section */}
            <div className="mt-8 bg-white rounded-lg shadow-md overflow-hidden">
              <div className="px-6 py-4 bg-indigo-50 border-b border-indigo-100">
                <h3 className="text-lg font-medium text-indigo-900">AI Recommendations</h3>
              </div>
              <div className="p-6">
                <ul className="space-y-4">
                  {recommendations.map((recommendation, index) => (
                    <li key={index} className="flex">
                      <div className="mr-3 flex-shrink-0">
                        <svg className="h-6 w-6 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <p className="text-gray-700">{recommendation}</p>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;