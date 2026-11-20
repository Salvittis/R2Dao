"""Regressoes de ativacao, roteamento e Arduino, sem audio, rede ou hardware."""

import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock, Mock, call, patch


CAMINHO = Path(__file__).resolve().parents[1] / "checkpoint_alexa.py"
spec = importlib.util.spec_from_file_location("r2d2_em_teste", CAMINHO)
app = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {
    nome: Mock() for nome in ("requests", "speech_recognition", "gtts", "pygame")
}):
    spec.loader.exec_module(app)


def entrar(teste, gerenciador):
    """Equivale a TestCase.enterContext (Python 3.11+); mantem os testes no 3.10."""
    pilha = contextlib.ExitStack()
    teste.addCleanup(pilha.close)
    return pilha.enter_context(gerenciador)


class ComandosVozTest(unittest.TestCase):
    def setUp(self):
        self.assistente = app.R2D2.__new__(app.R2D2)
        self.acoes = MagicMock()
        for nome in ("speech", "agenda", "calc", "ai", "extras", "arduino"):
            setattr(self.assistente, nome, getattr(self.acoes, nome))
        self.voz = app.SpeechManager.__new__(app.SpeechManager)
        self.console = contextlib.redirect_stdout(io.StringIO())
        self.console.__enter__()
        self.addCleanup(self.console.__exit__, None, None, None)

    def executar(self, fala):
        return self.assistente.processar_comando(self.voz._normalizar_texto(fala))

    def test_falas_sem_ativacao_exata_no_inicio_nao_executam_acoes(self):
        for fala in (
            "que horas são", "então sair", "dedo sair", "sair dedão",
            "você sabe dedão que horas são", "meu dedão sair",
            "dedãozinho sair", "dedão2 sair", "superdedão sair", "",
        ):
            with self.subTest(fala=fala):
                self.assertTrue(self.executar(fala))
                self.assertEqual(self.acoes.mock_calls, [])

    def test_ativacao_aceita_acentos_caixa_espacos_e_pontuacao(self):
        for fala in ("dedão sair", "  DEDÃO, sair!  ", "dedao: sair", "dedão   sair"):
            with self.subTest(fala=fala):
                self.acoes.reset_mock()
                self.assertFalse(self.executar(fala))
                self.assistente.speech.falar.assert_called_once()

    def test_aliases_de_saida_funcionam_como_comando_completo(self):
        for comando in ("sair", "encerrar", "tchau"):
            with self.subTest(comando=comando):
                self.acoes.reset_mock()
                self.assertFalse(self.executar(f"dedão {comando}"))
                self.assistente.speech.falar.assert_called_once()
        self.assertTrue(self.executar("dedão sair do windows"))

    def test_pesquisa_preserva_termo_e_nao_dispara_outros_comandos(self):
        for termo in (
            "como sair do windows", "como encerrar um programa", "como dizer tchau",
            "como cadastrar evento e limpar agenda", "que horas sao em toquio",
            "como calcular dois mais tres", "como reconhecer face", "seguir rosto",
            "qual a temperatura de fusao do gelo",
            "o que e bitcoin", "previsao do tempo em santos", "valor do dolar",
            "tirar screenshot no youtube", "portal fiap", "grita e listar comandos",
            "como pesquisar e perguntar sobre o dedao", "entao e dedo",
        ):
            with self.subTest(termo=termo):
                self.acoes.reset_mock()
                self.assistente.extras.pesquisar_google.return_value = "Pesquisa aberta."
                self.assertTrue(self.executar(f"dedão pesquisar {termo}"))
                self.assertEqual(self.acoes.mock_calls, [
                    call.extras.pesquisar_google(termo),
                    call.speech.falar("Pesquisa aberta."),
                ])

    def test_perguntas_nao_acionam_comandos_mencionados(self):
        for prefixo in ("perguntar", "me fale sobre"):
            with self.subTest(prefixo=prefixo):
                self.acoes.reset_mock()
                pergunta = "como sair e calcular depois de perguntar ao dedao"
                self.assertTrue(self.executar(f"dedão {prefixo} {pergunta}"))
                self.assistente.ai.perguntar.assert_called_once_with(pergunta)
                self.assistente.calc.calcular.assert_not_called()
                self.assistente.extras.pesquisar_google.assert_not_called()

    def test_youtube_preserva_busca_com_palavras_de_outros_comandos(self):
        for prefixo in ("youtube sobre", "abrir youtube sobre", "youtube video de"):
            with self.subTest(prefixo=prefixo):
                self.acoes.reset_mock()
                busca = "como sair e calcular falando sobre bitcoin"
                self.assistente.extras.abrir_youtube.return_value = "YouTube aberto."
                self.assertTrue(self.executar(f"dedão {prefixo} {busca}"))
                self.assertEqual(self.acoes.mock_calls, [
                    call.extras.abrir_youtube(busca), call.speech.falar("YouTube aberto."),
                ])

    def test_pesquisa_sem_termo_pede_resposta_sem_palavra_de_ativacao(self):
        self.assistente.speech.ouvir_resposta.return_value = "como sair do windows"
        self.assertTrue(self.executar("dedão pesquisar"))
        self.assistente.speech.ouvir_resposta.assert_called_once()
        self.assistente.extras.pesquisar_google.assert_called_once_with("como sair do windows")

    def test_comandos_documentados_continuam_acessiveis(self):
        casos = (
            ("calcular cinquenta mais vinte e cinco", "calc.calcular"),
            ("qual a temperatura", "extras.medir_ambiente"),
            ("cadastrar evento", "agenda.cadastrar_evento"),
            ("ler agenda", "agenda.ler_agenda"),
            ("limpar agenda", "agenda.limpar_agenda"),
            ("previsão do tempo em santos", "extras.obter_clima"),
            ("valor do dólar", "extras.obter_dolar"),
            ("bitcoin", "extras.obter_bitcoin"),
            ("tirar screenshot", "extras.tirar_screenshot"),
            ("abrir youtube", "extras.abrir_youtube"),
            ("abrir portal", "extras.abrir_portal_fiap"),
            ("grita", "extras.grita"),
        )
        for comando, destino in casos:
            with self.subTest(comando=comando):
                self.acoes.reset_mock()
                self.assistente.speech.ouvir_resposta.return_value = "sim"
                self.assertTrue(self.executar(f"dedão {comando}"))
                modulo, metodo = destino.split(".")
                getattr(getattr(self.assistente, modulo), metodo).assert_called_once()

    def test_perguntas_sobre_a_sala_leem_o_sensor(self):
        for fala in (
            "qual a temperatura", "qual é a temperatura", "qual a temperatura da sala",
            "temperatura ambiente", "qual a umidade", "quanto está a temperatura",
            "como está a temperatura", "quantos graus", "está calor", "tá frio",
        ):
            with self.subTest(fala=fala):
                self.acoes.reset_mock()
                self.assistente.extras.medir_ambiente.return_value = "A temperatura aqui é de 24 graus."
                self.assertTrue(self.executar(f"dedão {fala}"))
                self.assertEqual(self.acoes.mock_calls, [
                    call.extras.medir_ambiente(), call.speech.falar("A temperatura aqui é de 24 graus."),
                ])

    def test_temperatura_de_uma_cidade_continua_sendo_previsao_do_tempo(self):
        for fala, cidade in (("temperatura em santos", "santos"),
                             ("qual a temperatura em são paulo", "sao paulo"),
                             ("previsão do tempo em santos", "santos")):
            with self.subTest(fala=fala):
                self.acoes.reset_mock()
                self.assertTrue(self.executar(f"dedão {fala}"))
                self.assistente.extras.obter_clima.assert_called_once_with(cidade)
                self.assistente.extras.medir_ambiente.assert_not_called()

    def test_comandos_da_webcam_removida_nao_sao_mais_reconhecidos(self):
        for comando in ("reconhecer face", "seguir rosto", "parar de seguir"):
            with self.subTest(comando=comando):
                self.acoes.reset_mock()
                self.assertTrue(self.executar(f"dedão {comando}"))
                self.assertEqual(self.acoes.mock_calls, [call.speech.falar(
                    "Comando não reconhecido. "
                    "Para ver todos os comandos, diga: dedão listar comandos."
                )])

    def test_grito_balanca_a_cabeca(self):
        self.assistente.extras.grita.return_value = ""
        self.assertTrue(self.executar("dedão grita"))
        self.assistente.extras.grita.assert_called_once()

    def test_loop_ignora_falas_sem_ativacao_e_fecha_arduino_ao_sair(self):
        self.assistente.speech.ouvir.side_effect = [
            self.voz._normalizar_texto(fala)
            for fala in ("então sair", "você sabe dedão sair", "dedão pesquisar como sair do windows", "dedão sair")
        ]
        self.assistente.iniciar()
        self.assertEqual(self.assistente.speech.ouvir.call_count, 4)
        self.assistente.extras.pesquisar_google.assert_called_once_with("como sair do windows")
        self.assistente.arduino.fechar.assert_called_once()


