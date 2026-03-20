# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations

# Iterator informa que a funcao gera uma sequencia de datas.
from collections.abc import Iterator
# date, datetime e timedelta controlam o calendario da simulacao.
from datetime import date, datetime, time, timedelta
# Random e usado para escolher horarios aleatorios.
from random import Random


def date_sequence(start_date: date, end_date: date) -> Iterator[date]:
    # Comeca pela data inicial.
    current_date = start_date
    # Segue emitindo datas ate chegar na data final.
    while current_date <= end_date:
        # Entrega a data atual para quem estiver iterando.
        yield current_date
        # Avanca exatamente um dia.
        current_date += timedelta(days=1)


def random_timestamp(current_date: date, start_hour: int, end_hour: int, rng: Random) -> datetime:
    # Quando o horario inicial vem antes do final, usa um intervalo normal.
    if start_hour <= end_hour:
        hour = rng.randint(start_hour, end_hour)
    else:
        # Quando a janela cruza a meia-noite, monta explicitamente as horas validas.
        possible_hours = list(range(start_hour, 24)) + list(range(0, end_hour + 1))
        hour = rng.choice(possible_hours)

    # Completa o horario com minuto e segundo aleatorios.
    minute = rng.randint(0, 59)
    second = rng.randint(0, 59)
    # Combina a data com o horario escolhido.
    return datetime.combine(current_date, time(hour=hour, minute=minute, second=second))
