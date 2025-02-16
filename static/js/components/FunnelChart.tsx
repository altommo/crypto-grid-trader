import React from 'react';
import PropTypes from 'prop-types';
import { 
  Funnel, 
  FunnelChart as RechartsFunnelChart, 
  ResponsiveContainer, 
  Tooltip, 
  LabelList,
  Cell
} from 'recharts';

interface FunnelChartProps {
  data: Array<{
    name: string;
    value: number;
    fill?: string;
  }>;
  width?: number | string;
  height?: number | string;
}

const FunnelChart: React.FC<FunnelChartProps> = ({ 
  data, 
  width = '100%', 
  height = 400 
}) => {
  // Ensure data exists and is not empty
  if (!data || data.length === 0) {
    return <div>No data available</div>;
  }

  return (
    <ResponsiveContainer width={width} height={height}>
      <RechartsFunnelChart>
        <Funnel
          data={data}
          dataKey="value"
          labelKey="name"
          fill="#8884d8"
        >
          <LabelList 
            position="right" 
            fill="#000" 
            stroke="none" 
          />
          {data.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={entry.fill || `#${Math.floor(Math.random()*16777215).toString(16)}`} 
            />
          ))}
        </Funnel>
        <Tooltip />
      </RechartsFunnelChart>
    </ResponsiveContainer>
  );
};

FunnelChart.propTypes = {
  data: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      value: PropTypes.number.isRequired,
      fill: PropTypes.string
    })
  ).isRequired,
  width: PropTypes.oneOfType([
    PropTypes.number,
    PropTypes.string
  ]),
  height: PropTypes.oneOfType([
    PropTypes.number,
    PropTypes.string
  ])
};

export default FunnelChart;