class GritoTest(unittest.TestCase):
    def setUp(self):
        self.agora = 0.0
        self.fim_audio = 0.1
        self.eventos = []
        self.arduino = Mock(disponivel=True)
        self.arduino.iniciar_movimento.side_effect = lambda: self.eventos.append(("movimento", self.agora))
        self.arduino.parar_movimento.side_effect = lambda: self.eventos.append(("parada", self.agora))
        self.music = Mock()
        self.music.get_busy.side_effect = lambda: self.agora < self.fim_audio
        self.music.play.side_effect = lambda: self.eventos.append(("audio", self.agora))
        self.contexto = contextlib.ExitStack()
        self.addCleanup(self.contexto.close)
        self.contexto.enter_context(patch.object(app.mixer, "music", self.music))
        self.contexto.enter_context(patch.object(app.time, "monotonic", side_effect=lambda: self.agora))
        self.contexto.enter_context(patch.object(app.time, "sleep", side_effect=self.avancar))
        self.extras = app.ExtraCommands(arduino=self.arduino)

    def avancar(self, segundos):
        self.agora += segundos

    def test_audio_curto_nao_interrompe_movimento_antes_de_quatro_segundos(self):
        self.assertEqual(self.extras.grita(), "")
        self.assertEqual([evento for evento, _ in self.eventos], ["movimento", "audio", "parada"])
        self.assertGreaterEqual(self.eventos[-1][1], 4.0)
        self.arduino.respondendo.assert_has_calls([call(True), call(False)])

    def test_audio_longo_mantem_movimento_ate_terminar(self):
        self.fim_audio = 6.0
        self.assertEqual(self.extras.grita(), "")
        self.assertGreaterEqual(self.eventos[-1][1], 6.0)

    def test_sem_arduino_nao_adiciona_espera_ao_som(self):
        self.extras.arduino = None
        self.assertEqual(self.extras.grita(), "")
        self.assertLess(self.agora, 0.2)

    def test_arduino_desconectado_nao_tenta_mover_nem_adiciona_espera(self):
        self.arduino.disponivel = False
        self.assertIn("comunicação com o Arduino", self.extras.grita())
        self.arduino.iniciar_movimento.assert_not_called()
        self.assertLess(self.agora, 0.2)

    def test_perda_da_conexao_durante_grito_nao_e_reportada_como_sucesso(self):
        self.music.play.side_effect = lambda: setattr(self.arduino, "disponivel", False)
        self.assertIn("comunicação com o Arduino", self.extras.grita())
        self.arduino.parar_movimento.assert_called_once()
        self.arduino.respondendo.assert_called_with(False)

    def test_falha_no_player_desliga_servo_led_e_audio_imediatamente(self):
        self.music.play.side_effect = RuntimeError("falha no player")
        self.assertIn("falha no player", self.extras.grita())
        self.arduino.parar_movimento.assert_called_once()
        self.arduino.respondendo.assert_called_with(False)
        self.music.stop.assert_called()
        self.music.unload.assert_called()
        self.assertEqual(self.agora, 0.0)


