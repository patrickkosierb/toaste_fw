#include <esp_log.h>
#include <esp_system.h>
#include <nvs_flash.h>
#include <sys/param.h>
#include <string.h>
#include <esp_crc.h>
#include "driver/gpio.h"

#include <Wire.h>

#include "esp_camera.h"
//#include "PubSubClient.h" // Connect and publish to the MQTT broker
//#include "WiFi.h" // Enables the ESP32 to connect to the local network (via WiFi)

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

/* I2C COM */
#define I2C_SDA 15
#define I2C_SCL 14
#define I2C_SLAVE_ADDR 0x55
#define I2C_FREQ 100000

uint32_t i2count = 1;
uint8_t state = 0;
uint8_t take_pic = 0;//software sephamore
uint8_t pic_pross = 0;
bool isConfigured = 0;
static camera_fb_t* fb;
unsigned long start_t = 0;
uint32_t bytesLeft=0;
int start=0;
uint8_t capFail =0;

//error correction buffer
uint8_t pecBuff [32];
uint8_t tpBuff [32]; //idk but ok this is for pec
uint8_t pecLen=0;
int cy = 31;
uint8_t picStore [30000]; //Our own picture buffer so we can return the pointer immediately
uint32_t picLength = 0;

void onRequest(){
  if(state==1){
    //Serial.printf("on1Request: %d \n",picLength);
    writeToPecBuff(&capFail,1);
    writeToPecBuff((uint8_t*)&picLength,4);
    writeToPecBuff((uint8_t*)&picLength,4);
    writeToPecBuff((uint8_t*)&picLength,4);
    bytesLeft=picLength;
    state = 2;
  }else if(state == 2){
    //Serial.printf("on2Request: %d \n",bytesLeft);
    start = picLength - bytesLeft;
    if(bytesLeft>31){
      writeToPecBuff(((uint8_t*)(picStore))+start,cy);
      bytesLeft-=31;
    }else{
      writeToPecBuff(((uint8_t*)(picStore))+start,bytesLeft);
      state =3;
    }
  }else if(state==3){
    //Serial.printf("\non3Request: %d \n",i2count);
    writeToPecBuff((uint8_t*)&i2count,4);
    i2count++;
  }else{
    writeToPecBuff(0,1);
  }
  sendPecBuff();
  //Serial.print("onRequest: ");
  //Serial.println(millis()-start_t);
}

//written length must not exceed 31
void writeToPecBuff(uint8_t* data,uint8_t len){
  for(uint8_t i=0;i<len;i++){
    pecBuff[i+pecLen] = *(data+i);
    tpBuff[i+pecLen] = *(data+i);
  }
  pecLen+=len;
}
void sendPecBuff(){
  uint8_t pec = ~esp_crc8_le(~0x00,(uint8_t *)tpBuff,pecLen);
  Wire.flush();
  Wire.write(pecBuff,pecLen);
  Wire.write(&pec,1);
  pecLen=0;
}

