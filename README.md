# Projeto de Redes: Jogo Pedra, Papel e Tesoura
## Descrição:

Este trabalho final de redes tem o propósito de criar um jogo de pedra, papel e tesoura.
Planejamos utilizar, em códigos diferentes, conexão par a par e via servidor, criando também protocolos de comunicação personalizados.
Com isso, visamos garantir o máximo aprendizado de todos os conteúdos vistos em aula.
---

## Arquitetura Planejada:

### Cliente-Servidor

- **Modelo de Comunicação:** Push — o servidor envia atualizações de estado aos clientes.
- **Canal de Controle:** In-Band — dados e comandos de controle trafegam pelo mesmo canal TCP.

---

## Comandos do protocolo:

A comunicação será baseada em comandos de texto simples, cada um terminado por uma nova linha (`\n`).

### Cliente ➜ Servidor

| Comando | Parâmetro   | Descrição                                             |
|---------|-------------|-------------------------------------------------------|
| `CON`   | `<nome>`    | Requisita conexão ao servidor com um nome de jogador |
| `ROC`   | -           | Envia a jogada "Pedra"                                |
| `PAP`   | -           | Envia a jogada "Papel"                                |
| `SCI`   | -           | Envia a jogada "Tesoura"                              |
| `RAN`   | -           | Requisita o ranking atualizado do servidor           |
| `QUI`   | -           | Informa o servidor que o cliente está se desconectando|

### Servidor ➜ Cliente

| Comando | Parâmetro     | Descrição                                                   |
|---------|---------------|-------------------------------------------------------------|
| `MAT`   | `<oponente>`  | Avisa que a partida começou e informa o nome do oponente   |
| `PLA`   | -             | Sinaliza ao cliente que é sua vez de jogar                 |
| `WIN`   | -             | Informa que o cliente venceu a rodada                      |
| `LOS`   | -             | Informa que o cliente perdeu a rodada                      |
| `TIE`   | -             | Informa que a rodada terminou em empate                    |
| `RAN`   | `<payload>`   | Envia o ranking no formato `nome1:vitorias1,nome2:vitorias2`|
| `END`   | `<mensagem>`  | Sinaliza o fim da partida e encerra a aplicação            |

---

## Observação:
- Possivelmente faremos uso de algum método para implementar algum tipo de conexão segura.

