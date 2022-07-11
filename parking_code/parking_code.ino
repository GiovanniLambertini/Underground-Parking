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
#define CODE_LENGTH 7
#define INITIAL_CHAR '*'
#define FINAL_CHAR '#'

#define INITIAL_STATE 0
#define ACCESS_REQUEST 1
#define BARRIER_ACTIVE 2
//#define BARRIER_SENSOR2_ACTIVE 2
#define FINAL_STATE 3
#define SEC_LED_RGB 5
#define SEC_BARRIER 1
#define BARRIER_DELAY 15
#define BARRIER_STEPS 85
#define BARRIER_DOWN 34
#define BARRIER_UP 119


Servo servo;
int slots[NUM_SLOTS]={PARK1, PARK2, PARK3, PARK4, PARK5, PARK6};
bool slotsState[NUM_SLOTS];                                                                     // Occupato - false, Libero - true
int segments[DISPLAY_SEGMENTS] {LED_A, LED_B, LED_C, LED_D, LED_E, LED_F, LED_G, LED_DP};       // Pin display 7 segmenti
volatile int state;
byte available_parks;
byte bluetoothData;
char buttonCode[CODE_LENGTH];
int buttonState;                                                                                 // 0: stato iniziale, 1: *, 2:*X, 3:*XX, 4:*XXX, 5:*XXXX, 6:*XXXXX, 7:*XXXXX#
int bluetoothState;                                                                              // -1: stato iniziale (attesa dato), 0: attesa tipo del pacchetto, 1: attesa pacchetto di tipo 0, 2: attesa pacchetto di tipo 1, 3: attesa terminatore di pacchetto
int barrierState;                                                                                // -1 stato iniziale, 0: apertura barrirera, 1: entrata/uscita
int openingBarrierState;  
int millisBarrierState;  
bool openingBarrier;                                                                       
bool entering;
unsigned long millisLedRgb;
unsigned long millisBarrier;

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
  buttonState=0;
  bluetoothData=-1;
  bluetoothState = -1;
  openingBarrierState = -1;
  available_parks=0;
  millisLedRgb=0;
  
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
  servo.write(BARRIER_DOWN);
}

void loop() {
  
  char button = customKeypad.getKey();                     // Leggo il bottone premuto

  if (button) {                                            //Se è stato premuto un bottone
    Serial.println(button);
     buttonCode[buttonState]=button;
    if (button == INITIAL_CHAR){                           //Carattere *, resetto lo stato
      buttonState++;
    }
    else if (buttonState>=1 && buttonState<CODE_LENGTH-1){              //Nuova cifra, aggiorno lo stato
      buttonState++;
    }
    else if (buttonState == CODE_LENGTH-1){   
      if (button == FINAL_CHAR){
         //Invia il pacchetto dati con il codice inserito
         Serial1.write(0xff);
         Serial1.write(0x00);                            //Tipo pacchetto 0
         for (int i=0; i<CODE_LENGTH; i++)
           Serial1.write(buttonCode[i]);                 //Numero dello slot
         Serial1.write(0xfe);       
         Serial.println (buttonCode[1]);
      }
      buttonState=0;
    }
  }

  if (Serial1.available()>0){
    bluetoothData = Serial1.read();
    Serial.println(bluetoothData);

    switch (bluetoothState){
      case -1:            
        if (bluetoothData==0xff)
            bluetoothState=0;
        break;

      case 0:
        if (bluetoothData==0x00)
          bluetoothState=1;
        else if (bluetoothData==0x01)
          bluetoothState=2;          
        
        break;
        
      case 1: 
        if (bluetoothData==0){                                
            led_RGB(255, 0, 0); // Led Red, Error 
            millisLedRgb = millis();
        }
        else {  
            led_RGB(0, 255, 0); // Led Green, open barrier
            millisLedRgb = 0;
            barrierState=0;

            if (bluetoothData==1){                                  //Entrata
               Serial.println("Entrata");
               entering = true;
            }

            else if (bluetoothData==2){                             //Uscita
               Serial.println("Uscita");
               entering = false;
            }

            openingBarrierState = 0;
            millisBarrierState = millis();
            openingBarrier = true;               
        }

        bluetoothState=3;   
        break;

      case 2:
        available_parks = bluetoothData;
        display_number(available_parks);

        bluetoothState=3;  
        break;
        
      case 3:
        if (bluetoothData==0xfe)
            bluetoothState=-1;
        break;
          
      default:                                              //Se non ho dati sulla seriale
        break;
    }
  }

  if (millisLedRgb !=0 && (millis()-millisLedRgb) >= SEC_LED_RGB*1000){           //Spengo il led
      Serial.println (millisLedRgb-millis());
      led_RGB(0, 0, 0);
      millisLedRgb=0;
  }

  checkBarrier();

  if (openingBarrierState != -1){                                           //apertura graduale sbarra
      if (millisBarrierState - millis() >= (unsigned long) openingBarrierState*BARRIER_DELAY){
        if (openingBarrier)
           servo.write(BARRIER_DOWN+openingBarrierState);
        else
           servo.write(BARRIER_UP-openingBarrierState);
           
        if (openingBarrierState == BARRIER_STEPS-1)
           openingBarrierState = -1;
        else
           openingBarrierState++;
      }
  }

  for (int i=0; i<NUM_SLOTS; i++){
    checkSlot(i);
  }

}


