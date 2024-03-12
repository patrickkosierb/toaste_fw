#include <esp_log.h>
#include <esp_system.h>
#include <nvs_flash.h>
#include <sys/param.h>
#include <string.h>

#include "esp_camera.h"
#include "PubSubClient.h" // Connect and publish to the MQTT broker
#include "WiFi.h" // Enables the ESP32 to connect to the local network (via WiFi)

/* GPIO ESP32 CAM */
#define CAM_PIN_PWDN 32
#define CAM_PIN_RESET -1 //software reset will be performed
#define CAM_PIN_XCLK 0
#define CAM_PIN_SIOD 26
#define CAM_PIN_SIOC 27
#define CAM_PIN_D7 35
#define CAM_PIN_D6 34
#define CAM_PIN_D5 39
#define CAM_PIN_D4 36
#define CAM_PIN_D3 21
#define CAM_PIN_D2 19
#define CAM_PIN_D1 18
#define CAM_PIN_D0 5
#define CAM_PIN_VSYNC 25
#define CAM_PIN_HREF 23
#define CAM_PIN_PCLK 22

/* MQTT Config. */
#define PORT_LISTEN 1883

const char* ssid = "Patrick\342\200\231s iPhone";               
const char* wifi_password = "";
const char* mqtt_server = "172.20.10.4";  // IP of the MQTT broker
const char* topic_left_camera = "testing";
const char* topic_start = "start";
const char* mqtt_username = "pi"; 
const char* mqtt_password = "toast";
const char* clientID = "client_esp"; 
const char* ack = "ACK";
const char* fin = "FIN";
camera_fb_t* fb;
WiFiClient wifiClient;
PubSubClient client(wifiClient); 

uint8_t take_pic = 0;

void capture_frame(void){
    
    fb = esp_camera_fb_get();
    if(!fb){
      Serial.println("Capture failed."); 
      return;
    }
    Serial.println("Took a picture!");
    unsigned long start_t = millis();
    if(!client.publish(topic_left_camera, fb->buf,fb->len)){
        esp_camera_fb_return(fb);
        Serial.println("Failed to send.");
        return;}
    Serial.println(millis()-start_t);

    esp_camera_fb_return(fb);
 }

void init_camera()
{
    static camera_config_t camera_config = {
        .pin_pwdn = CAM_PIN_PWDN,
        .pin_reset = CAM_PIN_RESET,
        .pin_xclk = CAM_PIN_XCLK,
        .pin_sccb_sda = CAM_PIN_SIOD,
        .pin_sccb_scl = CAM_PIN_SIOC,
        .pin_d7 = CAM_PIN_D7,
        .pin_d6 = CAM_PIN_D6,
        .pin_d5 = CAM_PIN_D5,
        .pin_d4 = CAM_PIN_D4,
        .pin_d3 = CAM_PIN_D3,
        .pin_d2 = CAM_PIN_D2,
        .pin_d1 = CAM_PIN_D1,
        .pin_d0 = CAM_PIN_D0,
        .pin_vsync = CAM_PIN_VSYNC,
        .pin_href = CAM_PIN_HREF,
        .pin_pclk = CAM_PIN_PCLK,
    
        .xclk_freq_hz = 20000000, //XCLK 20MHz or 10MHz for OV2640 double FPS (Experimental)
        .ledc_timer = LEDC_TIMER_0,
        .ledc_channel = LEDC_CHANNEL_0,
    
        .pixel_format = PIXFORMAT_JPEG, //YUV422,GRAYSCALE,RGB565,JPEG
        .frame_size = FRAMESIZE_QVGA, //QQVGA-UXGA, For ESP32, do not use sizes above QVGA when not JPEG. The performance of the ESP32-S series has improved a lot, but JPEG mode always gives better frame rates.
    
        .jpeg_quality = 12, //0-63, for OV series camera sensors, lower number means higher quality
        .fb_count = 1,       //When jpeg mode is used, if fb_count more than one, the driver will work in continuous mode.
        .grab_mode = CAMERA_GRAB_WHEN_EMPTY,
    };

    if (esp_camera_init(&camera_config) != ESP_OK){
        Serial.printf("Failed to initialize camera.");
        return;
    }
}

void init_wifi(){
  Serial.print("Connecting to wifi"); 
  WiFi.begin(ssid, wifi_password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.print("\n Connected to ");
  Serial.println(ssid);

}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(clientID, mqtt_username, mqtt_password)) {
      Serial.println("connected");
      client.subscribe(topic_start);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void control(char* topic, byte* payload, unsigned int length) {
  char buff[1];
  buff[0] = (char)payload[0];
  if(buff[0]=='1'){
    Serial.println("Starting captures");
    take_pic = 1;
    }
   else{
    Serial.println("Stopping captures");
    take_pic = 0;
   }

}

 
void setup() {
  Serial.begin(115200);
  init_camera();
  init_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(control);
  client.setBufferSize(10000);

}

void loop() {

    if (!client.connected()) {
      reconnect();
    }
    client.loop();
    
    if(take_pic){
      capture_frame();
    }
    
    
}
