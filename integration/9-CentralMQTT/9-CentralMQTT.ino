/******************************************************************************
 * Central de Monitoramento Wi-Fi via MQTT (Broker Público)
 *
 * - Lê sensores (DHT11, LDR, acelerômetro MMA8452Q) de um IoT DevKit.
 * - Conecta em test.mosquitto.org (sem autenticação).
 * - Publica leituras em "esp32/monitor/data" a cada X segundos (JSON).
 * - Inscreve-se em "esp32/monitor/cmd" para receber mensagens:
 *    - Ao receber "L", inverte o LED (pino 13).
 *
 * Adaptado do código original da RoboCore (PROIoT) por [Seu Nome / Data].
 ******************************************************************************/

// --- Bibliotecas ---
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include "RoboCore_MMA8452Q.h"
#include <soc/sens_reg.h> // Para leitura de registradores (custom analogRead do LDR)

// --- Configurações Wi-Fi ---
const char* REDE  = "LAB INFORMATICA ENGENHARIA";
const char* SENHA = "logicpro";

// --- Configurações do Broker MQTT (Mosquitto público) ---
const char* BROKER_MQTT  = "131.255.82.115";
const uint16_t PORTA_MQTT = 1883;

// Client ID (nome único) para identificar o dispositivo no broker
const char* CLIENT_ID    = "ESP32MonitorClientN";

// Tópicos para publicar/inscrever
const char* TOPICO_PUB = "esp32/N/monitor/data"; // Envio de dados do sensor
const char* TOPICO_SUB = "esp32/N/monitor/cmd";  // Recebimento de comandos (ex: "ON")

// --- Objetos de rede e MQTT ---
WiFiClient wifiClient;         
PubSubClient MQTT(wifiClient);

// --- Acelerômetro ---
MMA8452Q acelerometro;

// --- Pino do DHT11 ---
const int PINO_DHT = 12;
DHT dht(PINO_DHT, DHT11); // Sensor padrão do DevKit

// Variáveis para leituras do DHT
float temperatura;
float umidade;

// --- Pino do LED ---
const int PINO_LED = 13;
int estadoLED = LOW; // Estado inicial (desligado)

// --- Pino do LDR ---
const int PINO_LDR = 15;
int leitura_LDR = 0;
uint32_t adc_register;  // Para manipular registrador e custom analogRead()

// Função customARead() (declaração)
int customARead(int pin);

// --- Controle de tempo para envio de mensagens ---
unsigned long proximoEnvio = 0;
// Exemplo: enviar dados a cada 30 segundos
const unsigned long INTERVALO = 3000;

// --- Controle de tempo para tentativa de reconexão ---
unsigned long proximaTentativa = 0;

// --- Variável para comparar mensagem recebida vs. mensagem enviada ---
String mensagem_enviada;

// --------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Central de Monitoramento WiFi - Broker Público MQTT ===");

  // Inicia sensor DHT
  dht.begin();

  // Inicia acelerômetro
  acelerometro.init();

  // Configura pino do LED
  pinMode(PINO_LED, OUTPUT);
  digitalWrite(PINO_LED, estadoLED);

  // Configura pino LDR
  pinMode(PINO_LDR, INPUT);
  // Salva estado atual do registrador
  adc_register = READ_PERI_REG(SENS_SAR_READ_CTRL2_REG);

  // Conecta ao Wi-Fi
  Serial.print("Conectando em: ");
  Serial.println(REDE);
  WiFi.mode(WIFI_STA);
  WiFi.begin(REDE, SENHA);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Conectado!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  // Configura o broker MQTT e callback
  MQTT.setServer(BROKER_MQTT, PORTA_MQTT);
  MQTT.setCallback(mqtt_callback);

  Serial.print("Broker: ");
  Serial.print(BROKER_MQTT);
  Serial.print("  Porta: ");
  Serial.println(PORTA_MQTT);
  Serial.print("Tópicos => Pub: ");
  Serial.println(TOPICO_PUB);
  Serial.print("             Sub: ");
  Serial.println(TOPICO_SUB);
}

