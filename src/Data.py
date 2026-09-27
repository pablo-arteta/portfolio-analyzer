import yfinance as yf
import pandas as pd
import csv
import matplotlib.pyplot as plt
'''
🇺🇸 United States — (none)	AAPL
🇪🇸 Spain — BME .MC	
🇬🇧 United Kingdom — London Stock Exchange	.L	
🇩🇪 Germany — Xetra .DE	
🇫🇷 France — Euronext Paris .PA	
🇮🇹 Italy — Borsa Italiana	.MI	
🇳🇱 Netherlands — Euronext Amsterdam .AS	
🇨🇭 Switzerland	.SW	
🇯🇵 Japan	.T	
🇭🇰 Hong Kong	.HK	
🇨🇳 China — Shanghai	.SS	
🇨🇳 China — Shenzhen	.SZ	
🇨🇦 Canada — Toronto	.TO	
🇦🇺 Australia	.AX	
🇮🇳 India — NSE	.NS	
🇮🇳 India — BSE	.BO	
🇧🇷 Brazil	.SA	
🇲🇽 Mexico	.MX	
🇸🇪 Sweden	.ST	
🇩🇰 Denmark .CO	
🇳🇴 Norway	.OL	
🇫🇮 Finland .HE
🇸🇬 Singapore .SI
🇰🇷 South Korea .KS
🇿🇦 South Africa .JO
🇳🇿 New Zealand .NZ
🇹🇼 Taiwan	.TW	
🇹🇷 Turkey	.IS	
'''
class Data():
    def __init__(self):
        self.tickers : list[str] = [] 
        self.data : pd.DataFrame = pd.DataFrame()
    def get_data(self):
        '''
        The user inputs the assets in their portfolio along with their respective weights.
        '''
        while True:
         ticker = input("Introduce the ticker of the company: ")
         if ticker == "":
             break
         self.tickers.append(ticker)
        start_date = input("Introduce the start date (YYYY-MMM-DD): ")
        end_date = input("Introduce the end date (YYYY-MMM-DD): ")
        '''
        Validate/download the tickers of the users.
        '''        
        self.data = yf.download(tickers=self.tickers, auto_adjust = True, start = start_date, end=end_date)
        if self.data.empty:
            print("Invalid tickers")
        else :
            print("Data downloaded successfully")
        '''
        MultiIndex columns: adjunta por close,high,low opwn,volume

        PROBLEM: NAN VALUES!!
        We create csv per ticker (pending)
        '''
        for ticker in self.tickers:
            with open(f"{ticker}.csv", "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(self.data)
        self.data.dropna(inplace=True)#NAN values solved?  SPLIT/REVERSE SPLIT PROBLEMS
        return 
def main():
    portfolio = Data()

    portfolio.get_data()

    print("\nTickers introducidos:")
    print(portfolio.tickers)

    print("\nPrimeras filas de los datos descargados:")
    print(portfolio.data.head())

    portfolio.data.plot()  #Create the graph
    plt.show() # Visualize the graph
    
if __name__ == "__main__":
    main()


'''
SORTINO RATIO: PENALIZA LOS DD PROLONGADOS 
SHARPE RATIO : NO PENALIZA LOS DD PROLONGADOS (VALORA MAS LAS GANANCIA FINAL)
'''