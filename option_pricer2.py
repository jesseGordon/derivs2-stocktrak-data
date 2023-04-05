import requests
import pandas as pd
import json
import numpy as np
import matplotlib.pyplot as plt
import datetime
import plotly.express as px
from scipy.stats import norm
import os
import imageio


class OptionData:
    def __init__(self, tickers, cookie):
        self.tickers = tickers
        self.cookie = cookie
        self.data_all = pd.DataFrame()
        self.filename = "all_options_2.xlsx"
    
    def run_all_tickers(self):
        for ticker in self.tickers:
            data_ticker = self.get_option_data(ticker)
            if data_ticker is not False:
                self.data_all = self.data_all.append(data_ticker)
            else:
                print("Error getting data for " + ticker)
        print(self.data_all)
    
    def get_underlying_price(self, ticker):

        url = "https://app.quotemedia.com/datatool/getEnhancedQuotes.json"

        querystring = {"symbols": ticker, "greek":"true","timezone":"true","afterhours":"true","premarket":"true","currencyInd":"true","countryInd":"true","marketstatus":"true","chfill":"ee69C1D1","chfill2":"69C1D1","chln":"69C1D1","chxyc":"5F6B6E","newslang":"","token":"caa04741220d22b9b5fd9a65d1c687bfa2a8bde9ba5c3ad99619067447a4f9e2"}

        payload = ""
        headers = {
            "cookie": self.cookie,
            "authority": "app.quotemedia.com",
            "accept": "*/*",
            "accept-language": "en",
            "origin": "https://monash.stocktrak.com",
            "referer": "https://monash.stocktrak.com/",
            "sec-ch-ua": "^\^Google",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "^\^Windows^^",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        }

        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

        data = response.json()
        # Check if data is valid and contains data["results"]["quote"][0]["pricedata"]["last"]
        if "results" not in data or "quote" not in data["results"] or len(data["results"]["quote"]) == 0 or "pricedata" not in data["results"]["quote"][0] or "last" not in data["results"]["quote"][0]["pricedata"]:
            return False
        
        current_price = data["results"]["quote"][0]["pricedata"]["last"]
        return current_price


    def get_option_data(self, ticker):
        underlying_price = self.get_underlying_price(ticker)
        if underlying_price == False:
            return False
        
        url = "https://app.quotemedia.com/datatool/getOptionQuotes.json"

        querystring = {"symbol": ticker,"greeks":"true","expireDays":"true","inclExpired":"false","strike": underlying_price,"strikeLimit":"40","money":"All","adjOptions":"true","groupDate":"true","callput":"group","optionSize":"all","token":"19e4db133f62ca9cf5f80b290eae16e0e71df9a316e5f632bf51c1efef39b48f"}

        payload = ""
        headers = {
            "cookie": self.cookie,
            "authority": "app.quotemedia.com",
            "accept": "*/*",
            "accept-language": "en",
            "origin": "https://monash.stocktrak.com",
            "referer": "https://monash.stocktrak.com/",
            "sec-ch-ua": "^\^Google",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "^\^Windows^^",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        }

        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

        # Assuming the given JSON data is stored in a variable called json_data
        json_data = response.text

        data = json.loads(json_data)

        expiry_groups = data["results"]["expiryGroup"]
        
        def process_option(option_data):
            expiry_date = pd.to_datetime(option_data["contract"]["expirydate"])
            today = pd.Timestamp.today()
            T = (expiry_date - today).days / 365
            
            expected_return = self.calculate_expected_return(underlying_price, option_data["contract"]["strike"], 0.05, T, option_data["greeks"]["impvol"], option_data["contract"]["callput"])
            
            if 'last' in option_data["pricedata"]:
                option_price = option_data["pricedata"]["last"] 
                price_diff = option_price - expected_return
            else:
                option_price = None
                price_diff = None
                
            option_info = {
                "symbol": option_data["root"]["key"]["symbol"][0],
                "name": option_data["root"]["equityinfo"]["longname"],
                "spot_price": underlying_price,
                "option_price": option_price,
                "expiry": option_data["contract"]["expirydate"],
                "type": option_data["contract"]["callput"],
                "strike": option_data["contract"]["strike"],
                "volume": option_data["pricedata"]["contractvolume"],
                "open_interest": option_data["contract"]["openinterest"],
                "implied_volatility": option_data["greeks"]["impvol"],
                "delta": option_data["greeks"]["delta"],
                "gamma": option_data["greeks"]["gamma"],
                "theta": option_data["greeks"]["theta"],
                "vega": option_data["greeks"]["vega"],
                "rho": option_data["greeks"]["rho"],
                "expected_return": expected_return,
                "price_diff": price_diff,
                "T": T
            }
            return option_info

        options = []

        for expiry_group in expiry_groups: #Loop through expiries
            #print(expiry_group["expirydate"])
            
            for option_pair in expiry_group["callputgroup"]:
                #print(option_pair["symbolstring"])
                
                for option in option_pair["quote"]:
                    #print(option["contract"])
                    
                    options.append(process_option(option))
                    
            

        # Convert the list of option dictionaries into a DataFrame
        options_df = pd.DataFrame(options)

        return options_df


    def plot_volatility_surface(options_df):
        options_df["strike"] = options_df["strike"].astype(float)
        options_df["implied_volatility"] = options_df["implied_volatility"].astype(float)
        options_df["volume"] = options_df["volume"].astype(float)
        options_df["open_interest"] = options_df["open_interest"].astype(float)
        
        # Create a dataframe for each type of option
        call_options_df = options_df[options_df["type"] == "Call"]
        put_options_df = options_df[options_df["type"] == "Put"]
        
        # Create a new dataframe for the call and put options
        call_options_df = call_options_df[["strike", "implied_volatility"]]
        put_options_df = put_options_df[["strike", "implied_volatility"]]
        
        # Create a surface plot for the implied volatility of the call options
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        ax.plot_trisurf(call_options_df["strike"], call_options_df["implied_volatility"], call_options_df["strike"], cmap=plt.cm.jet, linewidth=0.2)
        ax.set_xlabel("Strike Price")
        ax.set_ylabel("Implied Volatility")
        ax.set_zlabel("Strike Price")
        ax.set_title("Call Option Implied Volatility Surface")
        
        # Create a surface plot for the implied volatility of the put options
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        ax.plot_trisurf(put_options_df["strike"], put_options_df["implied_volatility"], put_options_df["strike"], cmap=plt.cm.jet, linewidth=0.2)
        ax.set_xlabel("Strike Price")
        ax.set_ylabel("Implied Volatility")
        ax.set_zlabel("Strike Price")
        ax.set_title("Put Option Implied Volatility Surface")
        
        plt.show()
        
    def save_as_excel(self, options_df, ticker):
        options_df.to_excel(f"{ticker}_options.xlsx", index=False)
    
    def save_all_as_excel(self):
        self.data_all.to_excel(self.filename, index=False)
        
    def calculate_expected_return(self, S, K, r, T, sigma, option_type):
        d1 = (np.log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        if option_type == 'Call' :
            return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        elif option_type == 'Put':
            return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        else:
            raise ValueError('Invalid option type')

    def find_best_option(self):
        # Filter for in-the-money options
        df = self.data_all

        # Find option with highest price_diff
        best_option = df.iloc[df['price_diff'].argmax()]
        print(best_option)
        return best_option
    
    def import_from_excel(self):
        df = pd.read_excel(self.filename)
        self.data_all = df
        
    def plot_volatility_surface(self, ticker):
        
        # Create a dataframe for each type of option, filtering all options where ticker = ticker and type = Call or Put
        df = self.data_all
        df = df[df['symbol'] == ticker]

        # Ensure that expiry >= current date
        df['expiry'] = pd.to_datetime(df['expiry'])
        df = df[df['expiry'] >= pd.to_datetime('today')]
        
        # Create a new dataframe for the call and put options

        df_call = df[df['type'] == 'Call']
        df_put = df[df['type'] == 'Put']
        
        # Plot the implied volatility of the call options vs the strike price vs T
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        ax.plot_trisurf(df_call["strike"], df_call["implied_volatility"], df_call["T"], cmap=plt.cm.jet, linewidth=0.2)
        ax.set_xlabel("Strike Price")
        ax.set_ylabel("Implied Volatility")
        ax.set_zlabel("Time to Expiry")
        ax.set_title(f"Call Option Implied Volatility Smile for {ticker}")
        
        # Plot the implied volatility of the put options vs the strike price vs T
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        ax.plot_trisurf(df_put["strike"], df_put["implied_volatility"], df_put["T"], cmap=plt.cm.jet, linewidth=0.2)
        ax.set_xlabel("Strike Price")
        ax.set_ylabel("Implied Volatility")
        ax.set_zlabel("Time to Expiry")
        ax.set_title(f"Put Option Implied Volatility Smile for {ticker}")
        
        plt.show()
    
    def plot_volatility_smile(self, ticker):
        
        df = self.data_all
        df = df[df['symbol'] == ticker]
        # Prompt user to select an expiry date from the avaliable options
        expiries = df['expiry'].unique()
        print(expiries)
        expiry = input("Enter expiry date: ")
        df = df[df['expiry'] == expiry]
        
        
        # Create a dataframe for each type of option, filtering all options where ticker = ticker and type = Call or Put
        df_call = df[df['type'] == 'Call']
        df_put = df[df['type'] == 'Put']
        
        # Plot the implied volatility of the call options vs the strike price
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(df_call["strike"], df_call["implied_volatility"], color='blue')
        ax.set_xlabel("Strike Price")
        ax.set_ylabel("Implied Volatility")
        ax.set_title(f"Call Option Implied Volatility Smile for {ticker}")
        
        # Plot the implied volatility of the put options vs the strike price
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(df_put["strike"], df_put["implied_volatility"], color='blue')
        ax.set_xlabel("Strike Price")
        ax.set_ylabel("Implied Volatility")
        ax.set_title(f"Put Option Implied Volatility Smile for {ticker}")
        
        plt.show()



    def gif_moving_volatility_smile(self, tickers):
        for ticker in tickers:
            df = self.data_all
            df = df[df['symbol'] == ticker]
            
            
            # Create a dataframe for each type of option, filtering all options where ticker = ticker and type = Call or Put
            df_call = df[df['type'] == 'Call']
            df_put = df[df['type'] == 'Put']
            
            # Get unique expiry dates for iterating through
            expiries = df['expiry'].unique()
            
            # Create a list to store image file names
            filenames = []
            
            # Iterate through expiry dates and create a new plot for each
            for expiry in expiries:
                df_ex_call = df_call[df_call['expiry'] == expiry]
                df_ex_put = df_put[df_put['expiry'] == expiry]
                
                # Determine the current ATM price (assuming the first option is ATM)
                spot_price = df_ex_call.iloc[0]['spot_price']

                print(f"Creating plot for {expiry}")
                print(df_ex_call)
                print(df_ex_put)

                # Create a figure with two subplots for call and put options
                fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(10, 5))
                
                # Plot the implied volatility of the call options vs the strike price
                ax1.plot(df_ex_call["strike"], df_ex_call["implied_volatility"], color='blue')
                ax1.axvline(x=spot_price, color='red', linestyle='--', label=f"ATM: {spot_price:.2f}")

                ax1.set_xlabel("Strike Price")
                ax1.set_ylabel("Implied Volatility")
                ax1.set_title(f"Call Option Implied Volatility Smile for {ticker}\nExpiry: {expiry}")
                
                # Plot the implied volatility of the put options vs the strike price
                ax2.plot(df_ex_put["strike"], df_ex_put["implied_volatility"], color='blue')
                ax2.axvline(x=spot_price, color='red', linestyle='--', label=f"ATM: {spot_price:.2f}")

                ax2.set_xlabel("Strike Price")
                ax2.set_ylabel("Implied Volatility")
                ax2.set_title(f"Put Option Implied Volatility Smile for {ticker}\nExpiry: {expiry}")
                
                # Save the figure as an image and add the file name to the list
                filename = f"{ticker}_{expiry}.png"
                plt.savefig(filename)
                filenames.append(filename)
                
                # Close the figure
                plt.close()
            
            # Use imageio to create a GIF from the saved images
            with imageio.get_writer(f"{ticker}_vol_smile.gif", mode='I', duration=0.5) as writer:
                for filename in filenames:
                    image = imageio.imread(filename)
                    writer.append_data(image)
            
            # Remove the image files
            for filename in set(filenames):
                os.remove(filename)
        
        