// --------------------------------------------------------------------------
void loop() {
  // Mantém a comunicação MQTT
  MQTT.loop();

  // Se não está conectado ao broker, tenta reconectar periodicamente
  if (!MQTT.connected()) {
    if (millis() > proximaTentativa) {
      Serial.println("\nTentando conectar ao broker MQTT...");
      // Conexão sem autenticação (broker público)
      if (MQTT.connect(CLIENT_ID)) {
        Serial.println("Conectado ao broker!");
        // Faz inscrição no tópico de comandos
        if (MQTT.subscribe(TOPICO_SUB)) {
          Serial.print("Inscrito com sucesso no tópico: ");
          Serial.println(TOPICO_SUB);
        } else {
          Serial.println("Falha ao se inscrever no tópico de comandos.");
        }
      } else {
        Serial.print("Falha na conexão. Erro: ");
        Serial.println(MQTT.state());
        Serial.println("Tentando novamente em 5s...");
      }
      proximaTentativa = millis() + 5000;
    }
  } else {
    // Se já está conectado, podemos publicar periodicamente
    if (millis() > proximoEnvio) {
      // --- Ler LDR (usando custom analogRead) e mapear para 0 a 100 ---
      leitura_LDR = customARead(PINO_LDR);
      leitura_LDR = map(leitura_LDR, 0, 4095, 100, 0); // Quanto maior ADC, menor luminosidade

      // --- Ler acelerômetro ---
      acelerometro.read(); // x, y, z ficam em acelerometro.x, .y, .z

      // --- Ler DHT11 ---
      temperatura = dht.readTemperature();
      umidade     = dht.readHumidity();

      if (isnan(temperatura) || isnan(umidade)) {
        Serial.println("Falha na leitura do Sensor DHT!");
      } else {
        // Monta JSON com 6 campos
        DynamicJsonDocument json( JSON_OBJECT_SIZE(6) );

        // Atribui leituras aos campos (pode renomear "Temperatura", "Umidade", etc.)
        json["Temperatura"]   = temperatura;
        json["Umidade"]       = umidade;
        json["Luminosidade"]  = leitura_LDR;
        json["Eixo_X"]        = acelerometro.x;
        json["Eixo_Y"]        = acelerometro.y;
        json["Eixo_Z"]        = acelerometro.z;

        // Serializa para string
        size_t tamanho = measureJson(json) + 1;
        char mensagem[tamanho];
        serializeJson(json, mensagem, tamanho);

        mensagem_enviada = mensagem; // Guarda para comparação na callback

        // Publica no tópico de dados
        Serial.print("\nPublicando em ");
        Serial.print(TOPICO_PUB);
        Serial.print(": ");
        Serial.println(mensagem);

        MQTT.publish(TOPICO_PUB, mensagem);
      }

      // Define o próximo envio
      proximoEnvio = millis() + INTERVALO;
    }
  }
}

// --------------------------------------------------------------------------
// Callback chamada ao chegar mensagem no tópico inscrito (TOPICO_SUB)
void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  String mensagem_recebida;
  for (unsigned int i = 0; i < length; i++) {
    mensagem_recebida += (char)payload[i];
  }

  Serial.print("\nMensagem recebida no tópico [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(mensagem_recebida);

  // Evita reagir à própria mensagem publicada, caso o broker ecoe
  if (mensagem_recebida != mensagem_enviada) {
    // Se receber "L", alterna o LED
    if (mensagem_recebida == "ON") {
      estadoLED = HIGH;
      digitalWrite(PINO_LED, estadoLED);
      Serial.print("LED agora está: ");
      Serial.println(estadoLED == HIGH ? "LIGADO" : "DESLIGADO");
    }
    if (mensagem_recebida == "OFF") {
      estadoLED = LOW;
      digitalWrite(PINO_LED, estadoLED);
      Serial.print("LED agora está: ");
      Serial.println(estadoLED == HIGH ? "LIGADO" : "DESLIGADO");
    }
  }
}

// --------------------------------------------------------------------------
// Leitura customizada do ADC para o LDR (solução com registradores)
int customARead(int pin) {
  uint32_t wifi_register = READ_PERI_REG(SENS_SAR_READ_CTRL2_REG);
  WRITE_PERI_REG(SENS_SAR_READ_CTRL2_REG, adc_register);
  SET_PERI_REG_MASK(SENS_SAR_READ_CTRL2_REG, SENS_SAR2_DATA_INV);

  int value = analogRead(pin); // Leitura do ADC

  WRITE_PERI_REG(SENS_SAR_READ_CTRL2_REG, wifi_register);
  return value;
}
