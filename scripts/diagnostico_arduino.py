"""Testa LEDs, balanco e posicao da cabeca e o sensor DHT11 pela serial, sem voz.

Use: python -m scripts.diagnostico_arduino   (ou --porta COM7 para fixar a porta)
"""

import argparse
import time

from checkpoint_alexa import ArduinoController


def verificar(arduino, servo=False, verde=False, vermelho=False):
    esperado = {"servo": servo, "verde": verde, "vermelho": vermelho}
    recebido = arduino.consultar_estado()
    if recebido != esperado:
        raise RuntimeError(f"Estado incorreto: esperado {esperado}, recebido {recebido}")
    print(f"Uno confirmou: {recebido}", flush=True)


def desligar(arduino):
    arduino.parar_movimento()
    arduino.escutando(False)
    arduino.respondendo(False)


def testar_posicoes(arduino, automatico):
    """Comando de angulo (R2D2/2): confirma que a cabeca vai a cada posicao."""
    print("\nTESTE: CABECA em 60 graus, 120 graus e de volta ao centro", flush=True)
    if not automatico:
        input("Observe o robo e pressione Enter para iniciar. ")
    for angulo, lado in ((60, "para um lado"), (120, "para o outro lado"), (arduino.POS_CENTRO, "para a frente")):
        if arduino.posicionar_cabeca(angulo) != angulo:
            raise RuntimeError(f"O Uno nao confirmou o angulo {angulo}.")
        print(f"Uno confirmou {angulo} graus: a cabeca deve virar {lado}.", flush=True)
        time.sleep(1.5)
    verificar(arduino)


def testar_sensor(arduino):
    """Comando 't' (R2D2/3): le temperatura e umidade do DHT11 no pino 2."""
    print("\nTESTE: SENSOR DHT11 (temperatura e umidade)", flush=True)
    for tentativa in range(1, 4):
        leitura = arduino.ler_ambiente()
        if leitura is not None:
            temperatura, umidade = leitura
            print(f"Uno leu o sensor: {temperatura:.1f} graus C e {umidade}% de umidade.", flush=True)
            return
        if not arduino.disponivel:
            raise RuntimeError("Comunicacao com o Arduino perdida durante a leitura do sensor.")
        time.sleep(1.5)   # o DHT11 aceita uma leitura por segundo
    print("AVISO: o sensor nao respondeu em 3 tentativas. Confira VCC no 5V, GND, "
          "DATA no pino 2 e o resistor de 10k (sensor avulso).", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--porta", default="", help="Ex.: COM7; padrao: deteccao automatica")
    parser.add_argument("--automatico", action="store_true", help="Executa sem aguardar Enter")
    args = parser.parse_args()
    arduino = ArduinoController(porta=args.porta)
    try:
        if not arduino.disponivel:
            raise RuntimeError("Nao foi possivel confirmar o firmware R2D2.")
        desligar(arduino)
        verificar(arduino)
        etapas = (
            ("LED VERDE aceso por 3 segundos", lambda: arduino.escutando(True), {"verde": True}),
            ("LED VERMELHO piscando por 3 segundos", lambda: arduino.respondendo(True), {"vermelho": True}),
            ("CABECA balancando por 3 segundos", arduino.iniciar_movimento, {"servo": True}),
        )
        for descricao, acao, estado in etapas:
            print(f"\nTESTE: {descricao}", flush=True)
            if not args.automatico:
                input("Observe o robo e pressione Enter para iniciar. ")
            acao()
            verificar(arduino, **estado)
            time.sleep(3)
            verificar(arduino, **estado)
            desligar(arduino)
            verificar(arduino)
        if arduino.aceita_posicao:
            testar_posicoes(arduino, args.automatico)
        if arduino.aceita_temperatura:
            testar_sensor(arduino)
        else:
            print("\nFirmware antigo: envie o sketch atual para testar a posicao da cabeca e o DHT11.")
        print("\nComunicacao e estados do firmware OK. Confirme visualmente luzes e movimento.")
    finally:
        arduino.fechar()


if __name__ == "__main__":
    main()