void onReceive(int len){
  Serial.printf("onReceive[%d]: ", len);
  char cmd = 'p';
  uint8_t confbuff[32];
  if(Wire.available()){
    cmd = Wire.read();
    Serial.printf("%d",cmd);
  }
  uint8_t counter = 0;
  while(Wire.available()){
    confbuff[counter] = Wire.read();
    counter++;
  }
  Serial.println();
  if(cmd =='c'){
    Serial.println("set config");
    for(uint8_t i =0;i<25;i++){
      Serial.printf("%u ",*(confbuff+i));
    }

    sensor_t *s = esp_camera_sensor_get();
    s->set_quality(s,confbuff[0]);
    s->set_contrast(s,((int)confbuff[1])-2);//int
    s->set_brightness(s,((int)confbuff[2])-2);//int
    s->set_saturation(s,((int)confbuff[3])-2);//int
    s->set_sharpness(s,((int)confbuff[4])-2);//int
    s->set_denoise(s,(int)confbuff[5]);
    s->set_gainceiling(s,(gainceiling_t)confbuff[6]);
    s->set_colorbar(s,(int)confbuff[7]);
    s->set_whitebal(s,(int)confbuff[8]);
    s->set_gain_ctrl(s,(int)confbuff[9]);
    s->set_exposure_ctrl(s,(int)confbuff[10]);
    s->set_hmirror(s,(int)confbuff[11]);
    s->set_vflip(s,(int)confbuff[12]);

    s->set_aec2(s,(int)confbuff[13]);
    s->set_awb_gain(s,(int)confbuff[14]);
    s->set_agc_gain(s,(int)confbuff[15]);
    s->set_ae_level(s,((int)confbuff[16])-2);//int
    s->set_aec_value(s,((int)confbuff[17])*4);//uint16
    s->set_special_effect(s,(int)confbuff[18]);
    s->set_wb_mode(s,(int)confbuff[19]);
   
    s->set_dcw(s,(int)confbuff[20]);
    s->set_bpc(s,(int)confbuff[21]);
    s->set_wpc(s,(int)confbuff[22]);
    s->set_raw_gma(s,(int)confbuff[23]);
    s->set_lenc(s,(int)confbuff[24]);
    ghostCapFrame();
  }else if(cmd == 'r'){
    Serial.println("snap photo");
    ghostCapFrame();
    state=1;
  }else if(cmd == 'a'){
    if(confbuff[1]=='s'){
      //success
      state = 0;
    }else{
      //failed
      state=1;
    }
    
  }else{
     Serial.println("pinged");
  }
  Wire.flush();
}
void ghostCapFrame(void){
  if(pic_pross==0){
    take_pic = 1;
  }
}

void capture_frame(void){
    take_pic =0;
    pic_pross=1;
    //Serial.println("Cap");
    fb = esp_camera_fb_get();
    //Serial.println("ture"); 
    if(!fb){
      Serial.println("Capture failed."); 
      capFail = 1;
      
      return;
    }
    capFail = 0;
    picLength = fb->len;
    //Serial.println(picLength);
    for(uint32_t i =0;i<picLength;i++){
      picStore[i]=*(fb->buf+i);  
    }
    start_t = millis();
    
    esp_camera_fb_return(fb);
    Serial.println("RB");
    pic_pross=0;
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
    
        .xclk_freq_hz = 15000000, //XCLK 20MHz or 10MHz for OV2640 double FPS (Experimental)
        .ledc_timer = LEDC_TIMER_0,
        .ledc_channel = LEDC_CHANNEL_0,
    
        .pixel_format = PIXFORMAT_JPEG, //YUV422,GRAYSCALE,RGB565,JPEG,PIXFORMAT_RAW
        .frame_size = FRAMESIZE_240X240, //QQVGA-UXGA, For ESP32, do not use sizes above QVGA when not JPEG. The performance of the ESP32-S series has improved a lot, but JPEG mode always gives better frame rates.
    
        .jpeg_quality = 12, //0-63, for OV series camera sensors, lower number means higher quality
        .fb_count = 1,       //When jpeg mode is used, if fb_count more than one, the driver will work in continuous mode.
        .fb_location = CAMERA_FB_IN_PSRAM,
        .grab_mode = CAMERA_GRAB_LATEST,
    };

    if (esp_camera_init(&camera_config) != ESP_OK){
        Serial.printf("Failed to initialize camera.");
        return;
    }
}


void setup() {
  Serial.begin(115200);
  gpio_set_pull_mode((gpio_num_t)I2C_SDA,GPIO_FLOATING);
  gpio_set_pull_mode((gpio_num_t)I2C_SCL,GPIO_FLOATING);
  //Serial.setDebugOutput(true);
  init_camera();
  Wire.onReceive(onReceive);
  Wire.onRequest(onRequest);
  bool val = Wire.begin((uint8_t)I2C_SLAVE_ADDR,I2C_SDA,I2C_SCL,I2C_FREQ);
  Serial.print("hello ");
  Serial.println(val);
  //idk what this does
  ghostCapFrame();
}

void loop() {
    if(take_pic){
      Serial.println("Take a Picture");
      capture_frame();
      delay(100);
    }
}