class ComunicacaoArduinoTest(unittest.TestCase):
    def setUp(self):
        self.porta = Mock(is_open=True)
        self.porta.write.side_effect = lambda comando: len(comando)
        self.porta.readline.return_value = b"R2D2/1\r\n"
        self.serial = Mock()
        self.serial.Serial.return_value = self.porta
        self.contexto = contextlib.ExitStack()
        self.addCleanup(self.contexto.close)
        self.contexto.enter_context(patch.dict(sys.modules, {"serial": self.serial}))
        self.contexto.enter_context(patch.object(app.time, "sleep"))
        self.contexto.enter_context(contextlib.redirect_stdout(io.StringIO()))

    def test_porta_aberta_so_e_aceita_apos_identificacao_do_firmware(self):
        arduino = app.ArduinoController(porta="COM4")
        self.assertTrue(arduino.disponivel)
        self.porta.write.assert_called_once_with(b"?")
        self.assertEqual(arduino.porta, "COM4")

    def test_firmware_sem_resposta_libera_porta_e_desativa_controle(self):
        self.porta.readline.return_value = b""
        arduino = app.ArduinoController(porta="COM4")
        self.assertFalse(arduino.disponivel)
        self.porta.close.assert_called_once()

    def test_confirmacao_de_outro_comando_nao_e_aceita(self):
        arduino = app.ArduinoController(porta="COM4")
        self.porta.readline.return_value = b"OK b\r\n"
        arduino.iniciar_movimento()
        self.assertFalse(arduino.disponivel)
        self.porta.close.assert_called_once()

    def test_falha_de_escrita_libera_porta(self):
        arduino = app.ArduinoController(porta="COM4")
        self.porta.write.side_effect = OSError("USB desconectado")
        arduino.escutando(True)
        self.assertFalse(arduino.disponivel)
        self.porta.close.assert_called_once()

    def test_firmware_antigo_funciona_mas_nao_aceita_posicao(self):
        arduino = app.ArduinoController(porta="COM4")
        self.assertTrue(arduino.disponivel)
        self.assertFalse(arduino.aceita_posicao)
        self.porta.reset_mock()
        self.assertIsNone(arduino.posicionar_cabeca(100))
        self.porta.write.assert_not_called()

    def test_firmware_novo_posiciona_cabeca_dentro_dos_limites(self):
        self.porta.readline.return_value = b"R2D2/2\r\n"
        arduino = app.ArduinoController(porta="COM4")
        self.assertTrue(arduino.aceita_posicao)
        for pedido, enviado, esperado in ((100, b"p100", 100), (200, b"p135", 135), (-5, b"p045", 45)):
            with self.subTest(pedido=pedido):
                self.porta.readline.return_value = b"OK " + enviado + b"\r\n"
                self.assertEqual(arduino.posicionar_cabeca(pedido), esperado)
                self.porta.write.assert_called_with(enviado)

    def test_posicao_sem_confirmacao_libera_porta(self):
        self.porta.readline.return_value = b"R2D2/2\r\n"
        arduino = app.ArduinoController(porta="COM4")
        self.porta.readline.return_value = b"ERR p\r\n"
        self.assertIsNone(arduino.posicionar_cabeca(90))
        self.assertFalse(arduino.disponivel)
        self.porta.close.assert_called_once()

    def portas_do_windows(self, *portas):
        """Simula serial.tools.list_ports com as portas informadas."""
        infos = [Mock(device=d, description=desc, manufacturer=fab, hwid=hwid, vid=vid)
                 for d, desc, fab, hwid, vid in portas]
        list_ports = Mock()
        list_ports.comports.return_value = infos
        self.serial.tools.list_ports = list_ports
        self.contexto.enter_context(patch.dict(sys.modules, {
            "serial.tools": self.serial.tools, "serial.tools.list_ports": list_ports,
        }))

    def test_deteccao_ignora_bluetooth_e_acha_o_uno_na_porta_usb(self):
        # Como no notebook do grupo: COM5/COM6 Bluetooth e o Uno em "Serial Port (USB)"
        self.portas_do_windows(
            ("COM5", "Standard Serial over Bluetooth link", "Microsoft", "BTHENUM\\{0000}", None),
            ("COM6", "Standard Serial over Bluetooth link", "Microsoft", "BTHENUM\\{0001}", None),
            ("COM7", "Serial Port (USB)", "Microsoft", "USB VID:PID=1234:5678", 0x1234),
        )
        with patch.dict(app.os.environ, {"ARDUINO_PORT": ""}):
            arduino = app.ArduinoController()
        self.assertTrue(arduino.disponivel)
        self.assertEqual(arduino.porta, "COM7")
        self.serial.Serial.assert_called_once()
        self.assertEqual(self.serial.Serial.call_args.args[0], "COM7")

    def test_deteccao_prioriza_chip_conhecido_e_tenta_a_proxima(self):
        self.portas_do_windows(
            ("COM9", "Dispositivo USB", "Generico", "USB VID:PID=AAAA:0001", 0xAAAA),
            ("COM3", "USB-SERIAL CH340", "wch.cn", "USB VID:PID=1A86:7523", 0x1A86),
        )
        respostas = iter([b"", b"R2D2/2\r\n"])   # COM3 nao responde; COM9 sim
        self.porta.readline.side_effect = lambda: next(respostas)
        with patch.dict(app.os.environ, {"ARDUINO_PORT": ""}):
            arduino = app.ArduinoController()
        portas_tentadas = [c.args[0] for c in self.serial.Serial.call_args_list]
        self.assertEqual(portas_tentadas, ["COM3", "COM9"])
        self.assertEqual(arduino.porta, "COM9")
        self.assertEqual(arduino.versao, 2)

    def test_porta_fixada_nao_tenta_outras(self):
        self.porta.readline.return_value = b""
        arduino = app.ArduinoController(porta="COM4")
        self.assertFalse(arduino.disponivel)
        self.assertEqual([c.args[0] for c in self.serial.Serial.call_args_list], ["COM4"])

    def test_sensor_dht11_no_firmware_r2d2_3(self):
        self.porta.readline.return_value = b"R2D2/3\r\n"
        arduino = app.ArduinoController(porta="COM7")
        self.assertTrue(arduino.aceita_temperatura)
        for resposta, esperado in ((b"TEMP 24.0 61", (24.0, 61)), (b"TEMP 23.3 40", (23.3, 40)),
                                   (b"TEMP -2.1 40", (-2.1, 40)), (b"TEMP 25 55", (25.0, 55))):
            with self.subTest(resposta=resposta):
                self.porta.readline.return_value = resposta + b"\r\n"
                self.assertEqual(arduino.ler_ambiente(), esperado)
                self.porta.write.assert_called_with(b"t")

    def test_sensor_que_falha_nao_derruba_a_conexao(self):
        self.porta.readline.return_value = b"R2D2/3\r\n"
        arduino = app.ArduinoController(porta="COM7")
        self.porta.readline.return_value = b"ERR t\r\n"
        self.assertIsNone(arduino.ler_ambiente())
        self.assertTrue(arduino.disponivel)
        self.porta.close.assert_not_called()

    def test_resposta_estranha_ao_pedir_temperatura_fecha_a_porta(self):
        self.porta.readline.return_value = b"R2D2/3\r\n"
        arduino = app.ArduinoController(porta="COM7")
        self.porta.readline.return_value = b"OK c\r\n"
        self.assertIsNone(arduino.ler_ambiente())
        self.assertFalse(arduino.disponivel)

    def test_firmware_sem_sensor_nao_pede_temperatura(self):
        self.porta.readline.return_value = b"R2D2/2\r\n"
        arduino = app.ArduinoController(porta="COM7")
        self.assertFalse(arduino.aceita_temperatura)
        self.porta.reset_mock()
        self.assertIsNone(arduino.ler_ambiente())
        self.porta.write.assert_not_called()

    def test_estado_informado_pelo_firmware(self):
        arduino = app.ArduinoController(porta="COM4")
        self.porta.readline.return_value = b"STATE 1 0 1\r\n"
        self.assertEqual(arduino.consultar_estado(), {
            "servo": True, "verde": False, "vermelho": True,
        })

    def test_encerramento_confirma_desligamento_das_tres_saidas(self):
        arduino = app.ArduinoController(porta="COM4")
        self.porta.reset_mock()
        self.porta.readline.side_effect = [b"OK b\n", b"OK d\n", b"OK f\n"]
        arduino.fechar()
        self.assertEqual(self.porta.write.call_args_list, [call(b"b"), call(b"d"), call(b"f")])
        self.porta.close.assert_called_once()
        self.assertFalse(arduino.disponivel)


