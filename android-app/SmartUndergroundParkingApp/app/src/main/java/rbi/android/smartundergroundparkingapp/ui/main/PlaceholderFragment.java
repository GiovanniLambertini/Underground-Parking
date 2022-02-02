package rbi.android.smartundergroundparkingapp.ui.main;

import static rbi.android.smartundergroundparkingapp.MainActivity.BROKER_ADDRESS;
import static rbi.android.smartundergroundparkingapp.MainActivity.BROKER_PORT;
import static rbi.android.smartundergroundparkingapp.MainActivity.BROKER_URL;
import static rbi.android.smartundergroundparkingapp.MainActivity.MESSAGE_COUNT;
import static rbi.android.smartundergroundparkingapp.MainActivity.TOPIC;
import static rbi.android.smartundergroundparkingapp.MainActivity.logger;

import android.content.Context;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.annotation.Nullable;
import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.core.content.res.ResourcesCompat;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.Observer;
import androidx.lifecycle.ViewModelProvider;

import org.eclipse.paho.client.mqttv3.IMqttClient;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttClientPersistence;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

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

    private static final String ARG_SECTION_NUMBER = "section_number";

    private PageViewModel pageViewModel;
    private FragmentMainBinding binding;
    TextView price, access_code, available_slots;
    LinearLayout a1, a2, a3, a4, a5, a6;
    Button book;
    Context context;

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
        /*pageViewModel.getText().observe(getViewLifecycleOwner(), new Observer<String>() {
            @Override
            public void onChanged(@Nullable String s) {
                textView.setText(s);
            }
        });*/
        price.setText("3$/h");

        ExecutorService executor = Executors.newSingleThreadExecutor();
        Handler handler = new Handler(Looper.getMainLooper());

        executor.execute(() -> {
            //Background work here
            try{

                //Generate a random MQTT client ID using the UUID class
                String clientId = UUID.randomUUID().toString();

                //Represents a persistent data store, used to store outbound and inbound messages while they
                //are in flight, enabling delivery to the QoS specified. In that case use a memory persistence.
                //When the application stops all the temporary data will be deleted.
                MqttClientPersistence persistence = new MemoryPersistence();

                //The the persistence is not passed to the constructor the default file persistence is used.
                //In case of a file-based storage the same MQTT client UUID should be used
                IMqttClient client = new MqttClient(
                        String.format("tcp://%s:%d", BROKER_ADDRESS, BROKER_PORT), //Create the URL from IP and PORT
                        clientId,
                        persistence);

                //Define MQTT Connection Options such as reconnection, persistent/clean session and connection timeout
                //Authentication option can be added -> See AuthProducer example
                MqttConnectOptions options = new MqttConnectOptions();
                // options.setAutomaticReconnect(true);
                options.setCleanSession(true);
                options.setConnectionTimeout(10);

                //Connect to the target broker
                client.connect(options);

                logger.info("Connected ! Client Id: {}", clientId);

                //Subscribe to the target topic #. In that case the consumer will receive (if authorized) all the message
                //passing through the broker
                client.subscribe("iot/underground_smart_parking/#",2);

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
                        switch (topic){
                            case "iot/underground_smart_parking/A/price":
                                price.setText(messageReceived+" $/h");
                                break;
                            case "iot/underground_smart_parking/A/available_slots":
                                available_slots.setText("Posti disponibili: " + messageReceived);
                                break;
                            case "iot/underground_smart_parking/A/access_code":
                                access_code.setText("CODICE ACCESSO: " + messageReceived);
                                break;
                            case "iot/underground_smart_parking/A/1":
                                if(messageReceived.equals("0"))
                                    a1.setBackground(ResourcesCompat.getDrawable(getResources(), R.drawable.slotshape, null));
                                else
                                    a1.setBackground(ResourcesCompat.getDrawable(getResources(), R.drawable.slotshapetaken, null));
                                break;
                            case "iot/underground_smart_parking/A/2":
                                if(messageReceived.equals("0"))
                                    a2.setBackground(ResourcesCompat.getDrawable(getResources(), R.drawable.slotshape, null));
                                else
                                    a2.setBackground(ResourcesCompat.getDrawable(getResources(), R.drawable.slotshapetaken, null));
                                break;

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


            logger.info("SimpleProducer started ...");

            try{

                //Generate a random MQTT client ID using the UUID class
                String mqttClientId = UUID.randomUUID().toString();

                //Represents a persistent data store, used to store outbound and inbound messages while they
                //are in flight, enabling delivery to the QoS specified. In that case use a memory persistence.
                //When the application stops all the temporary data will be deleted.
                MqttClientPersistence persistence = new MemoryPersistence();

                //The the persistence is not passed to the constructor the default file persistence is used.
                //In case of a file-based storage the same MQTT client UUID should be used
                IMqttClient client = new MqttClient(BROKER_URL, mqttClientId, persistence);

                //Define MQTT Connection Options such as reconnection, persistent/clean session and connection timeout
                //Authentication option can be added -> See AuthProducer example
                MqttConnectOptions options = new MqttConnectOptions();
                //options.setAutomaticReconnect(true);
                options.setCleanSession(true);
                options.setConnectionTimeout(10);

                //Connect to the target broker
                client.connect(options);

                logger.info("Connected ! Client Id: {}", mqttClientId);

                //Create an instance of an Engine Temperature Sensor
                EngineTemperatureSensor engineTemperatureSensor = new EngineTemperatureSensor();

                //Start to publish MESSAGE_COUNT messages
                for(int i = 0; i < MESSAGE_COUNT; i++) {

                    //Send data as simple numeric value
                    double sensorValue = engineTemperatureSensor.getTemperatureValue();
                    String payloadString = Double.toString(sensorValue);

                    //Internal Method to publish MQTT data using the created MQTT Client
                    publishData(client, TOPIC, payloadString);

                    //Sleep for 1 Second
                    //  Thread.sleep(1000);
                }

                //Disconnect from the broker and close the connection
                client.disconnect();
                client.close();

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