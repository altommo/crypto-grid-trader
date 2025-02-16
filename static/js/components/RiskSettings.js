import React from 'react';
import PropTypes from 'prop-types';

function RiskSettings({ settings = {}, onChange = () => {} }) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label className="block text-sm font-medium text-gray-700">Stop Loss (%)</label>
                <input
                    type="number"
                    value={settings.stopLoss || 0}
                    onChange={(e) => onChange('stopLoss', parseFloat(e.target.value))}
                    step="0.1"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700">Take Profit (%)</label>
                <input
                    type="number"
                    value={settings.takeProfit || 0}
                    onChange={(e) => onChange('takeProfit', parseFloat(e.target.value))}
                    step="0.1"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700">Minimum Success Rate (%)</label>
                <input
                    type="number"
                    value={settings.minSuccessRate || 0}
                    onChange={(e) => onChange('minSuccessRate', parseFloat(e.target.value))}
                    step="0.1"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700">Minimum Hold Time (seconds)</label>
                <input
                    type="number"
                    value={settings.minHoldTime || 0}
                    onChange={(e) => onChange('minHoldTime', parseInt(e.target.value, 10))}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                />
            </div>
        </div>
    );
}

RiskSettings.propTypes = {
    settings: PropTypes.shape({
        stopLoss: PropTypes.number,
        takeProfit: PropTypes.number,
        minSuccessRate: PropTypes.number,
        minHoldTime: PropTypes.number
    }),
    onChange: PropTypes.func
};

export default RiskSettings;