class MedirAmbienteTest(unittest.TestCase):
    """Frase falada a partir da leitura do DHT11."""

    def setUp(self):
        self.arduino = Mock(disponivel=True, aceita_temperatura=True)
        self.extras = app.ExtraCommands(arduino=self.arduino)

    def falar(self, leitura):
        self.arduino.ler_ambiente.return_value = leitura
        return self.extras.medir_ambiente()

    def test_leituras_viram_frases_naturais(self):
        for leitura, frase in (
            ((24.0, 61), "A temperatura aqui é de 24 graus e a umidade está em 61 por cento."),
            ((23.3, 40), "A temperatura aqui é de 23 vírgula 3 graus e a umidade está em 40 por cento."),
            ((1.0, 90), "A temperatura aqui é de 1 grau e a umidade está em 90 por cento."),
            ((-2.1, 40), "A temperatura aqui é de menos 2 vírgula 1 graus e a umidade está em 40 por cento."),
            ((0.0, 50), "A temperatura aqui é de 0 graus e a umidade está em 50 por cento."),
        ):
            with self.subTest(leitura=leitura):
                self.assertEqual(self.falar(leitura), frase)

    def test_sensor_sem_resposta(self):
        self.assertIn("Confira a ligação do DHT11 no pino 2", self.falar(None))

    def test_conexao_perdida_durante_a_leitura(self):
        def perder(*_args):
            self.arduino.disponivel = False
        self.arduino.ler_ambiente.side_effect = lambda: perder() or None
        self.assertIn("Perdi a comunicação com o Arduino", self.extras.medir_ambiente())

    def test_sem_arduino_ou_com_firmware_antigo(self):
        self.assertIn("sem o Arduino", app.ExtraCommands(arduino=None).medir_ambiente())
        self.arduino.disponivel = False
        self.assertIn("sem o Arduino", self.extras.medir_ambiente())
        self.arduino.disponivel = True
        self.arduino.aceita_temperatura = False
        self.assertIn("firmware", self.extras.medir_ambiente())
        self.arduino.ler_ambiente.assert_not_called()


