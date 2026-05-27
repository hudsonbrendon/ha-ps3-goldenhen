# PS3 GoldenHEN — Home Assistant

Integração custom para monitorar e controlar um **PlayStation 3 desbloqueado** (GoldenHEN) pela API HTTP do **webMAN MOD**.

## Pré-requisitos

- PS3 com **GoldenHEN** (ou outro HEN/CFW) **e webMAN MOD instalado e ativo**.
  - GoldenHEN sozinho **não basta** — quem expõe a API HTTP é o webMAN MOD.
  - Baixe em: https://github.com/aldostools/webMAN-MOD/releases
  - Confirme abrindo `http://IP_DO_PS3/` no navegador — deve aparecer o painel do webMAN.
- PS3 com IP fixo/reservado na rede (recomendado).

## Instalação (HACS)

1. HACS → Integrations → menu (⋮) → Custom repositories.
2. Adicione `https://github.com/hudsonbrendon/ha-ps3-goldenhen` como categoria **Integration**.
3. Instale "PS3 GoldenHEN" e reinicie o Home Assistant.
4. Settings → Devices & Services → Add Integration → "PS3 GoldenHEN".
5. Informe o **IP** do PS3 e a porta (padrão **80**).

## Entidades

| Tipo | Entidade |
|------|----------|
| binary_sensor | Online |
| sensor | Temp. CPU, Temp. RSX, Velocidade do fan, Memória livre, Firmware, Jogo atual |
| switch | Fan automático (ON=dinâmico / OFF=manual) |
| button | Reiniciar, Soft reboot, Hard reboot, Desligar, Ejetar disco, Inserir disco |
| image | Capa do jogo (quando disponível) |

## Serviços

- `ps3_goldenhen.notify` — popup na tela do PS3.
- `ps3_goldenhen.buzzer` — toca o buzzer (padrão 0–9).
- `ps3_goldenhen.launch_game` — inicia jogo/ISO por caminho.
- `ps3_goldenhen.set_fan_speed` — define velocidade do fan (0–100%, modo manual).

## Ligar o PS3 remotamente

O PS3 **não tem Wake-on-LAN**, então a integração **não consegue ligá-lo** pela rede (mesma limitação de Xbox 360 RGH). Soluções:

- **Tomada inteligente (smart plug):** ligue a tomada e o PS3 acende sozinho se o "auto power on" do console estiver habilitado, OU use o botão físico. Você pode criar no HA um `switch` da tomada e uma automação que liga a tomada antes de tentar usar o console.
- Desligar/reiniciar funcionam normalmente (via webMAN).

## Aviso

Software de homebrew/jailbreak é por sua conta e risco. Esta integração só fala com o webMAN MOD na sua LAN; nenhum dado sai da rede local.
