# Manual do R.2.D.2

[Voltar ao projeto e à lista de integrantes](../README.md)

> Assistente virtual por voz em português, com agenda, calculadora, IA generativa,
> comandos extras e um **Arduino Uno** que move um servo e acende LEDs de estado.
> Projeto CP4 — 2º Semestre | Programação Orientada a Objetos em Python

## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [O que vem na pasta](#o-que-vem-na-pasta)
- [Requisitos](#requisitos)
- [Instalação passo a passo](#instalação-passo-a-passo)
- [Montagem do Arduino (servo, LEDs e DHT11)](#montagem-do-arduino-servo-leds-e-dht11)
- [Como executar](#como-executar)
- [Comandos de voz](#comandos-de-voz)
- [Configurações opcionais](#configurações-opcionais)
- [Problemas comuns](#problemas-comuns)
- [Arquitetura OOP](#arquitetura-oop)
- [Status do projeto](#status-do-projeto)

---

## Sobre o projeto

O R.2.D.2 escuta o microfone, entende comandos em português e responde por voz.
Ele **só age quando ouve a palavra de ativação "dedão"** no começo do comando.
Sem ela, apenas imprime no console o que entendeu.
"Então" e "dedo" não são palavras de ativação. Acentos, maiúsculas e pontuação
após o nome são aceitos, como em `"Dedão, que horas são?"`.

O Arduino é **opcional**: sem ele, o assistente funciona normalmente, só não move o
servo, não acende os LEDs e não mede a temperatura da sala (sensor DHT11).

## O que vem na pasta

Veja a [estrutura completa no README](../README.md#estrutura-do-projeto).
O código principal permanece em `checkpoint_alexa.py`; os diagnósticos ficam em
`scripts/`, o som em `assets/audio/` e o firmware em `arduino/r2d2_servo/`.

Para iniciar no Windows, use o `Iniciar R2D2.bat`, na raiz do projeto.

A agenda é criada automaticamente em `data/agenda.txt`. Capturas de tela e
gravações de diagnóstico ficam em `outputs/`, e o sinal de parada do
`Iniciar R2D2.bat` fica em `controle/`. Essas pastas são locais e não entram no
repositório.

## Requisitos

| Item | Obrigatório? | Observação |
|---|---|---|
| Python 3.10 ou superior | Sim | Marque "Add Python to PATH" ao instalar no Windows |
| Microfone e caixa de som | Sim | |
| Internet | Sim | Voz (Google STT e gTTS), clima, dólar e bitcoin |
| [Ollama](https://ollama.com) com `llama3.2:3b` | Para a IA | Roda local, ~2 GB. Se faltar, o Groq (opcional) assume |
| Arduino Uno + servo + 2 LEDs + 2 resistores 220 Ω | Opcional | Ver [montagem](#montagem-do-arduino-servo-leds-e-dht11) |
| Sensor DHT11 (+ resistor de 10 kΩ se for o sensor avulso) | Opcional | Para "dedão qual a temperatura" |
| [Arduino IDE](https://www.arduino.cc/en/software) | Só se usar o Arduino | Para enviar o sketch ao Uno |

## Instalação passo a passo

### 1. Baixe e extraia o projeto

Extraia o ZIP e abra um terminal **dentro da pasta `R2D2`**.

### 2. Crie e ative o ambiente virtual

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> Se aparecer erro de "execução de scripts desabilitada", rode uma vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e tente de novo.

**Mac / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

> **PyAudio com erro?**
> - **Windows:** tente `pip install pipwin` e depois `pipwin install pyaudio`.
> - **Linux:** `sudo apt install portaudio19-dev python3-dev` e rode o `pip install` de novo.
> - **Mac:** `brew install portaudio` e rode o `pip install` de novo.

### 4. Instale o Ollama e baixe o modelo

1. Baixe e instale em <https://ollama.com>
2. Em um terminal:

```bash
ollama pull llama3.2:3b
```

O Ollama normalmente já fica rodando em segundo plano após instalar. Se não estiver,
rode `ollama serve` em outro terminal.

### 5. (Opcional) Configure o Arduino

Siga a seção abaixo. Pode ser feito depois: o assistente funciona sem ele.

## Montagem do Arduino (servo, LEDs e DHT11)

### Ligações

```
Arduino Uno
 ├─ pino 9 ────────────── sinal do servo   (fio laranja/amarelo)
 ├─ 5V ────────────────── VCC do servo     (fio vermelho)
 ├─ GND ───────────────── GND do servo     (fio marrom/preto)
 ├─ pino 7 ──[220 Ω]──►|── GND             LED VERDE (escutando)
 ├─ pino 8 ──[220 Ω]──►|── GND             LED VERMELHO (respondendo)
 └─ pino 2 ────────────── DATA do DHT11    (VCC no 5V, GND no GND)
```

**DHT11:**
- **Módulo de 3 pinos** (placa com o sensor azul): ligue `+`/VCC no 5V, `-`/GND no
  GND e `OUT`/DATA no pino 2. O resistor já vem na placa.
- **Sensor avulso de 4 pernas:** olhando a grade de frente, as pernas são VCC, DATA,
  sem uso e GND. Ponha um resistor de **10 kΩ entre DATA e 5V**.

Em cada LED, a **perna longa (ânodo, +)** recebe o resistor vindo do pino e a
**perna curta (cátodo, −)** vai ao GND.

> Servo pequeno (SG90, MG90S) funciona com o 5 V do USB. Servo maior ou com carga:
> use fonte externa de 5–6 V e **ligue o GND dela ao GND do Arduino**.

### O que cada saída faz

| Saída | Comportamento |
|---|---|
| LED de escuta, verde no esquema (pino 7) | Aceso enquanto o R2 está **escutando**. Pode ser de outra cor, como azul |
| LED vermelho (pino 8) | **Pisca** enquanto o R2 está **respondendo** (fala ou grito) |
| Servo (pino 9) | **Balança** durante o comando "grita" |
| DHT11 (pino 2) | Lido quando você pergunta a temperatura. O sensor aceita no máximo uma leitura por segundo; pedidos mais rápidos recebem a última leitura |

No `grita`, a cabeça percorre de 45° a 135° em passos de 1° a cada 30 ms
(cerca de 33° por segundo) e volta ao centro ao terminar.
Com o Arduino conectado, a animação e o LED vermelho duram pelo
menos quatro segundos, mesmo que o áudio termine antes.
Se a conexão com o Arduino estiver indisponível ou falhar durante o grito,
o assistente avisa por voz depois do som que não conseguiu confirmar o comando
da cabeça. As confirmações da serial comprovam o recebimento pelo firmware;
o movimento físico ainda precisa ser observado.

### Enviando o sketch ao Uno

1. Abra `arduino/r2d2_servo/r2d2_servo.ino` na Arduino IDE.
2. Em **Ferramentas → Placa**, escolha **Arduino Uno**.
3. Em **Ferramentas → Porta**, escolha a porta do Arduino (ex.: `COM7`). Em clones,
   ela pode aparecer como "Serial Port (USB)". As portas Bluetooth não servem.
4. Clique em **Carregar** (seta →).
5. Ao terminar, os dois LEDs acendem por meio segundo. Isso confirma a fiação.
   O sketch não precisa de bibliotecas além da `Servo`, que já vem com a IDE: a
   leitura do DHT11 está no próprio código.
6. **Feche o Monitor Serial da IDE** antes de rodar o Python: só um programa usa a porta por vez.

### Protocolo serial (para quem quiser testar à mão)

9600 baud, um caractere por comando (o `p` leva mais três dígitos):

| Comando | Ação |
|---|---|
| `a` / `b` | servo balança / para |
| `c` / `d` | LED verde acende / apaga |
| `e` / `f` | LED vermelho pisca / apaga |
| `p` + 3 dígitos | Leva a cabeça ao ângulo, em passos suaves (ex.: `p090`); responde `OK p090` |
| `t` | Lê o DHT11: responde `TEMP <graus> <umidade>` (ex.: `TEMP 24.0 61`) ou `ERR t` se o sensor não responder |
| `?` | Identifica o firmware: responde `R2D2/3` |
| `s` | Consulta os estados: `STATE <servo> <verde> <vermelho>`, cada um `0` ou `1` |

Cada comando de `a` a `f` devolve `OK <comando>`. O Python verifica a
identificação e essas confirmações. O `p` limita o ângulo a 45°–135°, interrompe o
balanço e responde `ERR p` se receber algo que não seja dígito. O Python também
aceita os firmwares antigos: o `R2D2/2` não tem o `t` e o `R2D2/1` também não tem o
`p`. Um `ERR t` não fecha a conexão, porque o Uno respondeu; só o sensor falhou. É necessário carregar o
sketch no Uno; abrir a porta serial, sozinho, não confirma a comunicação.

Para testar só a placa, sem depender do microfone, feche o assistente e o Monitor
Serial e rode `python -m scripts.diagnostico_arduino` (para fixar a porta, use
`--porta COM7`).
O teste aciona separadamente o LED verde, o LED vermelho e a cabeça, consulta
os estados antes e depois e desliga tudo ao terminar. Depois leva a cabeça a 60°,
120° e ao centro e lê o DHT11 (até três tentativas). Se o sensor não responder, o
teste avisa e mostra o que conferir na ligação. As respostas confirmam o estado do
programa no Uno; confirme as luzes e o movimento olhando o robô.

## Como executar

**Windows:** clique duas vezes em **`Iniciar R2D2.bat`**, na pasta do projeto. Ele usa
o Python do `.venv`, corrige os acentos do console e abre o assistente.

**Qualquer sistema:** com o ambiente virtual ativo (e o Ollama rodando, para a IA):

```bash
python checkpoint_alexa.py
```

1. **Arduino:** a porta é detectada sozinha. O programa ignora portas Bluetooth, testa
   as portas USB e aceita a que responder `R2D2/…`. Aparece
   `Arduino confirmado em COM7 (R2D2/3)`.
2. **Saudação:** ele fala *"Sistemas online..."*.
3. **Calibração:** fique em silêncio durante *"Calibrando microfone"*.
4. **Comandos:** com `Ouvindo...` e o LED de escuta aceso, diga **"dedão" + o comando**.
5. **Encerrar:** diga `"dedão sair"`. A cabeça volta ao centro e os LEDs apagam.

`Ctrl+C` na janela do assistente também encerra, então evite usá-lo para copiar
texto enquanto ela estiver em foco. Pelo `Iniciar R2D2.bat`, criar o arquivo
`controle/parar` na pasta do projeto encerra o assistente do mesmo jeito que o
`dedão sair`. Isso é útil para parar sem mexer na janela.

### Exemplo

```
Você:      "dedão que horas são"
R.2.D.2:   "São 18 horas e 30 minutos."

Você:      "dedão calcular cinquenta mais vinte e cinco"
R.2.D.2:   "O resultado é 75"

Você:      "bom dia"                      ← sem a palavra de ativação
Console:   [Reconhecido, sem acao]: bom dia
```

## Comandos de voz

Sempre começam com **"dedão"**. Diga `dedão listar comandos` para ouvir a lista.
O pedido vem logo após o nome. Palavras dentro do assunto de uma pesquisa ou
pergunta não acionam outros comandos: `dedão pesquisar como sair do Windows`
faz uma pesquisa e mantém o assistente ligado. Para encerrar, diga `dedão sair`,
`dedão encerrar` ou `dedão tchau`.

### Agenda

| Comando | O que faz |
|---|---|
| `dedão cadastrar evento` | Pergunta o evento e salva em `data/agenda.txt` |
| `dedão ler agenda` | Lê os eventos cadastrados |
| `dedão limpar agenda` | Pede confirmação ("sim") e apaga tudo |

### Data e hora

| Comando | O que faz |
|---|---|
| `dedão que horas são` | Fala a hora atual |
| `dedão que dia é hoje` | Fala a data com o dia da semana |

### Temperatura da sala (sensor DHT11)

| Comando | O que faz |
|---|---|
| `dedão qual a temperatura` / `qual é a temperatura` / `temperatura ambiente` | Lê o DHT11 e fala a temperatura e a umidade |
| `dedão qual a umidade` / `quantos graus` / `está calor` / `tá frio` | Mesma leitura |
| `dedão temperatura em <cidade>` | Previsão do tempo da cidade, pela internet (não usa o sensor) |

Resposta: *"A temperatura aqui é de 24 graus e a umidade está em 61 por cento."*
O DHT11 mede de 0 a 50 °C com precisão de ±2 °C e umidade de 20% a 90% (±5%).

### Calculadora

Aceita números por extenso (inclusive compostos) ou em algarismos.

| Fale | Resultado |
|---|---|
| `dedão calcular dois mais três` | 5 |
| `dedão calcular cinquenta mais vinte e cinco` | 75 |
| `dedão calcular cento e vinte e cinco mais um` | 126 |
| `dedão quanto é dois vezes oito` | 16 |
| `dedão calcular cem dividido por quatro` | 25 |
| `dedão calcular dez multiplicado por três` | 30 |
| `dedão calcular dois elevado a dez` | 1024 |

Operadores: mais, menos, vezes, multiplicado por, dividido por, elevado a.

### Inteligência artificial

| Comando | O que faz |
|---|---|
| `dedão perguntar <assunto>` | Consulta o Ollama local (ou o Groq, se o Ollama estiver offline) |
| `dedão me fale sobre <tema>` | Mesma função |

### Extras

| Comando | O que faz |
|---|---|
| `dedão previsão do tempo em <cidade>` | Temperatura e condições da cidade |
| `dedão valor do dólar` | Cotação USD/BRL |
| `dedão bitcoin` | Valor do Bitcoin em BRL e USD |
| `dedão tirar screenshot` | Salva uma captura da tela em PNG na pasta `outputs/` |
| `dedão pesquisar <termo>` | Pesquisa no Google |
| `dedão abrir youtube` / `dedão youtube sobre <tema>` | Abre o YouTube ou busca um vídeo |
| `dedão abrir portal` | Abre o portal da FIAP |
| `dedão grita` | Toca o som do R2D2, **balança o servo e pisca o LED vermelho** |
| `dedão sair` | Encerra |

## Configurações opcionais

Todas por variáveis de ambiente. **Nunca escreva chaves dentro do código.**

| Variável | Para que serve | Padrão |
|---|---|---|
| `GROQ_API_KEY` | Chave do Groq, usada se o Ollama estiver offline | vazio (sem backup) |
| `GROQ_MODEL` | Modelo do Groq | `openai/gpt-oss-20b` |
| `ARDUINO_PORT` | Fixa a porta serial do Arduino | detecção automática (portas USB que respondem `R2D2/…`) |
| `R2D2_MIC_INDEX` | Índice do microfone usado pelo Python | entrada padrão do Windows |

**Windows (PowerShell), valendo para a sessão atual:**

```powershell
$env:GROQ_API_KEY = "gsk_sua_chave_aqui"
$env:ARDUINO_PORT = "COM7"
python checkpoint_alexa.py
```

**Mac / Linux:**

```bash
export GROQ_API_KEY="gsk_sua_chave_aqui"
export ARDUINO_PORT="/dev/ttyACM0"
python checkpoint_alexa.py
```

Para criar uma chave do Groq: <https://console.groq.com> (conta gratuita).
Modelos do Groq são descontinuados com frequência. Se o backup parar de funcionar,
confira a lista atual em <https://console.groq.com/docs/deprecations> e ajuste `GROQ_MODEL`.

## Problemas comuns

| Sintoma | Causa provável e solução |
|---|---|
| `Arduino desativado. Confira o cabo USB...` | Nenhuma porta respondeu. Confira o cabo, feche o Monitor Serial da IDE e o outro assistente aberto, e veja a porta na Arduino IDE. Se precisar, fixe com `ARDUINO_PORT` |
| Upload falha com `cannot set com-state` em placa CH340 | Instale e selecione o driver **3.7.2022.1**, seguindo a [orientação oficial do Arduino](https://support.arduino.cc/hc/en-us/articles/13148652511260-avrdude-ser-open-can-t-set-com-state-for-COMn). Confira a versão ativa no Gerenciador de Dispositivos: instalar o pacote pode manter a versão mais recente selecionada |
| `Firmware nao confirmado em COMx` | Confira o cabo e a conexão USB. Verifique se o Uno está executando o `arduino/r2d2_servo/r2d2_servo.ino` atualizado e reinicie o assistente |
| `pyserial nao instalado` | `pip install pyserial` com o ambiente virtual ativo |
| LEDs não acendem ao enviar o sketch | Revise a fiação: perna longa do LED no resistor, perna curta no GND |
| Servo treme ou reinicia o Arduino | Falta corrente: use fonte externa de 5–6 V com GND comum |
| "A inteligência artificial local não está disponível" | Ollama não está rodando: abra o app do Ollama ou rode `ollama serve` |
| Não entende o que eu falo | Fale logo após o LED de escuta acender, perto do microfone e sem ruído. Precisa de internet |
| Não ativa ao chamar | Confira no console se o reconhecimento retornou "dedão" no início. "Então", "dedo" e o nome no meio da frase não ativam o assistente |
| `ModuleNotFoundError` | Ambiente virtual não está ativo, ou faltou o `pip install -r requirements.txt` |
| "Não consegui ler o sensor de temperatura" | Confira VCC no 5V, GND, DATA no pino 2 e, no sensor avulso, o resistor de 10 kΩ. Rode `python -m scripts.diagnostico_arduino` para testar só o sensor |
| "O firmware do Arduino ainda não tem o sensor" | O Uno está com um sketch antigo. Envie o `r2d2_servo.ino` atual; o console deve mostrar `R2D2/3` |
| Sem som no grito | Confirme que `assets/audio/r2d2_grito.mp3` existe na pasta do projeto |

Os comandos deste manual devem ser executados na raiz do projeto. O assistente
localiza o áudio e grava a agenda e as capturas com base na localização de
`checkpoint_alexa.py`, mesmo quando iniciado a partir de outra pasta.

### Diagnóstico da voz

Na primeira escuta, mantenha silêncio durante o segundo de calibração e fale
depois de `Ouvindo...`. A calibração acontece uma vez por execução; o assistente
tolera pausas de até aproximadamente 1,2 segundo durante o comando.

Para separar problemas da gravação de erros de transcrição, execute
`python -m scripts.diagnostico_voz`. Pressione Enter quando estiver pronto e diga
"dedão listar comandos". O teste grava seis segundos sem cortar nas pausas,
salva `outputs/diagnostico_voz.wav` e mostra o texto reconhecido pelo Google.
Ouça o arquivo: se o áudio estiver baixo, cortado ou distorcido, investigue a
captação; se estiver claro e a transcrição errada, investigue o reconhecimento.

Liste dispositivos com `python -m scripts.diagnostico_voz --listar` e teste outro com
`python -m scripts.diagnostico_voz --microfone 1`. Para usar esse mesmo índice no
assistente, defina `$env:R2D2_MIC_INDEX = "1"` no PowerShell antes de iniciar.
Feche a outra instância do assistente antes do teste.

## Arquitetura OOP

```
checkpoint_alexa.py
│
├── SpeechManager        # Escuta (Google STT) e fala (gTTS + pygame); controla os LEDs de estado
├── AgendaManager        # Cadastro, leitura e limpeza em data/agenda.txt
├── Calculator           # Interpreta contas ditas por voz; avaliação segura (sem eval)
├── AIIntegration        # IA via Ollama, com fallback para o Groq
├── ArduinoController    # Serial com o Arduino: servo, LEDs e DHT11; detecta a porta e trava o acesso
├── ExtraCommands        # Clima, dólar, bitcoin, screenshot, buscas e o "grita"
└── R2D2                 # Orquestradora: loop de escuta e despacho de comandos
```

```
R2D2
 ├── arduino  → ArduinoController
 ├── speech   → SpeechManager (usa arduino para os LEDs)
 ├── agenda   → AgendaManager
 ├── calc     → Calculator
 ├── ai       → AIIntegration
 └── extras   → ExtraCommands (usa arduino no grito e para ler o DHT11)
```

## Status do projeto

- [x] Palavra de ativação antes de qualquer comando
- [x] Agenda: cadastrar, ler e limpar (`data/agenda.txt`)
- [x] Hora e data
- [x] Calculadora por voz, com números compostos
- [x] IA generativa (Ollama local + Groq como backup)
- [x] Extras: clima, dólar, bitcoin, screenshot, Google, YouTube, portal FIAP, grito
- [x] Integração com Arduino: servo no grito e LEDs de estado
- [x] Temperatura e umidade da sala pelo sensor DHT11
- [x] Programação orientada a objetos, com comentários e docstrings
- [x] Diagnósticos do Arduino e do microfone, e testes automatizados sem hardware