class ArquivoParadaTest(unittest.TestCase):
    """O "Iniciar R2D2.bat" permite parar o assistente criando um arquivo de sinal."""

    def setUp(self):
        self.pasta = Path(entrar(self, tempfile.TemporaryDirectory()))
        self.arquivo = self.pasta / "parar"
        self.assistente = app.R2D2.__new__(app.R2D2)
        self.acoes = MagicMock()
        for nome in ("speech", "arduino"):
            setattr(self.assistente, nome, getattr(self.acoes, nome))
        entrar(self, contextlib.redirect_stdout(io.StringIO()))
        entrar(self, patch.dict(app.os.environ, {
            "R2D2_ARQUIVO_PARADA": str(self.arquivo),
        }))

    def test_arquivo_de_parada_encerra_como_ctrl_c(self):
        def ouvir(**_kwargs):
            self.arquivo.write_text("")
            limite = time.monotonic() + 5
            while time.monotonic() < limite:   # "escutando" ate ser interrompido
                time.sleep(0.01)
            return ""

        self.assistente.speech.ouvir.side_effect = ouvir
        inicio = time.monotonic()
        self.assistente.iniciar()
        self.assertLess(time.monotonic() - inicio, 3)
        self.assistente.speech.falar.assert_called_with("Até logo! Bip bup.")
        self.assistente.arduino.fechar.assert_called_once()
        self.assertFalse(self.arquivo.exists())

    def test_pedido_feito_durante_a_inicializacao_nao_se_perde(self):
        self.arquivo.write_text("")  # chegou antes do loop comecar

        def ouvir(**_kwargs):  # o microfone e lido em pedacos curtos
            limite = time.monotonic() + 5
            while time.monotonic() < limite:
                time.sleep(0.01)
            return ""

        self.assistente.speech.ouvir.side_effect = ouvir
        inicio = time.monotonic()
        self.assistente.iniciar()
        self.assertLess(time.monotonic() - inicio, 3)
        self.assistente.arduino.fechar.assert_called_once()


