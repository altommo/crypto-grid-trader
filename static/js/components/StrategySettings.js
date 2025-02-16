import React, { useState, useEffect } from 'react';
import BasicSettings from './BasicSettings';
import WolfpackSettings from './WolfpackSettings';
import RiskSettings from './RiskSettings';
import TechnicalSettings from './TechnicalSettings';

function StrategySettings() {
    const [activeTab, setActiveTab] = useState('basic');
    const [settings, setSettings] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        try {
            console.log('Fetching strategy parameters...');
            const response = await fetch('/api/strategy/parameters');
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to fetch settings');
            }
            
            const data = await response.json();
            console.log('Settings fetched successfully:', data);
            setSettings(data);
            setLoading(false);
            setError(null);
        } catch (error) {
            console.error('Error fetching settings:', error);
            setError(error.message);
            setLoading(false);
        }
    };

    const handleChange = (section, field, value) => {
        console.log(`Changing ${section}.${field} to:`, value);
        setSettings(prev => ({
            ...prev,
            [section]: {
                ...prev[section],
                [field]: value
            }
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError(null);
        
        try {
            console.log('Submitting settings:', settings);
            const response = await fetch('/api/strategy/parameters', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to save settings');
            }

            const result = await response.json();
            console.log('Settings saved successfully:', result);
            
            alert('Settings saved successfully!');
        } catch (error) {
            console.error('Error saving settings:', error);
            setError(error.message);
            alert(`Error saving settings: ${error.message}`);
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return <div className="text-center py-4">Loading settings...</div>;
    }

    if (error) {
        return (
            <div 
                className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative"
                role="alert"
            >
                <strong className="font-bold">Error: </strong>
                <span className="block sm:inline">{error}</span>
                <button 
                    onClick={fetchSettings} 
                    className="ml-4 bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded"
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow">
            <div className="border-b border-gray-200">
                <nav className="flex space-x-4 px-6 py-4">
                    {['basic', 'wolfpack', 'risk', 'technical'].map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-3 py-2 rounded-md ${
                                activeTab === tab 
                                    ? 'bg-blue-100 text-blue-700' 
                                    : 'text-gray-600 hover:text-gray-800'
                            }`}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)} Settings
                        </button>
                    ))}
                </nav>
            </div>

            <form onSubmit={handleSubmit} className="p-6">
                {activeTab === 'basic' && (
                    <BasicSettings
                        settings={settings.basic}
                        onChange={(field, value) => handleChange('basic', field, value)}
                    />
                )}
                {activeTab === 'wolfpack' && (
                    <WolfpackSettings
                        settings={settings.wolfpack}
                        onChange={(field, value) => handleChange('wolfpack', field, value)}
                    />
                )}
                {activeTab === 'risk' && (
                    <RiskSettings
                        settings={settings.risk}
                        onChange={(field, value) => handleChange('risk', field, value)}
                    />
                )}
                {activeTab === 'technical' && (
                    <TechnicalSettings
                        settings={settings.technical}
                        onChange={(field, value) => handleChange('technical', field, value)}
                    />
                )}

                <div className="mt-6 text-right">
                    <button
                        type="submit"
                        disabled={saving}
                        className={`px-4 py-2 rounded-md text-white ${
                            saving ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'
                        }`}
                    >
                        {saving ? 'Saving...' : 'Save Settings'}
                    </button>
                </div>
            </form>
        </div>
    );
}

export default StrategySettings;