void display_number(int num) {                //Stampa un numero sul display 7 segmenti e accendi il led di conseguenza
  
  for(int i=0; i<DISPLAY_SEGMENTS; i++) {
    digitalWrite(segments[i], displayNumber[num][i]);
  }
}

void checkSlot(int i){
  int newState = digitalRead(slots[i]);
  
  if (slotsState[i] != newState){          //Se lo stato del pacheggio è cambiato
    Serial.println(i);
    slotsState[i] = newState;

    Serial.println(i);
    
    //Invia il pacchetto dati con l'aggiornamento dello stato del posto
    Serial1.write(0xff);
    Serial1.write(0x01);                       //Pacchetto tipo 1
    Serial1.write((char) 'A');                 //Sezione dello slot
    Serial1.write((char) i+1);                 //Id dello slot
    Serial1.write((char) slotsState[i]);       //1 - Libero, 0 - Occupato
    Serial1.write(0xfe);

    Serial.print("Stato parcheggio");
    Serial.print(i+1);
    Serial.print(": ");
    Serial.println(digitalRead(slots[i])); 
  }
}

void led_RGB(int red_value, int green_value, int blue_value)
 {
  analogWrite(LED_RED, red_value);
  analogWrite(LED_GREEN, green_value);
  analogWrite(LED_BLUE, blue_value);
}

void checkBarrier(){
  switch (barrierState){
      case 0:
      if (entering){
         if (digitalRead(BARRIER_SENSOR2)==LOW)   //entering -> Aspetto l'attivazione del sensore 2
            barrierState=1;
      }
      else{
         if (digitalRead(BARRIER_SENSOR1)==LOW)
            barrierState=1;
      }
      break;

      case 1:
         if (entering){
            if (digitalRead(BARRIER_SENSOR2)==HIGH){   //entering -> Aspetto la disattivazione del sensore 2
                barrierState=2;
                millisBarrier=millis();
            }
         }
         else{
            if (digitalRead(BARRIER_SENSOR1)==HIGH){
                barrierState=2;
                millisBarrier=millis();
            }
         }
         
         break;
      case 2:
         if ((entering && (digitalRead(BARRIER_SENSOR2)==HIGH)&& (millis()-millisBarrier >= 1000*SEC_BARRIER))){
                 led_RGB(0, 0, 0);
                 openingBarrierState = 0;
                 openingBarrier = false;
                 barrierState=-1;
                 millisBarrierState = millis();
         }
         else if (!entering && (digitalRead(BARRIER_SENSOR1)==HIGH)&& (millis()-millisBarrier >= 1000*SEC_BARRIER)){
                 led_RGB(0, 0, 0);
                 openingBarrierState = 0;
                 openingBarrier = false;
                 barrierState=-1;
                 millisBarrierState = millis();
         }
            
         break;
  }
}
