// ESP32 Rock Paper Scissors Player
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Configurazione WiFi
const char* ssid = "your_ssid";
const char* password = "your_password";

// Configurazione Server
const char* serverUrl = "http://your_local_ip:5000";
const int playerNumber = 1;  // Cambia a 2 per il secondo ESP32
const int ledPin = 22;        // GPIO22 per il LED verde

// Stato del gioco
bool isMyTurn = false;
String currentMove = "";
String gamePhase = "IN_PROGRESS";
unsigned long lastCheckTime = 0;
unsigned long turnStartTime = 0;
bool turnJustStarted = false;

// Configurazione temporizzazione
const unsigned long checkInterval = 2000;  // Controlla ogni 2 secondi
const unsigned long moveDelay = 3000;    // Attende 3 secondi prima di fare la mossa

void setup() {
  Serial.begin(115200);
  pinMode(ledPin, OUTPUT);
  
  // Inizializzazione più robusta del generatore di numeri casuali
  int seed = 0;
  for(int i = 0; i < 8; i++) {
    seed = (seed << 4) + analogRead((36 + i) % 40);  // Legge da diversi pin analogici
    delay(1);  // Piccolo delay per variare ulteriormente le letture
  }
  randomSeed(seed ^ micros());
  
  // Connessione WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnesso al WiFi");
}

void loop() {
  if (millis() - lastCheckTime >= checkInterval) {
    checkGameState();
    lastCheckTime = millis();
  }

  if (isMyTurn && currentMove == "") {
    digitalWrite(ledPin, HIGH);  // Accendi LED quando è il tuo turno
    
    // Se il turno è appena iniziato, memorizza il tempo
    if (!turnJustStarted) {
      turnStartTime = millis();
      turnJustStarted = true;
      Serial.println("Turno iniziato");
    }
    
    // Aspetta moveDelay millisecondi prima di fare la mossa
    if (millis() - turnStartTime >= moveDelay) {
      makeRandomMove();
      turnJustStarted = false;
      Serial.println("Mossa effettuata");
    }
  } else {
    digitalWrite(ledPin, LOW);
    turnJustStarted = false;
  }

  // Reset della mossa se è il nostro turno
  if (isMyTurn && gamePhase == "IN_PROGRESS") {
    currentMove = "";
  }
}

void checkGameState() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(serverUrl) + "/game_state/" + String(playerNumber);
    
    http.begin(url);
    int httpCode = http.GET();
    
    if (httpCode > 0) {
      String payload = http.getString();
      DynamicJsonDocument doc(1024);
      deserializeJson(doc, payload);
      
      isMyTurn = doc["is_turn"];
      gamePhase = doc["game_phase"].as<String>();
      
      // Debug
      Serial.print("Game Phase: ");
      Serial.println(gamePhase);
      Serial.print("Is My Turn: ");
      Serial.println(isMyTurn);
      
      // Reset della mossa quando cambia la fase di gioco
      if (gamePhase == "SET_COMPLETE" || gamePhase == "MATCH_COMPLETE") {
        currentMove = "";
        Serial.println("Reset mossa per nuova fase");
      }
    }
    http.end();
  }
}

void makeRandomMove() {
  const char* moves[] = {"rock", "paper", "scissors"};
  
  // Usa più fonti di entropia per la casualità
  int analog1 = analogRead(36);  // SVP pin
  int analog2 = analogRead(39);  // SVN pin
  int micros_val = (int)(micros() & 0xFF);
  
  // Combina le fonti di entropia
  int randomSeed = analog1 + analog2 + micros_val + playerNumber * 1000;
  randomSeed ^= (millis() & 0xFFFF);
  
  // Genera un numero casuale basato su tutte queste fonti
  random(randomSeed);
  int randomMove = random(3);
  
  // Aggiungi un'ulteriore variazione basata sul playerNumber
  randomMove = (randomMove + playerNumber + (millis() % 3)) % 3;
  
  String move = moves[randomMove];
  
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(serverUrl) + "/make_move";
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    
    DynamicJsonDocument doc(1024);
    doc["player"] = playerNumber;
    doc["move"] = move;
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    int httpCode = http.POST(jsonString);
    if (httpCode > 0) {
      currentMove = move;
      isMyTurn = false;
      Serial.print("Mossa inviata: ");
      Serial.println(move);
    }
    http.end();
  }
}