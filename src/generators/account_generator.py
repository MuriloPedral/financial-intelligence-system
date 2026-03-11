import random
from collections import Counter

# CATEGORIES
categories = ['groceries', 'restaurant', 'transport', 'entertainment', 'utilities', 'health', 'shopping', 'travel']

def choose_fav_category(categories, quantidade=4):
    sorteadas = random.choices(categories, k=quantidade)
    return Counter(sorteadas)

def categories_chooser_percentage(list_fav_categories):
    valores = {}
    
    for categoria, peso in list_fav_categories.items():
        valores[categoria] = random.random() * peso
    
    soma_total = sum(valores.values())
    
    porcentagens = {}
    
    for categoria, valor in valores.items():
        porcentagens[categoria] = round((valor / soma_total) * 100, 2)
    
    return porcentagens


list_fav_categories = choose_fav_category(categories)
categories_chooser = categories_chooser_percentage(list_fav_categories)


#CITY
cities = ['Aracaju', 'Itabi', 'São Cristovão', 'Estância', 'Barra dos Coqueiros']
cities_anomalie = ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Fortaleza', 'Recife']

def choose_home_city(cities):
    return random.choice(cities)

home_city = choose_home_city(cities)


#ACTIVITY
def activity_selector():
    activity = random.choice(['low','medium','high'])

    if activity == 'low':
        transactions = random.randint(2, 3)
    elif activity == 'medium':
        transactions = random.randint(4, 6)
    elif activity == 'high':
        transactions = random.randint(7, 10)
    
    return activity, transactions

activity, transaction = activity_selector()


#Ver ultimo chat do gpt


#initial_balance = salary * fator_aleatorio
#INITIAL_BALANCE
initial_balance = random.randint(1000, 30000)


#SALARY
def random_salary():
    salary = random.uniform(1518, 20000)
    return round(salary, 2)

salary = random_salary()


#ACCOUNT_GENERATOR
def account_generator():
    account = {
        'account_id': 1,
        'home_city': home_city,
        'initial_balance': initial_balance,
        'salary': salary,
        'activity_level': activity,
        'transactions_per_day': transaction,
        'favorite_categories': categories_chooser,
        'active_hour_start': 8,
        'active_hour_end': 22
    }

    return account

account = account_generator()
print(account)