import React from 'react';
import PropTypes from 'prop-types';

// Debugging log for module loading
console.log('BasicSettings module loaded');

function BasicSettings({ settings = {}, onChange = () => {} }) {
  // Debugging log for component rendering
  console.log('BasicSettings rendered with settings:', settings);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">Symbol</label>
        <input
          type="text"
          value={settings.symbol || ''}
          onChange={(e) => {
            console.log('Symbol changed:', e.target.value);
            onChange('symbol', e.target.value);
          }}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Grid Size</label>
        <input
          type="number"
          value={settings.gridSize || 0}
          onChange={(e) => {
            console.log('Grid Size changed:', e.target.value);
            onChange('gridSize', parseInt(e.target.value, 10));
          }}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Grid Spacing (%)</label>
        <input
          type="number"
          value={settings.gridSpacing || 0}
          onChange={(e) => {
            console.log('Grid Spacing changed:', e.target.value);
            onChange('gridSpacing', parseFloat(e.target.value));
          }}
          step="0.1"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Position Size</label>
        <input
          type="number"
          value={settings.positionSize || 0}
          onChange={(e) => {
            console.log('Position Size changed:', e.target.value);
            onChange('positionSize', parseFloat(e.target.value));
          }}
          step="0.1"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Max Positions</label>
        <input
          type="number"
          value={settings.maxPositions || 0}
          onChange={(e) => {
            console.log('Max Positions changed:', e.target.value);
            onChange('maxPositions', parseInt(e.target.value, 10));
          }}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Use BNB Fees</label>
        <input
          type="checkbox"
          checked={!!settings.useBnbFees}
          onChange={(e) => {
            console.log('Use BNB Fees changed:', e.target.checked);
            onChange('useBnbFees', e.target.checked);
          }}
          className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600"
        />
      </div>
    </div>
  );
}

BasicSettings.propTypes = {
  settings: PropTypes.shape({
    symbol: PropTypes.string,
    gridSize: PropTypes.number,
    gridSpacing: PropTypes.number,
    positionSize: PropTypes.number,
    maxPositions: PropTypes.number,
    useBnbFees: PropTypes.bool
  }),
  onChange: PropTypes.func
};

// Add global window export for legacy support
if (typeof window !== 'undefined') {
  window.BasicSettings = BasicSettings;
}

export default BasicSettings;