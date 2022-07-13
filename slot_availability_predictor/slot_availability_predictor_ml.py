import pandas as pd
from fbprophet import Prophet
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
import  numpy as np
from datetime import datetime, timedelta
import dateutil
import dateutil.parser
plt.style.use('fivethirtyeight')

PRICE_TOPIC = "iot/underground_smart_parking/price/1"
QOS = 2
PREDICTION_RANGE = 2
BASE_PRICE = 1
EXP = 1.4
NUM_SLOTS = 6
NORMALIZATION = 0.5/NUM_SLOTS

def fzwait():
    if False:
        return input("Press Enter to continue.")
    return ' '

class MQTTServer():

    def setupMQTT(self):
        self.clientMQTT = mqtt.Client()
        self.clientMQTT.on_connect = self.on_connect
        self.clientMQTT.on_message = self.on_message
        print("connecting mqtt...")
        self.clientMQTT.connect("broker.hivemq.com", 1883, 60)

        self.clientMQTT.loop_start()


    def on_connect(self, client, userdata, flags, rc):
        #self.clientMQTT.subscribe(PRICE_TOPIC)
        print("Connected with mqtt broker with result code " + str(rc))

    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))

    def setup(self):
        self.setupMQTT()


if __name__ == "__main__":
    mqttServer = MQTTServer()
    mqttServer.setup()

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
    ax.set_ylabel('Monthly parking slot occupations')
    ax.set_xlabel('Date')

    plt.show()

    fzwait()

    m = Prophet(changepoint_prior_scale=0.01).fit(df)
    future = m.make_future_dataframe(periods=3000, freq='60min')
    fcst = m.predict(future)
    fig = m.plot(fcst)
    fig.show()
    print(fcst)

    now = dateutil.parser.parse(datetime.utcnow().isoformat())
    future_time = now - timedelta(hours=PREDICTION_RANGE)

    #fcst["ds"]=pd.to_datetime(fcst["ds"], format="YYYY-mm-dd hh:mm:ss")
    future_state = fcst.loc[(fcst["ds"].dt.year == future_time.year) & (fcst["ds"].dt.month == future_time.month) & (fcst["ds"].dt.day == future_time.day) & (fcst["ds"].dt.hour == future_time.hour) ]

    average_future_disponibility = future_state["trend"].iloc[0]
    current_price = BASE_PRICE + ((NUM_SLOTS-average_future_disponibility) ** EXP) * NORMALIZATION

    mqttServer.clientMQTT.publish(PRICE_TOPIC, '{:f}'.format(current_price), qos=QOS, retain=True)

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

