import React, { useState, useEffect, useCallback } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, ReferenceLine
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
        <div className="timeline-content">
          <Loading />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="improvement-timeline-card">
        <div className="timeline-content">
          <div className="error-message">{error}</div>
        </div>
      </Card>
    );
  }

  if (analyses.length === 0) {
    return (
      <Card className="improvement-timeline-card">
        <div className="timeline-content">
          <h3 className="timeline-title">Improvement Timeline</h3>
          <p className="no-data-message">
            No analysis data available yet. Upload your first video to start tracking your progress!
          </p>
        </div>
      </Card>
    );
  }

  // Calculate average clarity score for reference line
  const avgClarity = analyses.reduce((sum, a) => sum + (a.clarity_score || 0), 0) / analyses.length;

  return (
    <Card className="improvement-timeline-card">
      <div className="timeline-content">
        <div className="timeline-header">
          <h3 className="timeline-title">Improvement Timeline</h3>
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
        
        <div className="chart-wrapper">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart 
              data={chartData} 
              margin={{ 
                top: 10, 
                right: 20, 
                left: 0, 
                bottom: 60 
              }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis 
                dataKey="date"
                tick={{ fontSize: 11, fill: '#666' }}
                angle={-45}
                textAnchor="end"
                height={80}
                interval={0}
                dy={10}
              />
              <YAxis 
                domain={[0, 100]}
                tick={{ fontSize: 11, fill: '#666' }}
                width={50}
                label={{ 
                  value: 'Clarity (%)', 
                  angle: -90, 
                  position: 'insideLeft',
                  style: { textAnchor: 'middle', fontSize: '11px', fill: '#666' },
                  offset: 5
                }}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine 
                y={avgClarity} 
                stroke="#8884d8" 
                strokeDasharray="3 3" 
                label={{ 
                  value: `Avg: ${avgClarity.toFixed(0)}%`, 
                  position: 'right',
                  style: { fontSize: '11px', fill: '#8884d8' }
                }}
              />
              <Line
                type="monotone"
                dataKey="clarityScore"
                stroke="#4CAF50"
                strokeWidth={2}
                name="Clarity Score"
                dot={{ fill: '#4CAF50', r: 4 }}
                activeDot={{ r: 6 }}
                isAnimationActive={true}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        <div className="timeline-stats">
          <div className="stat-item">
            <span className="stat-label">Current</span>
            <span className="stat-value">{analyses[analyses.length - 1]?.clarity_score.toFixed(0) || 'N/A'}%</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Average</span>
            <span className="stat-value">{avgClarity.toFixed(0)}%</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Best</span>
            <span className="stat-value">{Math.max(...analyses.map(a => a.clarity_score || 0)).toFixed(0)}%</span>
          </div>
        </div>
      </div>
    </Card>
  );
}

export default ImprovementTimeline;
