class StrategySettings extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            settings: {
                symbol: 'BTC/USDT',
                gridSize: 10,
                gridSpacing: 1,
                lowerPrice: 0,
                upperPrice: 0,
            }
        };
    }

    componentDidMount() {
        this.fetchSettings();
    }

    async fetchSettings() {
        try {
            const response = await fetch('/api/strategy/parameters');
            const data = await response.json();
            this.setState({ settings: data });
        } catch (error) {
            console.error('Error fetching strategy settings:', error);
        }
    }

    handleInputChange = (event) => {
        const { name, value } = event.target;
        this.setState(prevState => ({
            settings: {
                ...prevState.settings,
                [name]: value
            }
        }));
    }

    handleSubmit = async (event) => {
        event.preventDefault();
        try {
            const response = await fetch('/api/strategy/parameters', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.state.settings),
            });
            const data = await response.json();
            if (data.error) {
                console.error('Error updating settings:', data.error);
            } else {
                console.log('Settings updated successfully');
            }
        } catch (error) {
            console.error('Error updating strategy settings:', error);
        }
    }

    render() {
        const { settings } = this.state;
        return (
            <div className="bg-white rounded-lg shadow p-6 mb-8">
                <h2 className="text-xl font-semibold mb-4">Strategy Settings</h2>
                <form onSubmit={this.handleSubmit} className="space-y-4">
                    {Object.entries(settings).map(([key, value]) => (
                        <div key={key}>
                            <label className="block text-sm font-medium text-gray-700">
                                {key}
                            </label>
                            <input
                                type={typeof value === 'number' ? 'number' : 'text'}
                                name={key}
                                value={value}
                                onChange={this.handleInputChange}
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                            />
                        </div>
                    ))}
                    <button
                        type="submit"
                        className="w-full bg-blue-600 text-white rounded-md py-2 hover:bg-blue-700"
                    >
                        Update Settings
                    </button>
                </form>
            </div>
        );
    }
}

// Export for use in other modules
export default StrategySettings;