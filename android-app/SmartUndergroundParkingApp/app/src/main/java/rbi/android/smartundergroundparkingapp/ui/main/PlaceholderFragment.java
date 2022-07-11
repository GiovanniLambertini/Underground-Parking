package rbi.android.smartundergroundparkingapp.ui.main;

import static rbi.android.smartundergroundparkingapp.MainActivity.BASE_TOPIC;
import static rbi.android.smartundergroundparkingapp.MainActivity.BROKER_ADDRESS;
import static rbi.android.smartundergroundparkingapp.MainActivity.BROKER_PORT;
import static rbi.android.smartundergroundparkingapp.MainActivity.BROKER_URL;
import static rbi.android.smartundergroundparkingapp.MainActivity.MESSAGE_COUNT;
import static rbi.android.smartundergroundparkingapp.MainActivity.BASE_TOPIC;
import static rbi.android.smartundergroundparkingapp.MainActivity.logger;

import android.content.Context;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;

import androidx.annotation.Nullable;
import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.core.content.res.ResourcesCompat;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.Observer;
import androidx.lifecycle.ViewModelProvider;

import com.android.volley.AuthFailureError;
import com.android.volley.NetworkResponse;
import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.VolleyLog;
import com.android.volley.toolbox.HttpHeaderParser;
import com.android.volley.toolbox.StringRequest;
import com.android.volley.toolbox.Volley;

import org.eclipse.paho.client.mqttv3.IMqttClient;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttClientPersistence;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.UnsupportedEncodingException;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import rbi.android.smartundergroundparkingapp.EngineTemperatureSensor;

import rbi.android.smartundergroundparkingapp.R;
import rbi.android.smartundergroundparkingapp.databinding.FragmentMainBinding;



/**
 * A placeholder fragment containing a simple view.
 */
public class PlaceholderFragment extends Fragment {
    static final String FLASK_URL_BOOKING = "http://10.0.2.2/booking";
    private static final String ARG_SECTION_NUMBER = "section_number";

    private PageViewModel pageViewModel;
    private FragmentMainBinding binding;
    TextView price, access_code, available_slots;
    LinearLayout a1, a2, a3, a4, a5, a6;
    Button book;
    Context context;
    MqttClientPersistence persistence;
    IMqttClient client;
    MqttConnectOptions options;

    public static PlaceholderFragment newInstance(int index) {
        PlaceholderFragment fragment = new PlaceholderFragment();
        Bundle bundle = new Bundle();
        bundle.putInt(ARG_SECTION_NUMBER, index);
        fragment.setArguments(bundle);
        return fragment;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        pageViewModel = new ViewModelProvider(this).get(PageViewModel.class);
        int index = 1;
        if (getArguments() != null) {
            index = getArguments().getInt(ARG_SECTION_NUMBER);
        }
        pageViewModel.setIndex(index);
    }

