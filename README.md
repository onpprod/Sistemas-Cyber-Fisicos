# Deploy com FAAAST

Este guia descreve as etapas para configurar e executar o FAAAST utilizando um arquivo `.AASX`.

## Etapa 1: Criação de um `.AASX`

Esta etapa será descrita em outro documento.

## Etapa 2: Configuração preliminar

1. **Adicionar o arquivo `.AASX`**
   - Copie o arquivo `.AASX` para a pasta `resources` e se necessário renomeie-o para `model.aasx`.

2. **Configurar o `config.json`**
   - As configurações abaixo são realizadas especificamente na chave `assetConnections. subscriptionProviders`.
   - Defina o caminho correto para a propriedade, seguindo este modelo:
     ```json
     "(Submodel)https://example.com/ids/sm/6415_3082_2052_7347, (Property)Temperature"
     ```
   
   - Ajuste o tópico correto para o sensor:
     ```json
     "topic": "emulator/sensor"
     ```
   
   - Defina a chave correta no payload utilizando uma query JSONPath:
     ```json
     "query": "$.temperature"
     ```
   
   - Configure o endereço correto do broker MQTT. Se for local, utilize o IP da máquina:
     ```json
     "serverUri": "tcp://192.168.0.6:1883"
     ```
   
   - Ajuste o `clientID` em cada propriedade para evitar conflitos com outros clientes conectados:
     ```json
     "clientID": "FAAAST MQTT Client"
     ```
## Etapa 3: Configurar a camada de integração
Ajustar as variáveis de ambiente presentes no docker-compose.yml.

```
      MQTT_BROKER: 131.255.82.115
      MQTT_PORT: 1883
      MQTT_TOPIC: esp32/n/monitor/cmd
      CLIENT_ID: esp32
```

## Etapa 4: Iniciar o serviço FAAAST

### Usando Docker
Com Docker instalado, utilizamos o comando abaixo na pasta raiz:
```sh
docker-compose up -d
```

## Extras

O exemplo pode ser utilizado apenas com os arquivos deste repositório, utilizando o compose do emulador e o compose principal do exemplo e ajustando o parâmetro de config.json `serverUri` . O AAS estará disponível na porta `8081` local, acessível por clientes OPCUA.

### Utilizando o emulador
Para simular um sensor de temperatura, utilize o seguinte comando dentro da pasta `extras/emulator`:
```sh
docker-compose up -d
```
Isso criará um broker MQTT local e executará um script que publicará atualizações de temperatura automaticamente.

- O emulador publicará no broker em `tcp://localhost:1883` (substitua pelo IP da rede local da máquina no arquivo de configuração).
- As mensagens serão enviadas para o tópico `emulator/sensor` no seguinte formato:
  ```json
  {"temperature": 34.4}
  ```

---
Este guia garante que todas as configurações essenciais estejam corretas antes de iniciar o FAAAST. Caso tenha dúvidas, consulte a documentação oficial do FAAAST para mais detalhes.

