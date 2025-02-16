import React from 'react';
import PropTypes from 'prop-types';

function TechnicalSettings({ settings = {}, onChange = () => {} }) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label className="block text-sm font-medium text-gray-700">RSI Period</label>
                <input
                    type="number"
                    value={settings.rsiPeriod || 0}
                    onChange={(e) => onChange('rsiPeriod', parseInt(e.target.value, 10))}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700">Short Trend Period</label>
                <input
                    type="number"
                    value={settings.shortTrendPeriod || 0}
                    onChange={(e) => onChange('shortTrendPeriod', parseInt(e.target.value, 10))}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700">Trend Strength</label>
                <input
                    type="number"
                    value={settings.trendStrength || 0}
                    onChange={(e) => onChange('trendStrength', parseInt(e.target.value, 10))}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700">Use EMAs</label>
                <input
                    type="checkbox"
                    checked={!!settings.useEmas}
                    onChange={(e) => onChange('useEmas', e.target.checked)}
                    className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600"
                />
            </div>
            {settings.useEmas && (
                <>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">EMA 1 Period</label>
                        <input
                            type="number"
                            value={settings.ema1Period || 0}
                            onChange={(e) => onChange('ema1Period', parseInt(e.target.value, 10))}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">EMA 2 Period</label>
                        <input
                            type="number"
                            value={settings.ema2Period || 0}
                            onChange={(e) => onChange('ema2Period', parseInt(e.target.value, 10))}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                        />
                    </div>
                </>
            )}
        </div>
    );
}

TechnicalSettings.propTypes = {
    settings: PropTypes.shape({
        rsiPeriod: PropTypes.number,
        shortTrendPeriod: PropTypes.number,
        trendStrength: PropTypes.number,
        useEmas: PropTypes.bool,
        ema1Period: PropTypes.number,
        ema2Period: PropTypes.number
    }),
    onChange: PropTypes.func
};

export default TechnicalSettings;