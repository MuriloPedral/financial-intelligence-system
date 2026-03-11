import random
from collections import Counter


# CATEGORIES
CATEGORIES = ['groceries', 'restaurant', 'transport', 'entertainment', 'utilities', 'health', 'shopping', 'travel']

def choose_fav_categories(categories, k=3):
    return random.sample(categories, k)

def generate_category_weights(fav_categories):
    pesos = [random.random() for _ in fav_categories]
    soma = sum(pesos)

    return {
        categoria: round(peso / soma, 4)
        for categoria, peso in zip(fav_categories, pesos)
    }


# CITY
CITIES = [('Aracaju', 0.6), ('São Cristóvão', 0.15), ('Estância', 0.1), ('Barra dos Coqueiros', 0.1), ('Itabi', 0.05)]

def choose_home_city():
    cidades = [c[0] for c in CITIES]
    pesos = [c[1] for c in CITIES]

    return random.choices(cidades, weights=pesos)[0]


# ACTIVITY
def activity_selector():
    activity = random.choices(['low', 'medium', 'high'], weights=[0.3, 0.5, 0.2])[0]

    if activity == 'low':
        transactions = random.randint(2, 3)
    elif activity == 'medium':
        transactions = random.randint(4, 6)
    else:
        transactions = random.randint(7, 10)

    return activity, transactions


# SALARY
def random_salary():
    faixa = random.choices(['low', 'medium', 'high'], weights=[0.5, 0.35, 0.15])[0]

    if faixa == 'low':
        salary = random.uniform(1518, 3000)
    elif faixa == 'medium':
        salary = random.uniform(3000, 8000)
    else:
        salary = random.uniform(8000, 15000)

    return round(salary, 2)


# INITIAL BALANCE
def generate_initial_balance(salary):
    fator = random.uniform(0.5, 3)

    return round(salary * fator, 2)


# ACTIVE HOURS
def generate_active_hours():
    perfil = random.choice(['day', 'mixed', 'night'])

    if perfil == 'day':
        return 6, 20
    elif perfil == 'mixed':
        return 9, 23
    else:
        return 18, 2


# ACCOUNT GENERATOR
def account_generator(account_id):
    salary = random_salary()

    initial_balance = generate_initial_balance(salary)

    activity, transactions = activity_selector()

    fav_categories = choose_fav_categories(CATEGORIES)

    category_weights = generate_category_weights(fav_categories)

    start_hour, end_hour = generate_active_hours()

    account = {
        "account_id": account_id,
        "home_city": choose_home_city(),
        "initial_balance": initial_balance,
        "current_balance": initial_balance,
        "salary": salary,
        "activity_level": activity,
        "transactions_per_day": transactions,
        "favorite_categories": category_weights,
        "active_hour_start": start_hour,
        "active_hour_end": end_hour
    }

    return account


# MULTIPLE ACCOUNTS
def generate_accounts(n):
    accounts = []

    for i in range(n):
        account = account_generator(i + 1)
        accounts.append(account)

    return accounts

# TEST
accounts = generate_accounts(5)
for acc in accounts:
    print(acc)