class SerialConcorrenteTest(unittest.TestCase):
    def test_comandos_de_duas_threads_recebem_a_propria_confirmacao(self):
        porta = Mock(is_open=True)
        pendentes = []
        trava_porta = threading.Lock()

        def escrever(comando):
            with trava_porta:
                pendentes.append(comando)
            time.sleep(0.001)  # da chance de outra thread se intrometer
            return len(comando)

        def ler():
            with trava_porta:
                comando = pendentes.pop(0)
            return b"R2D2/2\n" if comando == b"?" else b"OK " + comando + b"\n"

        porta.write.side_effect = escrever
        porta.readline.side_effect = ler
        serial = Mock()
        serial.Serial.return_value = porta
        with patch.dict(sys.modules, {"serial": serial}), patch.object(app.time, "sleep"), \
                contextlib.redirect_stdout(io.StringIO()):
            arduino = app.ArduinoController(porta="COM7")
        erros = []

        def cabeca():
            for angulo in range(60, 120):
                if arduino.posicionar_cabeca(angulo) != angulo:
                    erros.append(angulo)

        def leds():
            for i in range(60):
                arduino.escutando(i % 2 == 0)

        threads = [threading.Thread(target=cabeca), threading.Thread(target=leds)]
        with contextlib.redirect_stdout(io.StringIO()):
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        self.assertEqual(erros, [])
        self.assertTrue(arduino.disponivel)


