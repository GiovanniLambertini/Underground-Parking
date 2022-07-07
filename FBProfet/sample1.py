import pandas as pd
from fbprophet import Prophet
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

def fzwait():
    if False:
        return input("Press Enter to continue.")
    return ' '

if __name__ == "__main__":

    # 1. lettura dati
    df = pd.read_csv('slot_availability.csv')
    print(df.head(5))

    # 2.0 tipi di dato e nomi colonne
    print(df.dtypes)
    df['Datetime'] = pd.DatetimeIndex(df['Datetime'])
    print(df.dtypes)
    df = df.rename(columns={'Datetime': 'ds',
                            'Slots': 'y'})
    print(df.head(5))

    #3.0 show data
    ax = df.set_index('ds').plot(figsize=(12, 8))
    ax.set_ylabel('Monthly Number of Airline Passengers')
    ax.set_xlabel('Date')

    plt.show()

    fzwait()

    #4.0 model creation
    my_model = Prophet(interval_width=0.95, weekly_seasonality=True)


    #5.0 fit the data
    my_model.fit(df)

    #6.0 creation of future dataframe
    future_dates = my_model.make_future_dataframe(periods=36, freq='MS')
    print(future_dates.tail())

    #7.0 forecast
    forecast = my_model.predict(future_dates)
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()

    #8.0 plot of the forecast
    plt2 = my_model.plot(forecast, uncertainty=True)
    plt2.show()
    fzwait()



    plt3 = my_model.plot_components(forecast)
    plt3.show()
    fzwait()