    @Override
    public View onCreateView(
            @NonNull LayoutInflater inflater, ViewGroup container,
            Bundle savedInstanceState) {

        binding = FragmentMainBinding.inflate(inflater, container, false);
        View root = binding.getRoot();

        //Generate a random MQTT client ID using the UUID class
        String clientId = UUID.randomUUID().toString();

        price = binding.price;
        access_code = binding.accessCode;
        available_slots = binding.availableSlots;
        book = binding.book;
        a1 = binding.a1;
        a2 = binding.a2;
        a3 = binding.a3;
        a4 = binding.a4;
        a5 = binding.a5;
        a6 = binding.a6;
        LinearLayout[] slotsListViews = {a1, a2, a3, a4, a5, a6};
        /*pageViewModel.getText().observe(getViewLifecycleOwner(), new Observer<String>() {
            @Override
            public void onChanged(@Nullable String s) {
                textView.setText(s);
            }
        });*/
        price.setText("");

        ExecutorService executor = Executors.newSingleThreadExecutor();
        Handler handler = new Handler(Looper.getMainLooper());

        executor.execute(() -> {
            //Background work here
            try{



                //Represents a persistent data store, used to store outbound and inbound messages while they
                //are in flight, enabling delivery to the QoS specified. In that case use a memory persistence.
                //When the application stops all the temporary data will be deleted.
                persistence = new MemoryPersistence();

                //The the persistence is not passed to the constructor the default file persistence is used.
                //In case of a file-based storage the same MQTT client UUID should be used
                client = new MqttClient(
                        String.format("tcp://%s:%d", BROKER_ADDRESS, BROKER_PORT), //Create the URL from IP and PORT
                        clientId,
                        persistence);

                //Define MQTT Connection Options such as reconnection, persistent/clean session and connection timeout
                //Authentication option can be added -> See AuthProducer example
                options = new MqttConnectOptions();
                options.setAutomaticReconnect(true);
                options.setCleanSession(true);
                options.setConnectionTimeout(10);

                //Connect to the target broker
                client.connect(options);

                logger.info("Connected ! Client Id: {}", clientId);

                //Subscribe to the target topic #. In that case the consumer will receive (if authorized) all the message
                //passing through the broker
                client.subscribe(BASE_TOPIC+"#",2);

                // iot/underground_smart_parking/A/1
                // ...
                // iot/underground_smart_parking/A/6

                // iot/underground_smart_parking/A/price
                // iot/underground_smart_parking/A/available_slots

                client.setCallback(new MqttCallback() {
                    @Override
                    public void connectionLost(Throwable cause) {
                    }

                    @Override
                    public void messageArrived(String topic, MqttMessage message) throws Exception {
                        System.out.println(String.format("[%s] %s", topic, new String(message.getPayload())));
                        String messageReceived = new String(message.getPayload());
                        if(topic.contains(BASE_TOPIC+"price"))
                            price.setText( String.format("%.2f", Double.parseDouble(messageReceived))+" €/h");
                        else if(topic.contains(BASE_TOPIC+"available_slots"))
                            available_slots.setText("Posti disponibili: " + messageReceived);
                        else if(topic.contains(BASE_TOPIC+"total_price_paid"))
                            access_code.setText("Costo parcheggio: " + messageReceived+" €");
                        else if(topic.contains(BASE_TOPIC+"slot_state")) {
                            String[] topicParts = topic.split("/");
                            String slot = topicParts[topicParts.length-1];
                            if(messageReceived.equals("0"))
                                slotsListViews[Integer.parseInt(slot)-1].setBackground(ResourcesCompat.getDrawable(getResources(), R.drawable.slotshapetaken, null));
                            else
                                slotsListViews[Integer.parseInt(slot)-1].setBackground(ResourcesCompat.getDrawable(getResources(), R.drawable.slotshape, null));

                        }

                        // iot/underground_smart_parking/A/1
                        // ...
                        // iot/underground_smart_parking/A/6

                        // iot/underground_smart_parking/A/price
                        // iot/underground_smart_parking/A/available_slots

                        logger.info("Message Received ({}) Message Received: {}", topic, new String(message.getPayload()));

                    }

                    @Override
                    public void deliveryComplete(IMqttDeliveryToken token) {

                    }
                });


            }catch (Exception e){
                e.printStackTrace();
            }

            book.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View view) {
                    Thread thread = new Thread(){
                        public void run(){
                            System.out.println("Thread Running");
                            try {
                                URL url = new URL (FLASK_URL_BOOKING);//"https://www.picuruldemierezilnic.com/flask/booking");
                                HttpURLConnection con = (HttpURLConnection)url.openConnection();
                                con.setRequestMethod("POST");
                                con.setRequestProperty("Content-Type", "application/json; utf-8");
                                con.setRequestProperty("Accept", "application/json");
                                con.setDoOutput(true);
                                String jsonInputString = "{\"userId\": 1, \"locationId\": 1, \"type\":\"device\"}";

                                try(OutputStream os = con.getOutputStream()) {
                                    byte[] input = jsonInputString.getBytes("utf-8");
                                    os.write(input, 0, input.length);
                                }

                                try(BufferedReader br = new BufferedReader(
                                        new InputStreamReader(con.getInputStream(), "utf-8"))) {
                                    StringBuilder response = new StringBuilder();
                                    String responseLine = null;
                                    while ((responseLine = br.readLine()) != null) {
                                        response.append(responseLine.trim());
                                    }
                                    System.out.println(response.toString());
                                    JSONObject jsonObject = null;
                                    try {
                                        jsonObject = new JSONObject(response.toString());
                                        String code = jsonObject.getString("code");

                                        access_code.setText("Codice Accesso: " + code);
                                    } catch (JSONException e) {
                                        access_code.setText("Codice Accesso non disponibile..");
                                    }
                                }

                       /* RequestQueue requestQueue = Volley.newRequestQueue(view.getContext());
                        String URL = "http://127.0.0.1:80/booking";// "https://www.picuruldemierezilnic.com/flask/booking";
                        JSONObject jsonBody = new JSONObject();
                        jsonBody.put("userId", 1);
                        jsonBody.put("locationId", 1);
                        jsonBody.put("type", "device");
                        final String requestBody = jsonBody.toString();

                        StringRequest stringRequest = new StringRequest(Request.Method.POST, URL, new Response.Listener<String>() {
                            @Override
                            public void onResponse(String response) {
                                Log.i("VOLLEY", response);

                            }
                        }, new Response.ErrorListener() {
                            @Override
                            public void onErrorResponse(VolleyError error) {
                                Log.e("VOLLEY", error.toString());
                            }
                        }) {
                            @Override
                            public String getBodyContentType() {
                                return "application/json; charset=utf-8";
                            }

                            @Override
                            public byte[] getBody() throws AuthFailureError {
                                try {
                                    return requestBody == null ? null : requestBody.getBytes("utf-8");

                                } catch (UnsupportedEncodingException uee) {
                                    VolleyLog.wtf("Unsupported Encoding while trying to get the bytes of %s using %s", requestBody, "utf-8");
                                    return null;
                                }
                            }

                            @Override
                            protected Response<String> parseNetworkResponse(NetworkResponse response) {
                                String parsed;
                                try {
                                    parsed = new String(response.data, HttpHeaderParser.parseCharset(response.headers));
                                    JSONObject jsonObject = null;
                                    try {

                                        jsonObject = new JSONObject(parsed);
                                        String code = jsonObject.getString("code");

                                        access_code.setText("Codice Accesso: " + code);
                                    } catch (JSONException e) {
                                        access_code.setText("Codice Accesso non disponibile..");
                                    }
                                } catch (UnsupportedEncodingException e) {
                                    parsed = new String(response.data);
                                }
                                return Response.success(parsed, HttpHeaderParser.parseCacheHeaders(response));

                            }
                        };

                        requestQueue.add(stringRequest);

                        */
                            } catch (MalformedURLException e) {
                                e.printStackTrace();
                            } catch (IOException e) {
                                e.printStackTrace();
                            }
                        }
                    };

                    thread.start();


                    /*
// Instantiate the RequestQueue.
                    RequestQueue queue = Volley.newRequestQueue(inflater.getContext());
                    String url = FLASK_URL_BOOKING;

// Request a string response from the provided URL.
                    StringRequest stringRequest = new StringRequest(Request.Method.POST, url,
                            new Response.Listener<String>() {
                                @Override
                                public void onResponse(String response) {
                                    // Display the first 500 characters of the response string.
                                    JSONObject jsonObject = null;
                                    try {
                                        jsonObject = new JSONObject(response);
                                        String code = jsonObject.getString("code");

                                        access_code.setText("Codice Accesso: " + code);
                                    } catch (JSONException e) {
                                        access_code.setText("Codice Accesso non disponibile..");
                                    }

                                }
                            }, new Response.ErrorListener() {
                        @Override
                        public void onErrorResponse(VolleyError error) {
                            access_code.setText("Codice Accesso non disponibile...");
                        }
                    });
// Add the request to the RequestQueue.
                    queue.add(stringRequest); */
                }
            });


