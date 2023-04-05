# Stock Options Analyzer
By Jesse Gordon 

This Python script allows you to gather stock option data from Stocktrack, store the data, and analyze it through 3D graphs and GIFs. 

## Dependencies

The script requires the following Python packages:

- requests
- pandas
- json
- numpy
- matplotlib
- datetime
- plotly
- scipy
- os
- imageio

## Usage

1. Import the required modules and the `OptionData` class from the script.
2. Initialize the `OptionData` class by providing a list of tickers and a cookie string from Stocktrack.
3. Call the `run_all_tickers()` method to collect and store options data for all tickers.
4. Save the data to an Excel file using the `save_all_as_excel()` method.
5. Analyze the data with the following methods:

   - `plot_volatility_surface()`: Generates a 3D plot of the implied volatility surface for a specific ticker.
   - `plot_volatility_smile()`: Generates a 2D plot of the implied volatility smile for a specific ticker and expiry date.
   - `find_best_option()`: Finds the best option based on the highest price difference between the market price and the expected return.
   - `gif_moving_volatility_smile()`: Creates a GIF of the moving implied volatility smile for a list of tickers.

## Example

```python
from stock_options_analyzer import OptionData

tickers = ["AAPL", "GOOGL"]
cookie = "your_cookie_string_here"

option_data = OptionData(tickers, cookie)
option_data.run_all_tickers()
option_data.save_all_as_excel()
option_data.plot_volatility_surface("AAPL")
option_data.plot_volatility_smile("GOOGL")
best_option = option_data.find_best_option()
print(f"The best option is: {best_option}")
option_data.gif_moving_volatility_smile(tickers)
``` 

## Disclaimer
This script is for educational purposes only. Any financial decisions made based on the output of this script are at your own risk. Consult with a professional financial advisor before making any financial decisions.

## License
This project is licensed under the MIT License. See LICENSE for more details.
