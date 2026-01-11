import React from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  Legend, ResponsiveContainer, ReferenceLine, Area
} from 'recharts';
import Card from './layout/Card';
import '../styles/components/EmotionTimeline.css';

function EmotionTimeline({ wpsData }) {
  if (!wpsData || wpsData.length === 0) {
    return (
      <Card className="emotion-timeline-card">
        <p>No speaking rate data available.</p>
      </Card>
    );
  }
  
  const prepareWpsData = () => {
    return wpsData.map((wp) => ({
      timeInSeconds: wp.Time,
      wps: wp.WPS,
      optimalMin: 2.0,
      optimalMax: 3.0
    }));
  };
  
  const chartData = prepareWpsData();
  
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const minutes = Math.floor(data.timeInSeconds / 60);
      const seconds = data.timeInSeconds % 60;
      const timeString = `${minutes}:${String(seconds).padStart(2, '0')}`;
      
      return (
        <div className="custom-tooltip">
          <p className="label">{`Time: ${timeString}`}</p>
          {data.wps !== null && data.wps !== undefined && (
            <p className="wps">
              {`Speaking Rate: ${data.wps.toFixed(2)} WPS`}
              {data.wps > 3.0 && " (too fast)"}
              {data.wps < 2.0 && " (too slow)"}
            </p>
          )}
        </div>
      );
    }
    return null;
  };
  
  return (
    <Card className="emotion-timeline-card">
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="timeInSeconds"
              type="number"
              domain={['dataMin', 'dataMax']}
              tickFormatter={(value) => `${Math.floor(value / 60)}:${String(value % 60).padStart(2, '0')}`}
              label={{ value: 'Time (MM:SS)', position: 'insideBottom', offset: -5 }}
            />
            <YAxis domain={[0, 4]} label={{ value: 'WPS', angle: -90, position: 'insideLeft' }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="wps"
              stroke="#82ca9d"
              name="Words Per Second"
              dot={{ fill: '#82ca9d', r: 5 }}
              isAnimationActive={false}
            />
            <ReferenceLine y={2.0} stroke="rgba(0, 255, 0, 0.5)" strokeDasharray="3 3" label={{ value: 'Min Optimal', position: 'insideLeft' }} />
            <ReferenceLine y={3.0} stroke="rgba(255, 0, 0, 0.5)" strokeDasharray="3 3" label={{ value: 'Max Optimal', position: 'insideLeft' }} />
            <Area 
              dataKey="optimalMin"
              stroke="transparent"
              fill="rgba(0, 255, 0, 0.1)"
              activeDot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

export default EmotionTimeline;