class CapturaVozTest(unittest.TestCase):
    def setUp(self):
        self.recognizer = Mock(energy_threshold=300)
        self.recognizer.recognize_google.return_value = "dedão listar comandos"
        self.microfone = MagicMock()
        self.sr = Mock()
        self.sr.Recognizer.return_value = self.recognizer
        self.sr.Microphone = self.microfone
        self.sr.WaitTimeoutError = type("WaitTimeoutError", (Exception,), {})
        self.sr.UnknownValueError = type("UnknownValueError", (Exception,), {})
        self.sr.RequestError = type("RequestError", (Exception,), {})
        self.contexto = contextlib.ExitStack()
        self.addCleanup(self.contexto.close)
        self.contexto.enter_context(patch.object(app, "sr", self.sr))
        self.contexto.enter_context(patch.dict(app.os.environ, {"R2D2_MIC_INDEX": "1"}))
        self.contexto.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.arduino = Mock()
        self.voz = app.SpeechManager(arduino=self.arduino)

    def test_segunda_fala_nao_e_consumida_por_nova_calibracao(self):
        self.recognizer.listen.side_effect = ["primeiro audio", "segundo audio"]
        self.assertEqual(self.voz.ouvir(), "dedao listar comandos")
        self.assertEqual(self.voz.ouvir(), "dedao listar comandos")
        self.assertEqual(self.recognizer.adjust_for_ambient_noise.call_count, 1)
        self.microfone.assert_called_with(device_index=1)
        self.assertEqual(self.recognizer.recognize_google.call_args_list, [
            call("primeiro audio", language="pt-BR"),
            call("segundo audio", language="pt-BR"),
        ])

    def test_falha_na_calibracao_permite_nova_tentativa(self):
        self.recognizer.adjust_for_ambient_noise.side_effect = [OSError("microfone ocupado"), None]
        self.assertEqual(self.voz.ouvir(), "")
        self.assertEqual(self.voz.ouvir(), "dedao listar comandos")
        self.assertEqual(self.recognizer.adjust_for_ambient_noise.call_count, 2)

    def test_timeout_de_escuta_desliga_led(self):
        self.recognizer.listen.side_effect = self.sr.WaitTimeoutError()
        self.assertEqual(self.voz.ouvir(), "")
        self.assertEqual(self.arduino.escutando.call_args_list, [call(True), call(False)])

    def test_timeout_da_rede_nao_derruba_assistente(self):
        self.recognizer.recognize_google.side_effect = TimeoutError("sem resposta")
        self.assertEqual(self.voz.ouvir(), "")
        self.arduino.escutando.assert_called_with(False)


if __name__ == "__main__":
    unittest.main()
