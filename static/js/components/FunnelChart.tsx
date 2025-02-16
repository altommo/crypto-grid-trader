import React from 'react';
import PropTypes from 'prop-types';

// Simplified custom Funnel Chart without Recharts animation
const FunnelChart = ({ data }) => {
  // Validate and prepare data
  if (!data || data.length === 0) {
    return <div>No data available</div>;
  }

  // Calculate maximum value for scaling
  const maxValue = Math.max(...data.map(item => item.value));

  // Color palette
  const colors = [
    '#3182bd', '#6baed6', '#9ecae1', '#c6dbef', '#e6f2ff'
  ];

  return (
    <div className="funnel-chart" style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      width: '100%', 
      padding: '20px' 
    }}>
      <h3>Funnel Visualization</h3>
      {data.map((item, index) => {
        // Calculate width based on value
        const widthPercentage = (item.value / maxValue) * 100;
        
        return (
          <div 
            key={item.name} 
            style={{
              width: `${widthPercentage}%`,
              backgroundColor: colors[index % colors.length],
              color: 'white',
              padding: '10px',
              margin: '5px 0',
              textAlign: 'center',
              transition: 'width 0.3s ease',
              borderRadius: '5px'
            }}
          >
            {item.name}: {item.value}
          </div>
        );
      })}
    </div>
  );
};

FunnelChart.propTypes = {
  data: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      value: PropTypes.number.isRequired
    })
  ).isRequired
};

// Add global window export for legacy support
if (typeof window !== 'undefined') {
  window.FunnelChart = FunnelChart;
}

export default FunnelChart;