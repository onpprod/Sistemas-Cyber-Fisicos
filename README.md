# Deploy com FAAAST

Este guia descreve as etapas básicas para configurar e executar o FAAAST utilizando um arquivo `.AASX`.

## Etapa 1: Criação de um `.AASX`

Esta etapa será descrita em outro documento.

## Etapa 2: Configuração preliminar

1. **Adicionar o arquivo `.AASX`**
   - Copie o arquivo `.AASX` para a pasta `resources` e se necessário renomeie-o para `model.aasx`.

2. **Configurar o `config.json`**
   - As configurações abaixo são realizadas especificamente na chave `assetConnections. subscriptionProviders`.
   - Defina o caminho correto para a propriedade, seguindo este modelo:
     ```json
     "(Submodel)https://example.com/ids/sm/2594_4052_3052_7147, (Property)Control"
     ```
   
   - Ajuste o tópico correto para o sensor:
     ```json
     "topic": "spacexlab/AAS/AAS_ID/state"
     ```
   
   - Defina a chave correta no payload utilizando uma query JSONPath:
     ```json
     "query": "$.operational_state"
     ```
   
   - Configure o endereço correto do broker MQTT. Se for local, utilize o IP da máquina:
     ```json
     "serverUri": "tcp://131.255.82.115:1883"
     ```
   
   - Ajuste o `clientID` em cada propriedade para evitar conflitos com outros clientes conectados.
   Pode ser feito substituindo o valor YourName pelo nome do usuário.
     ```json
     "clientID": "FAAAST_YourName_operational_state"
     ```
     
   No fim, teremos a configuração no formato:
    ```
        {
            "@class": "de.fraunhofer.iosb.ilt.faaast.service.assetconnection.mqtt.MqttAssetConnection",
            "subscriptionProviders":
                    {
                        "(Submodel)https://example.com/ids/sm/2594_4052_3052_7147, (Property)Control":
                            {
                                "format": "JSON",
                                "topic": "spacexlab/AAS/AAS_ID/state",
                                "query": "$.operational_state"
                            }
                    },
            "serverUri": "tcp://131.255.82.115:1883",
            "clientID": "FAAAST_YourName_operational_state"
        }
    ```
    **Nota**: Substitua AAS_ID pelo ID do robô(disponínel na mesa de trabalho).



3. **Configurar a camada de integração**

    Ajustar as variáveis de ambiente presentes no docker-compose.yml.
    Substitua AAS_ID pelo ID do robô(disponínel na mesa de trabalho).
    
    ```
    MQTT_BROKER: 131.255.82.115
    MQTT_PORT: 1883
    MQTT_TOPIC_COMMAND: spacexlab/AAS/AAS_ID/command
    CLIENT_ID: your_name
    ```
   
    Ajustar os caminhos para as variaveis no OPCUA, correspondente a modelagem, no arquivo em integration/src/robot.
    É necessário sempre colocar a palavra "Value" ao final, para que ele acesse o valo da variável.

    - "operational_state" : Estado do robô.
    - "x_pick_position" : Posição X de Pick.
    - "y_pick_position" : Posição Y de Pick.
    - "z_pick_position" : Posição Z de Pick.
    - "x_place_position" : Posição X de Place.
    - "y_place_position" : Posição Y de Place.
    - "z_place_position" : Posição Z de Place.

    ````
    paths = {
        "operational_state": ["AASEnvironment", "Submodel:PickAndPlace", "Control", "Value"],

        "x_pick_position": ["AASEnvironment", "Submodel:PickAndPlace", "Pick", "X", "Value"],
        "y_pick_position": ["AASEnvironment", "Submodel:PickAndPlace", "Pick", "Y", "Value"],
        "z_pick_position": ["AASEnvironment", "Submodel:PickAndPlace", "Pick", "Z", "Value"],

        "x_place_position": ["AASEnvironment", "Submodel:PickAndPlace", "Place", "X", "Value"],
        "y_place_position": ["AASEnvironment", "Submodel:PickAndPlace", "Place", "Y", "Value"],
        "z_place_position": ["AASEnvironment", "Submodel:PickAndPlace", "Place", "Z", "Value"]
    }
   ````

## Etapa 3: Iniciar o serviço FAAAST

### Usando Docker
Com Docker instalado, utilizamos o comando abaixo na pasta raiz:
```sh
docker-compose up -d
```

---
Este guia garante que todas as configurações essenciais estejam corretas antes de iniciar o FAAAST. Caso tenha dúvidas, consulte a documentação oficial do FAAAST para mais detalhes.

## Etapa 4: Utilizando o AAS
Para interagir com o AAS, é necessário usar o UaExpert.
Para utilizar o AAS para mover os robôs é necessário ajustar os valores de Pick (X,Y,Z) e Place(X,Y,Z).
Para fins de teste, pode-se utilizar Pick (200,80,-80) e Place (-200,80,-80).
As opções de comando são:
- "start": realiza todo o movimento de Pick and Place.
- "calibrate": realiza a calibração do robô educacional.
- "move": realiza um único movimento utilizando apenas as coordenadas do Pick(X,Y,Z).
- "home": realiza um único movimento para o ponto inicial.