            logger.info("SimpleProducer started ...");

            try{

                //Create an instance of an Engine Temperature Sensor
                EngineTemperatureSensor engineTemperatureSensor = new EngineTemperatureSensor();

                //Start to publish MESSAGE_COUNT messages
                for(int i = 0; i < MESSAGE_COUNT; i++) {

                    //Send data as simple numeric value
                    double sensorValue = engineTemperatureSensor.getTemperatureValue();
                    String payloadString = Double.toString(sensorValue);

                    //Internal Method to publish MQTT data using the created MQTT Client
                    publishData(client, BASE_TOPIC, payloadString);

                    //Sleep for 1 Second
                    //  Thread.sleep(1000);
                }

                //underground_smartparking?id_parking=...  &device_type=0,1

                //Disconnect from the broker and close the connection
               // client.disconnect();
               // client.close();

                logger.info("Disconnected !");

            }catch (Exception e){
                e.printStackTrace();
            }


            handler.post(() -> {
                //UI Thread work here
            });
        });
        return root;
    }

    //producer
    public static void publishData(IMqttClient mqttClient, String topic, String msgString) throws MqttException {

        logger.debug("Publishing to Topic: {} Data: {}", topic, msgString);

        if (mqttClient.isConnected() && msgString != null && topic != null) {

            //Create an MQTT Message defining the required QoS Level and if the message is retained or not
            MqttMessage msg = new MqttMessage(msgString.getBytes());
            msg.setQos(2);
            msg.setRetained(false);
            mqttClient.publish(topic,msg);

            logger.debug("Data Correctly Published !");
        }
        else{
            logger.error("Error: Topic or Msg = Null or MQTT Client is not Connected !");
        }

    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }
}