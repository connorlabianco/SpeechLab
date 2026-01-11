import React, { useState, useEffect, useCallback } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  Legend, ResponsiveContainer, ReferenceLine
} from 'recharts';
import { getAnalyses } from '../services/api';
import Card from './layout/Card';
import Loading from './layout/Loading';
import '../styles/components/ImprovementTimeline.css';

function ImprovementTimeline({ onFilterChange }) {
  const [analyses, setAnalyses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterCount, setFilterCount] = useState(10);
  const [error, setError] = useState(null);

  const fetchAnalyses = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getAnalyses();
      const analysesData = response.analyses || [];
      
      // Sort by date (most recent first) and filter by count
      const sortedAnalyses = analysesData
        .filter(analysis => analysis.clarity_score !== null && analysis.clarity_score !== undefined)
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, filterCount)
        .reverse(); // Reverse to show oldest to newest for timeline
      
      setAnalyses(sortedAnalyses);
    } catch (err) {
      console.error('Error fetching analyses:', err);
      setError('Failed to load analysis history.');
    } finally {
      setIsLoading(false);
    }
  }, [filterCount]);

  useEffect(() => {
    fetchAnalyses();
  }, [fetchAnalyses]);

  const prepareChartData = () => {
    return analyses.map((analysis, index) => ({
      index: index + 1,
      date: new Date(analysis.created_at).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      }),
      clarityScore: analysis.clarity_score,
      fullDate: new Date(analysis.created_at)
    }));
  };

  const chartData = prepareChartData();

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="improvement-tooltip">
          <p className="tooltip-label">{`Date: ${data.fullDate.toLocaleDateString()}`}</p>
          <p className="tooltip-value">
            {`Clarity Score: ${data.clarityScore.toFixed(0)}%`}
          </p>
        </div>
      );
    }
    return null;
  };

  if (isLoading) {
    return (
      <Card className="improvement-timeline-card">
        <Loading />
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="improvement-timeline-card">
        <div className="error-message">{error}</div>
      </Card>
    );
  }

  if (analyses.length === 0) {
    return (
      <Card className="improvement-timeline-card">
        <h3>Improvement Timeline</h3>
        <p className="no-data-message">
          No analysis data available yet. Upload your first video to start tracking your progress!
        </p>
      </Card>
    );
  }

  // Calculate average clarity score for reference line
  const avgClarity = analyses.reduce((sum, a) => sum + (a.clarity_score || 0), 0) / analyses.length;

  return (
    <Card className="improvement-timeline-card">
      <div className="timeline-header">
        <h3>Improvement Timeline</h3>
        <div className="filter-controls">
          <label htmlFor="filter-count">Show last:</label>
          <select 
            id="filter-count"
            value={filterCount} 
            onChange={(e) => {
              const newCount = Number(e.target.value);
              setFilterCount(newCount);
              if (onFilterChange) {
                onFilterChange(newCount);
              }
            }}
            className="filter-select"
          >
            <option value={5}>5 speeches</option>
            <option value={10}>10 speeches</option>
            <option value={15}>15 speeches</option>
          </select>
        </div>
      </div>
      
      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis 
              dataKey="date"
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis 
              domain={[0, 100]}
              label={{ value: 'Clarity Score (%)', angle: -90, position: 'insideLeft' }}
              tick={{ fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <ReferenceLine 
              y={avgClarity} 
              stroke="#8884d8" 
              strokeDasharray="3 3" 
              label={{ value: `Avg: ${avgClarity.toFixed(0)}%`, position: 'right' }}
            />
            <Line
              type="monotone"
              dataKey="clarityScore"
              stroke="#4CAF50"
              strokeWidth={2}
              name="Clarity Score"
              dot={{ fill: '#4CAF50', r: 5 }}
              activeDot={{ r: 7 }}
              isAnimationActive={true}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      <div className="timeline-stats">
        <div className="stat-item">
          <span className="stat-label">Current:</span>
          <span className="stat-value">{analyses[analyses.length - 1]?.clarity_score.toFixed(0) || 'N/A'}%</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Average:</span>
          <span className="stat-value">{avgClarity.toFixed(0)}%</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Best:</span>
          <span className="stat-value">{Math.max(...analyses.map(a => a.clarity_score || 0)).toFixed(0)}%</span>
        </div>
      </div>
    </Card>
  );
}

export default ImprovementTimeline;
