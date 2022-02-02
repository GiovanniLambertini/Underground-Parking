package rbi.android.smartundergroundparkingapp;

import android.os.Bundle;

import com.google.android.material.floatingactionbutton.FloatingActionButton;
import com.google.android.material.snackbar.Snackbar;
import com.google.android.material.tabs.TabLayout;

import androidx.viewpager.widget.ViewPager;
import androidx.appcompat.app.AppCompatActivity;

import android.os.Handler;
import android.os.Looper;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;

import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import rbi.android.smartundergroundparkingapp.ui.main.SectionsPagerAdapter;
import rbi.android.smartundergroundparkingapp.databinding.ActivityMainBinding;

public class MainActivity extends AppCompatActivity  {
    public final static Logger logger = LoggerFactory.getLogger(SimpleConsumer.class);

    //CONSUMER MQTT
    //IP Address of the target MQTT Broker
    public static final String BROKER_ADDRESS = "broker.emqx.io";

    //PORT of the target MQTT Broker
    public static final int BROKER_PORT = 1883;

    //PRODUCER MQTT
    //BROKER URL
    public static final String BROKER_URL = "tcp://broker.emqx.io:1883";

    //Message Limit generated and sent by the producer
    public static final int MESSAGE_COUNT = 10;

    //Topic used to publish generated demo data
    public static final String TOPIC = "iot/underground_smart_parking1/prova";


    private ActivityMainBinding binding;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        SectionsPagerAdapter sectionsPagerAdapter = new SectionsPagerAdapter(this, getSupportFragmentManager());
        ViewPager viewPager = binding.viewPager;
        viewPager.setAdapter(sectionsPagerAdapter);
        TabLayout tabs = binding.tabs;
        tabs.setupWithViewPager(viewPager);
       /* FloatingActionButton fab = binding.fab;

        fab.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Snackbar.make(view, "Replace with your own action", Snackbar.LENGTH_LONG)
                        .setAction("Action", null).show();
            }
        });*/

    }



}