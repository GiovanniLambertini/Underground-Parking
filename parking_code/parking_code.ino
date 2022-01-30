#include <Servo.h>
#include <Keypad.h>

#define BARRIER_SENSOR1 31
#define BARRIER_SENSOR2 5
#define BARRIER_MOTOR 35
#define PARK1 52
#define PARK2 46
#define PARK3 40
#define PARK4 34
#define PARK5 28
#define PARK6 22
#define LED_A 53
#define LED_B 51
#define LED_C 49
#define LED_D 47
#define LED_E 45
#define LED_F 43
#define LED_G 41
#define LED_DP 39

#define LED_RED 2
#define LED_GREEN 3
#define LED_BLUE 4

#define NUM_SLOTS 6
#define DISPLAY_SEGMENTS 8
#define COMMON_CATHODE 0

#define ROWS 4
#define COLS 4
#define ROW1 6
#define ROW2 7
#define ROW3 8
#define ROW4 9
#define COL1 10
#define COL2 11
#define COL3 12
#define COL4 13

#define INITIAL_STATE 0
#define ACCESS_REQUEST 1
#define BARRIER_ACTIVE 2
//#define BARRIER_SENSOR2_ACTIVE 2
#define FINAL_STATE 3

Servo servo;
int angle = 0;
int slots[NUM_SLOTS]={PARK1, PARK2, PARK3, PARK4, PARK5, PARK6};
bool slotsState[NUM_SLOTS];                                                                     //Occupato - false, Libero - true
int segments[DISPLAY_SEGMENTS] {LED_A, LED_B, LED_C, LED_D, LED_E, LED_F, LED_G, LED_DP};       //Pin display 7 segmenti
volatile int state;
int available_parks;
int bluetoothData;

// Matrice bottoni
char buttonMatrix[ROWS][COLS] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};

byte rowPins[ROWS] = {ROW1, ROW2, ROW3, ROW4};     // Pin delle righe del keypad
byte colPins[COLS] = {COL1, COL2, COL3, COL4};     // Pin delle colonne del keypad

Keypad customKeypad = Keypad(makeKeymap(buttonMatrix), rowPins, colPins, ROWS, COLS);

byte displayNumber[][DISPLAY_SEGMENTS] { 
           {1,1,1,1,1,1,0,0},   //0
           {0,1,1,0,0,0,0,0},   //1
           {1,1,0,1,1,0,1,0},   //2
           {1,1,1,1,0,0,1,0},   //3
           {0,1,1,0,0,1,1,0},   //4
           {1,0,1,1,0,1,1,0},   //5
           {1,0,1,1,1,1,1,0},   //6
           {1,1,1,0,0,0,0,0},   //7
           {1,1,1,1,1,1,1,0},   //8
           {1,1,1,1,0,1,1,0},   //9
};

void setup() { 
  int i;
   
  state=0;
  bluetoothData=-1;
  available_parks=0;
  
  pinMode(BARRIER_MOTOR, OUTPUT); 
  pinMode(BARRIER_SENSOR1, INPUT); 
  pinMode(BARRIER_SENSOR2, INPUT); 

  for (i=0; i<NUM_SLOTS; i++){
    pinMode(slots[i], INPUT);
    slotsState[i] = digitalRead(slots[i]);
    if (slotsState[i])                        //Se il posto è libero
      available_parks++;
  }

  for (i=0; i<DISPLAY_SEGMENTS; i++){
    pinMode(segments[i], OUTPUT);
  }

  pinMode(LED_RED, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_BLUE, OUTPUT);

  /*
  for (i=0; i<ROWS; i++){
    pinMode(rowPins[i], INPUT);
  }

  for (i=0; i<COLS; i++){
    pinMode(colPins[i], INPUT);
  }
  */
  
  Serial.begin(9600);           // Monitor
  Serial1.begin(9600);          //Bluetooth

  servo.attach(BARRIER_MOTOR);
  servo.write(angle);

  attachInterrupt(digitalPinToInterrupt(BARRIER_SENSOR1), checkBarrierSensor1, FALLING );    
  attachInterrupt(digitalPinToInterrupt(BARRIER_SENSOR2), checkBarrierSensor2, RISING );   
}

void loop() {
  /*
  for(int i = 0; i < 10; i++) //print
  {
    display_number(i);
    delay(1000);
  }
  */

  // Leggo il bottone premuto
  char button = customKeypad.getKey();

  if (button) {                               //Se è stato premuto un bottone
    Serial.println(button);
  }

  if (Serial1.available()>0){
    bluetoothData = Serial1.read();
    Serial.print(bluetoothData);
  }
  bluetoothData = bluetoothData%3;

  switch (bluetoothData){
    case 0:                                               //Prenotazione - Solo diminuzione posto
      led_RGB(255, 0, 0); // Red
      servo.write(90);               
      delay(3000);
      servo.write(10);    
      break;

    case 1:                                               //Prenotazione - Solo alzata sbarra
      led_RGB(0, 255, 0); //Green
      servo.write(90);               
      delay(3000);
      servo.write(10);   
      break;

    case 2:                                               //Senza prenotazione - Diminuzione posto e alzata sbarra
      led_RGB(255, 150, 0); //Orange
      servo.write(90);               
      delay(3000);
      servo.write(10);   
      break;

    default:                                              //Se non ho dati sulla seriale
      break;
  }

  /*
  
  if(digitalRead(BARRIER_SENSOR1)==LOW){
    // scan from 0 to 180 degrees
    //angle=90;
    for(angle = 10; angle < 90; angle++)  
    {                                  
      servo.write(angle);               
      //delay(15);                   
    } 

    while (digitalRead(BARRIER_SENSOR1)==LOW);             //Aspetto che la macchina sia andata via
    delay(2*1000); 
    
    // now scan back from 180 to 0 degrees
    for(angle = 90; angle > 10; angle--)    
    {                                
      servo.write(angle);           
      //delay(15);       
    } 
  }
  */
  

  for (int i=0; i<NUM_SLOTS; i++){
    Serial.print("Stato parcheggio");
    Serial.print(i+1);
    Serial.print(": ");
    Serial.println(digitalRead(slots[i])); 
  }

  delay(3000);
}


void display_number(int num) // print any number on the segment
{ 
  //setState(COMMON_CATHODE);//turn off the segment
 
  for(int i=0; i<DISPLAY_SEGMENTS; i++) {
    digitalWrite(segments[i], displayNumber[num][i]);
  }
}


void checkBarrierSensor1(){
  //if (state==
}

void checkBarrierSensor2(){
  
}

void led_RGB(int red_value, int green_value, int blue_value)
 {
  analogWrite(LED_RED, red_value);
  analogWrite(LED_GREEN, green_value);
  analogWrite(LED_BLUE, blue_value);
}
