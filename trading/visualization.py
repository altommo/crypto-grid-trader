import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional
from datetime import datetime

class TradingVisualizer:
    def __init__(self, historical_data: pd.DataFrame, trades: List[Dict]):
        self.data = historical_data
        self.trades = trades

    def create_trading_view(self) -> go.Figure:
        """Create a comprehensive trading view with price, indicators, and trades"""
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=('Price & Trades', 'Indicators', 'Volume'),
            row_heights=[0.5, 0.3, 0.2]
        )

        # Main price chart
        fig.add_trace(
            go.Candlestick(
                x=self.data.index,
                open=self.data['open'],
                high=self.data['high'],
                low=self.data['low'],
                close=self.data['close'],
                name='Price'
            ),
            row=1, col=1
        )

        # Add trades
        for trade in self.trades:
            marker_color = 'green' if trade['action'] == 'BUY' else 'red'
            marker_symbol = 'triangle-up' if trade['action'] == 'BUY' else 'triangle-down'
            
            fig.add_trace(
                go.Scatter(
                    x=[trade['timestamp']],
                    y=[trade['price']],
                    mode='markers',
                    marker=dict(
                        color=marker_color,
                        symbol=marker_symbol,
                        size=12
                    ),
                    name=f"{trade['action']} - {trade['price']:.4f}"
                ),
                row=1, col=1
            )

        # Add RSI
        fig.add_trace(
            go.Scatter(
                x=self.data.index,
                y=self.data['RSI'],
                name='RSI'
            ),
            row=2, col=1
        )

        # Add MACD
        fig.add_trace(
            go.Scatter(
                x=self.data.index,
                y=self.data['MACD'],
                name='MACD'
            ),
            row=2, col=1
        )

        # Add volume
        fig.add_trace(
            go.Bar(
                x=self.data.index,
                y=self.data['volume'],
                name='Volume'
            ),
            row=3, col=1
        )

        # Update layout
        fig.update_layout(
            title='Trading Analysis Dashboard',
            xaxis_rangeslider_visible=False,
            height=800
        )

        return fig

    def create_grid_heatmap(self, grid_levels: List[Dict]) -> go.Figure:
        """Create a heatmap visualization of grid levels and their activity"""
        prices = [level['price'] for level in grid_levels]
        positions = [level['position_size'] for level in grid_levels]

        fig = go.Figure(data=[
            go.Heatmap(
                y=prices,
                z=[positions],
                colorscale='RdYlGn',
                showscale=True
            )
        ])

        fig.update_layout(
            title='Grid Levels Heatmap',
            yaxis_title='Price Levels',
            height=400
        )

        return fig

    def create_performance_dashboard(self, metrics: Dict) -> go.Figure:
        """Create a performance metrics dashboard"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Cumulative PnL',
                'Win Rate Analysis',
                'Drawdown',
                'Trade Distribution'
            )
        )

        # Cumulative PnL
        pnl_data = pd.DataFrame(self.trades)
        fig.add_trace(
            go.Scatter(
                x=pnl_data['timestamp'],
                y=pnl_data['cumulative_pnl'],
                name='Cumulative PnL'
            ),
            row=1, col=1
        )

        # Win Rate Pie Chart
        wins = metrics['win_rate'] * 100
        fig.add_trace(
            go.Pie(
                values=[wins, 100-wins],
                labels=['Wins', 'Losses'],
                name='Win Rate'
            ),
            row=1, col=2
        )

        # Drawdown
        fig.add_trace(
            go.Scatter(
                x=pnl_data['timestamp'],
                y=pnl_data['drawdown'],
                name='Drawdown',
                fill='tozeroy'
            ),
            row=2, col=1
        )

        # Trade PnL Distribution
        fig.add_trace(
            go.Histogram(
                x=pnl_data['pnl'],
                name='PnL Distribution'
            ),
            row=2, col=2
        )

        fig.update_layout(
            height=800,
            title_text='Performance Analysis Dashboard',
            showlegend=True
        )

        return fig

    def export_report(self, filepath: str) -> None:
        """Export a complete HTML trading report"""
        trading_view = self.create_trading_view()
        performance_dashboard = self.create_performance_dashboard({
            'win_rate': len([t for t in self.trades if t['pnl'] > 0]) / len(self.trades)
        })

        # Combine plots into a single HTML file
        with open(filepath, 'w') as f:
            f.write(f"""
            <html>
            <head>
                <title>Trading Report</title>
            </head>
            <body>
                <h1>Trading Analysis Report</h1>
                <div>{trading_view.to_html()}</div>
                <div>{performance_dashboard.to_html()}</div>
            </body>
            </html>
            """)