if __name__ == "__main__":
    stocks = ["GE", "AAPL", "SPY", "TSLA", "MSFT", "AMZN", "GOOG", "NFLX", "NVDA", "AMD", "INTC", "BABA", "BAC", "C", "JPM", "WFC", "V", "MA", "PYPL", "T", "DIS", "CMCSA", "NKE", "PFE", "MRK", "UNH", 
            "HD", "MCD", "KO", "PEP", "VZ", "XOM", "CVX", "WMT", "JNJ", "PG", "TGT", "LOW", "COST", "M", "BA", "CAT", "MMM", "GS", "IBM", "AMGN", "AXP", "CRM", "DHR", "DOW", "DUK", "EXC", "FDX", "GILD", "HON", 
            "INTU", "JNJ", "KO", "LMT", "MDT", "MET", "MS", "NEE", "PEP", "PM", "QCOM", "RTX", "SBUX", "SO", "SPG", "TMO", "TRV", "UNP", "UPS", "USB", "V", "VZ", "WBA", "WFC", "WMT", "XOM"]
    #stocks = ["GE", "AAPL"]
    cookie = "" # get unique cookie online from Stoktrak 
    new_options = OptionData(stocks, cookie)
    #new_options.run_all_tickers()
    #new_options.save_all_as_excel()
    new_options.import_from_excel()
    new_options.find_best_option()
    #new_options.plot_volatility_surface("SBUX")
    new_options.gif_moving_volatility_smile(["SBUX", "AAPL", "NKE", "GE", "TSLA", "MSFT", "AMZN", "GOOG", "NFLX", "NVDA", "AMD", "JPM"])