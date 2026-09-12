// ============================================================
// BAI GIUA KY - IoT, UEH (mo phong Wokwi)
// Kien truc theo dung rubric: Slave (ESP32) <-> Router (WiFi) <-> Cloud (server
//                              tu xay, deploy Render) <-> Control and Display
// Tai dung cam bien/actuator tu Tram chinh cua do an cuoi ky (DHT22, LDR,
// Relay->Quat, LED PWM). KHONG dung LoRa/tram ve tinh - giua ky chi can 1 ESP32.
// KHONG dung Blynk - Dashboard tu xay (xem webapp/), ESP32 goi HTTPS len do.
// ============================================================
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// ==== Cau hinh WiFi mo phong Wokwi (mang ao khong can mat khau) ====
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

// ==== Dia chi server Cloud tu xay (deploy tren Render) ====
// DOI thanh dia chi that sau khi deploy xong webapp/ len Render.
const char* SERVER_URL = "https://TEN-APP-CUA-BAN.onrender.com/api/data";

// ==== Chan phan cung (giong Tram chinh do an cuoi ky) ====
#define DHTPIN 13
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

const int LDR_PIN = 34;
const int RELAY_FAN_PIN = 26;
const int LED_PWM_PIN = 27;
const int LED_PWM_FREQ = 5000;
const int LED_PWM_RESOLUTION = 8; // 0-255
const int LED_PWM_CHANNEL = 0;

// ==== Nguong bat/tat quat (hysteresis, tranh nhap nhay) ====
const float NGUONG_BAT_NHIETDO = 32.0;
const float NGUONG_BAT_DOAM = 80.0;
const float NGUONG_TAT_NHIETDO = 30.0;
const float NGUONG_TAT_DOAM = 75.0;

// ==== Bien trang thai ====
float nhietDoHienTai = NAN;
float doAmHienTai = NAN;
int anhSangRawHienTai = 0;
bool quatDangBat = false;
int pwmDenHienTai = 0;

bool cheDoThuCong = false; // true = dieu khien quat bang tay tu Dashboard
bool quatThuCong = false;  // trang thai quat khi dang o che do thu cong

unsigned long lanDocCamBienCuoi = 0;
const unsigned long CHU_KY_DOC_CAM_BIEN = 2000;
unsigned long lanGuiServerCuoi = 0;
const unsigned long CHU_KY_GUI_SERVER = 2000;

// ==== Logic thuan (giong het control_logic ben do an cuoi ky) ====
bool quyetDinhBatQuat(float nhietDo, float doAm, bool dangBat) {
  if (isnan(nhietDo) || isnan(doAm)) return dangBat; // du lieu loi, giu nguyen
  if (dangBat) {
    if (nhietDo <= NGUONG_TAT_NHIETDO && doAm <= NGUONG_TAT_DOAM) return false;
    return true;
  } else {
    if (nhietDo > NGUONG_BAT_NHIETDO || doAm > NGUONG_BAT_DOAM) return true;
    return false;
  }
}

int tinhPwmDen(int anhSangRaw) {
  int raw = constrain(anhSangRaw, 0, 4095);
  return 255 - (raw * 255 / 4095); // toi (raw thap) -> den sang manh hon
}

// Gui so lieu cam bien len server (Cloud), nhan lai lenh dieu khien dang cho
// TRONG CUNG 1 request - khong can goi rieng 1 lan nua de lay lenh.
void guiVaNhanTuServer() {
  if (WiFi.status() != WL_CONNECTED) return;

  WiFiClientSecure client;
  client.setInsecure(); // bo qua kiem tra chung chi TLS - don gian cho do an hoc tap

  HTTPClient http;
  http.setTimeout(5000); // mang loi cung khong treo chuong trinh qua lau
  if (!http.begin(client, SERVER_URL)) {
    Serial.println("Khong mo duoc ket noi toi server.");
    return;
  }
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<256> goiGui;
  if (isnan(nhietDoHienTai)) goiGui["nhietDo"] = nullptr; else goiGui["nhietDo"] = nhietDoHienTai;
  if (isnan(doAmHienTai)) goiGui["doAm"] = nullptr; else goiGui["doAm"] = doAmHienTai;
  goiGui["anhSang"] = anhSangRawHienTai;
  goiGui["quatDangBat"] = quatDangBat;
  goiGui["pwmDen"] = pwmDenHienTai;

  String noiDungGui;
  serializeJson(goiGui, noiDungGui);

  int maPhanHoi = http.POST(noiDungGui);
  if (maPhanHoi == 200) {
    StaticJsonDocument<128> goiNhan;
    DeserializationError loi = deserializeJson(goiNhan, http.getString());
    if (!loi) {
      cheDoThuCong = goiNhan["cheDoThuCong"] | false;
      quatThuCong = goiNhan["quatThuCong"] | false;
    } else {
      Serial.print("Loi doc JSON tra ve: ");
      Serial.println(loi.c_str());
    }
  } else {
    Serial.print("Gui server that bai, ma loi HTTP: ");
    Serial.println(maPhanHoi);
  }
  http.end();
}

void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("Bai giua ky - Slave ESP32 <-> Router <-> Cloud tu xay");

  dht.begin();

  pinMode(RELAY_FAN_PIN, OUTPUT);
  digitalWrite(RELAY_FAN_PIN, LOW);

  ledcSetup(LED_PWM_CHANNEL, LED_PWM_FREQ, LED_PWM_RESOLUTION);
  ledcAttachPin(LED_PWM_PIN, LED_PWM_CHANNEL);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Da ket noi WiFi. Dia chi IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  unsigned long bayGio = millis();
  if (bayGio - lanDocCamBienCuoi >= CHU_KY_DOC_CAM_BIEN) {
    lanDocCamBienCuoi = bayGio;

    nhietDoHienTai = dht.readTemperature();
    doAmHienTai = dht.readHumidity();
    anhSangRawHienTai = analogRead(LDR_PIN);

    bool quatTuDong = quyetDinhBatQuat(nhietDoHienTai, doAmHienTai, quatDangBat);
    quatDangBat = cheDoThuCong ? quatThuCong : quatTuDong;
    digitalWrite(RELAY_FAN_PIN, quatDangBat ? HIGH : LOW);

    pwmDenHienTai = tinhPwmDen(anhSangRawHienTai);
    ledcWrite(LED_PWM_CHANNEL, pwmDenHienTai);

    Serial.print("Nhiet do: "); Serial.print(nhietDoHienTai);
    Serial.print(" C, Do am: "); Serial.print(doAmHienTai);
    Serial.print(" %, Anh sang: "); Serial.print(anhSangRawHienTai);
    Serial.print(", Quat: "); Serial.print(quatDangBat ? "BAT" : "TAT");
    Serial.print(cheDoThuCong ? " (thu cong)" : " (tu dong)");
    Serial.print(", PWM den: "); Serial.println(pwmDenHienTai);
  }

  // Day len Cloud + nhan lenh dieu khien (Display + Control - muc 3 cua rubric)
  if (bayGio - lanGuiServerCuoi >= CHU_KY_GUI_SERVER) {
    lanGuiServerCuoi = bayGio;
    guiVaNhanTuServer();
  }
}
