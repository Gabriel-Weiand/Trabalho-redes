# Projeto de Redes: Jogo Pedra, Papel e Tesoura

## Descrição:

Este trabalho final de redes tem o propósito de criar um jogo de pedra, papel e tesoura.
Planejamos utilizar, em códigos diferentes, conexão par a par e via servidor, criando também protocolos de comunicação personalizados.
Com isso, visamos garantir o máximo aprendizado de todos os conteúdos vistos em aula.
---

## Arquitetura Planejada: 
- **Arquitetura:** Cliente-Servidor
- **Tipo de Conexão:** Persistente — a conexão permanece aberta durante toda a sessão de jogo.
- **Modelo de Comunicação:** Push — o servidor envia atualizações de estado aos clientes.
- **Canal de Controle:** In-Band — dados e comandos de controle trafegam pelo mesmo canal TCP.
- **Gerenciamento de Estado:** Stateful — o servidor mantém o estado de cada cliente durante a sessão. 

---

## Comandos do protocolo:

A comunicação será baseada em comandos de texto simples, cada um terminado por uma nova linha (`\n`).

### Cliente ➜ Servidor

| Comando | Parâmetro | Descrição                                              |
|---------|-----------|--------------------------------------------------------|
| `CON`   | `<nome>`  | Requisita conexão ao servidor com um nome de jogador   |
| `ROC`   | -         | Envia a jogada "Pedra"                                 |
| `PAP`   | -         | Envia a jogada "Papel"                                 |
| `SCI`   | -         | Envia a jogada "Tesoura"                               |
| `RAN`   | -         | Requisita o ranking atualizado do servidor             |
| `QUI`   | -         | Informa o servidor que o cliente está se desconectando |

### Servidor ➜ Cliente

| Comando | Parâmetro    | Descrição                                                      |
|---------|--------------|----------------------------------------------------------------|
| `MAT`   | `<oponente>` | Avisa que a partida começou e informa o nome do oponente       |
| `PLA`   | -            | Sinaliza ao cliente que é sua vez de jogar                     |
| `WIN`   | `<jogada>`   | Informa que o cliente venceu a rodada e a jogada do oponente   |
| `LOS`   | `<jogada>`   | Informa que o cliente perdeu a rodada e a jogada do oponente   |
| `TIE`   | `<jogada>`   | Informa que a rodada terminou em empate e a jogada do oponente |
| `RAN`   | `<ranking>`  | Envia o ranking no formato `nome1:vitorias1,nome2:vitorias2`   |
| `END`   | `<mensagem>` | Sinaliza o fim da partida e encerra a aplicação                |

---

## Formato das mensagens e campos de cabeçalho

Toda a comunicação entre cliente e servidor é realizada através de mensagens no formato **JSON**, enviadas como uma única linha de texto por conexão TCP.

Cada mensagem possui dois campos principais, type e payload, como exemplificado a seguir:

```json
{
  "type": "NOME_DO_COMANDO",
  "payload": { "flag" : "conteudo" }
}
```
E ainda diferentes tipos de payload, como listados e exemplificados abaixo:
- **Cliente joga "pedra"**: Um dos diversos exemplos com payload vazio
```json
{
"type": "ROC",
"payload": {}
}
```

- **Cliente conecta ao servidor:** Envia o nome como payload
```json
{
  "type": "CON",
  "payload": {
    "nome": "Gabriel"
  }
}
```
- **Servidor informa início da partida:** Nome do oponente como payload
```json
{
  "type": "MAT",
  "payload": {
    "oponente": "Alice"
  }
}
```

- **Servidor informa vitória:** Jogada do oponente como payload
```json
{
  "type": "WIN",
  "payload": {
    "jogada_oponente": "sci"
  }
}
```
- **Servidor envia ranking:** Formato especifico do ranking como payload
```json
{
  "type": "RAN",
  "payload": {
    "ranking": [
      { "nome": "Gabriel", "vitorias": 5 },
      { "nome": "Alice", "vitorias": 3 }
    ]
  }
}
```
- **Fim da partida:** Mensagem final do servidor como payload
```json
{
  "type": "END",
  "payload": {
    "mensagem": "O vencedor foi Gabriel!"
  }
}
```

## Observação:
- Possivelmente faremos uso de algum método para implementar algum tipo de conexão segura.

