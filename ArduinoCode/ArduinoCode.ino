#include <Servo.h>

#define sensor A0
#define potency A1

Servo servo;

const unsigned char flame = 3;
const unsigned char smoke = 2;
const unsigned char buzzer = 10;

const unsigned char gas_switcher = 8;
const unsigned char led = 9;
const unsigned char motor = 11;
const unsigned char left = 12;
const unsigned char right = 13; 

bool smoke_emergency_state = false;
bool fire_emergency_state = false;

int input = 0;
bool controller_led = false;

void setup()
{
  pinMode (flame, INPUT) ;
  pinMode (smoke, INPUT) ;
  pinMode (buzzer, OUTPUT) ;
  pinMode(led, OUTPUT);
  
  pinMode(motor, OUTPUT);
  pinMode(left, OUTPUT);

  pinMode(sensor, INPUT);
  pinMode(potency, INPUT);

  servo.attach(8);
  servo.write(0);
  
  digitalWrite(led, LOW);
  Serial.begin(9600);
}

void loop()
{
  while (Serial.available())
  {
    input = Serial.read();
  }

  float sens_value = analogRead(smoke);
  int f = digitalRead(flame) ;
  int s = digitalRead(smoke);

  fire_emergency_state = (f == HIGH);
  smoke_emergency_state = (s == HIGH);

  if (fire_emergency_state or smoke_emergency_state)
  {
    digitalWrite(led, HIGH);
    digitalWrite(buzzer, HIGH);
    servo.write(180);
  }
  else
  {
    fire_emergency_state = false;
    smoke_emergency_state = false;
    digitalWrite(led, LOW);
    digitalWrite(buzzer, LOW);
    servo.write(0);
  }
  delay(100);
  
  switch (input)
  {
    case '4': // ESQUERDA
      digitalWrite(motor,HIGH);
      digitalWrite(left,HIGH);
      digitalWrite(left,LOW);
      input = 0;
      break;  
    case '6':
      digitalWrite(motor,LOW);
      digitalWrite(left,LOW);
      digitalWrite(right,LOW);
      input = 0;
      break;
    case '7':
      Serial.print(analogRead(sensor) * 0.488);
      input = 0;
      break;
    case '8':
      Serial.print(analogRead(potency));
      input = 0;
      break;
    case 's':
      Serial.print(smoke_emergency_state);
      input = 0;
      break;
    case 'f':
      Serial.print(fire_emergency_state);
      input = 0;
      break;
  }
  input = 0;
}

void manage_leds(int led, bool* controller_led)
{
  if (*controller_led)
  {
    digitalWrite(led, LOW);
    switch_bool(controller_led);
  }
  else
  {
    digitalWrite(led, HIGH);
    switch_bool(controller_led);
  }
}

void switch_bool(bool *led) {
  *led ? *led = false : *led = true;
}
