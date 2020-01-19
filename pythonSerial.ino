#include <FastLED.h>
//    in Serial Input Basics   http://forum.arduino.cc/index.php?topic=396450.0

#define NUM_LEDS 6
#define DATA_PIN 3

CRGB leds[NUM_LEDS];

const byte numChars = 45;
char receivedChars[numChars];

boolean newData = false;


void setup() {
  FastLED.addLeds<WS2811, DATA_PIN, RGB>(leds, NUM_LEDS);
  Serial.begin(115200);
  Serial.println("<Arduino is ready>");
}


void loop() {
  recvWithStartEndMarkers();
  //replyToPython();

  //   for (int i = 0; i < 42; i++) {
  //    leds[i] = CRGB::Red;
  //Serial.print("<");
  //Serial.print(receivedChars);
  //Serial.print('>');
  
  if (newData == true) {
    for (int i = 0; i < 42; i++) {
      if (receivedChars[i] == '2') {
        leds[i] = CRGB::Yellow;
      }
      if (receivedChars[i] == '1') {
        leds[i] = CRGB::Green;
      }
      if (receivedChars[i] == '0') {
        leds[i] = CRGB::Black;
      }
    }
    newData = false;
  }

  //    else if (receivedChars[i] == "1") {
  //      leds[i] = CRGB::Yellow;
  //    }
  //    else {
  //      leds[i] = CRGB::Black;
  //    }
  // }
  FastLED.show();
}

void recvWithStartEndMarkers() {
  static boolean recvInProgress = false;
  static byte ndx = 0;
  char startMarker = '<';
  char endMarker = '>';
  char rc;

  while (Serial.available() > 0 && newData == false) {
    rc = Serial.read();

    if (recvInProgress == true) {
      if (rc != endMarker) {
        receivedChars[ndx] = rc;
        ndx++;
        if (ndx >= numChars) {
          ndx = numChars - 1;
        }
      }
      else {
        receivedChars[ndx] = '\0'; // terminate the string
        recvInProgress = false;
        ndx = 0;
        newData = true;
      }
    }

    else if (rc == startMarker) {
      recvInProgress = true;
    }
  }
}

void replyToPython() {
  if (newData == true) {
    //Serial.print("<");
    //Serial.print(receivedChars);
    //Serial.print('>');
    //newData = false;
  }
}
