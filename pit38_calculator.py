import csv
import json
import requests
import argparse
import os
from datetime import datetime, timedelta
import collections

NBP_CACHE = {}

def get_last_working_day(date):
    """Returns the previous working day (T-1)."""
    if date.weekday() == 0:  # Monday -> Friday
        return date - timedelta(days=3)
    elif date.weekday() == 6:  # Sunday -> Friday
        return date - timedelta(days=2)
    else:
        return date - timedelta(days=1)

def get_nbp_rate(currency, date):
    """Fetches NBP Tabela A rate for a given currency and date."""
    if not currency:
        # Fallback if currency is missing
        return 1.0
        
    if currency == 'PLN':
        return 1.0
        
    # Handle GBX (Pence Sterling) -> GBP and divide rate by 100 later
    query_curr = 'GBP' if currency == 'GBX' else currency
        
    target_date = get_last_working_day(date)
    date_str = target_date.strftime('%Y-%m-%d')
    cache_key = f"{query_curr}_{date_str}"
    
    rate = None
    if cache_key in NBP_CACHE:
        rate = NBP_CACHE[cache_key]
    else:
        url = f"http://api.nbp.pl/api/exchangerates/rates/a/{query_curr}/{date_str}/?format=json"
        
        # In case of holidays, NBP API might return 404 for a working day (e.g., 1st of May).
        # We loop backwards up to 7 days to find the last valid rate.
        for _ in range(7):
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    rate = data['rates'][0]['mid']
                    NBP_CACHE[cache_key] = rate
                    break
            except requests.exceptions.RequestException:
                pass
                
            target_date -= timedelta(days=1)
            if target_date.weekday() > 4: # Skip weekend
                 target_date -= timedelta(days=2 if target_date.weekday() == 6 else 1)
            date_str = target_date.strftime('%Y-%m-%d')
            url = f"http://api.nbp.pl/api/exchangerates/rates/a/{query_curr}/{date_str}/?format=json"

    if rate is None:
        raise Exception(f"Could not fetch NBP rate for {query_curr} on {date}")
        
    if currency == 'GBX':
        return rate / 100.0
    return rate
    date_str = target_date.strftime('%Y-%m-%d')
    cache_key = f"{currency}_{date_str}"
    
    if cache_key in NBP_CACHE:
        return NBP_CACHE[cache_key]
        
    url = f"http://api.nbp.pl/api/exchangerates/rates/a/{currency}/{date_str}/?format=json"
    
    # In case of holidays, NBP API might return 404 for a working day (e.g., 1st of May).
    # We loop backwards up to 7 days to find the last valid rate.
    for _ in range(7):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                rate = data['rates'][0]['mid']
                NBP_CACHE[cache_key] = rate
                return rate
        except requests.exceptions.RequestException:
            pass
            
        target_date -= timedelta(days=1)
        if target_date.weekday() > 4: # Skip weekend
             target_date -= timedelta(days=2 if target_date.weekday() == 6 else 1)
        date_str = target_date.strftime('%Y-%m-%d')
        url = f"http://api.nbp.pl/api/exchangerates/rates/a/{currency}/{date_str}/?format=json"

    raise Exception(f"Could not fetch NBP rate for {currency} on {date}")


def parse_invest_csv(filepath):
    """Parses Trading 212 Invest CSV and calculates Invest income and costs."""
    transactions_buy = collections.defaultdict(list) # Ticker -> list of buys
    
    total_revenue_pln = 0.0
    total_cost_pln = 0.0
    
    total_dividends_pln = 0.0
    total_withholding_tax_pln = 0.0
    
    print("\n--- Parsowanie Invest (Akcje/ETF) ---")
    
    with open(filepath, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            action = row['Action']
            if not action:
                continue
                
            time_str = row['Time']
            if not time_str:
                continue
            date = datetime.strptime(time_str.split(' ')[0], '%Y-%m-%d')
            
            ticker = row['Ticker']
            
            if action.startswith('Dividend'):
                # Handle Dividends
                result_curr = row.get('Currency (Result)')
                if not result_curr:
                     # Some T212 exports have empty summary currency for dividends, but 'Currency (Price / share)' might be there
                     result_curr = row.get('Currency (Price / share)', 'USD') # Default to USD if really nothing is found
                     
                total = float(row['Total']) # Wartość po podatku
                withholding_tax = float(row['Withholding tax']) if row['Withholding tax'] else 0.0
                
                # NBP z T-1 od daty wpłynięcia
                try:
                    rate = get_nbp_rate(result_curr, date)
                    div_gross_pln = (total + withholding_tax) * rate
                    tax_pln = withholding_tax * rate
                    
                    total_dividends_pln += div_gross_pln
                    total_withholding_tax_pln += tax_pln
                except Exception as e:
                    print(f"Błąd pobierania kursu NBP dla dywidendy z {date}: {e}")
                    
            elif action == 'Market buy' or action == 'Limit buy':
                 qty = float(row['No. of shares'])
                 price = float(row['Price / share'])
                 curr = row['Currency (Price / share)']
                 
                 fee1 = float(row['Stamp duty reserve tax']) if row['Stamp duty reserve tax'] else 0.0
                 fee2 = float(row['Currency conversion fee']) if row['Currency conversion fee'] else 0.0
                 fee_curr = row.get('Currency (Currency conversion fee)', 'PLN')
                 if not fee_curr: fee_curr = 'PLN'
                 
                 transactions_buy[ticker].append({
                     'date': date,
                     'qty': qty,
                     'price': price,
                     'curr': curr,
                     'fees': fee1 + fee2, # Dla uproszczenia (T212 przeważnie opłaty podaje w walucie konta, załóżmy że są 1:1 jeśli puste, w pliku testowym są w PLN)
                     'fee_curr': fee_curr
                 })
                 
            elif action == 'Market sell' or action == 'Limit sell':
                 qty = float(row['No. of shares'])
                 price = float(row['Price / share'])
                 curr = row['Currency (Price / share)']
                 
                 fee1 = float(row.get('Currency conversion fee', 0) or 0)
                 fee_curr = row.get('Currency (Currency conversion fee)', 'PLN')
                 if not fee_curr: fee_curr = 'PLN'
                 
                 try:
                     rate_sell = get_nbp_rate(curr, date)
                     revenue_pln = qty * price * rate_sell
                     total_revenue_pln += revenue_pln
                     
                     fee_sell_rate = get_nbp_rate(fee_curr, date)
                     total_cost_pln += fee1 * fee_sell_rate
                     
                     # FIFO logic for resolving costs
                     while qty > 0 and transactions_buy[ticker]:
                         buy = transactions_buy[ticker][0]
                         matched_qty = min(qty, buy['qty'])
                         
                         rate_buy = get_nbp_rate(buy['curr'], buy['date'])
                         cost_pln = matched_qty * buy['price'] * rate_buy
                         
                         # Add fees to cost (proportional to matched qty)
                         fee_buy_rate = get_nbp_rate(buy['fee_curr'], buy['date'])
                         cost_pln += (buy['fees'] * (matched_qty / buy['qty'])) * fee_buy_rate
                         
                         total_cost_pln += cost_pln
                         
                         buy['qty'] -= matched_qty
                         buy['fees'] -= buy['fees'] * (matched_qty / (buy['qty'] + matched_qty)) if buy['qty'] > 0 else buy['fees']
                         qty -= matched_qty
                         
                         if buy['qty'] <= 0:
                             transactions_buy[ticker].pop(0)
                 except Exception as e:
                     print(f"Błąd rozliczania {ticker}: {e}")
                     
    return total_revenue_pln, total_cost_pln, total_dividends_pln, total_withholding_tax_pln


def parse_cfd_json(filepath):
    """Parses Trading 212 CFD JSON and calculates CFD income and costs."""
    total_revenue_pln = 0.0
    total_cost_pln = 0.0
    
    print("\n--- Parsowanie CFD ---")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for item in data:
        t = item['type']
        
        # Fees are added to costs
        if t in ['FEE_FX', 'FEE_OVERNIGHT']:
             # Fees from CFD in latest Trading212 JSONs are typically in Account Currency (PLN)
             fee = 0.0
             if 'interestInAccountCurrency' in item:
                 fee = float(item['interestInAccountCurrency'])
             elif 'feeInPLN' in item:
                 fee = float(item['feeInPLN'])
                 
             # A negative fee is a cost (we keep costs positive in our logic)
             if fee < 0:
                total_cost_pln += abs(fee)
             elif fee > 0:
                # Jeśli opłata była dodatnia (bardzo rzadkie, ale możliwe np. przy short overnight), to obniża koszty lub zwiększa przychód
                total_cost_pln -= fee 
                
        elif t == 'POSITION':
             try:
                 open_date = datetime.fromisoformat(item['openingTime'].replace('Z', '+00:00')).replace(tzinfo=None)
                 close_date = datetime.fromisoformat(item['time'].replace('Z', '+00:00')).replace(tzinfo=None)
                 
                 qty = float(item['quantity'])
                 open_price = float(item['openPrice'])
                 close_price = float(item['closePrice'])
                 curr = item['currency']
                 direction = item['direction']
                 
                 rate_open = get_nbp_rate(curr, open_date)
                 rate_close = get_nbp_rate(curr, close_date)
                 
                 if direction.lower() == 'long' or direction.lower() == 'buy':
                     rev = close_price * qty * rate_close
                     cost = open_price * qty * rate_open
                     total_revenue_pln += rev
                     total_cost_pln += cost
                 elif direction.lower() == 'short' or direction.lower() == 'sell':
                     rev = open_price * qty * rate_open
                     cost = close_price * qty * rate_close
                     total_revenue_pln += rev
                     total_cost_pln += cost
             except Exception as e:
                 print(f"Błąd w CFD (POSITION): {e}")
                 
    return total_revenue_pln, total_cost_pln


def main():
    parser = argparse.ArgumentParser(description="Kalkulator PIT-38 z danych Trading 212.")
    parser.add_argument("--rok", type=int, default=2025, help="Rok podatkowy do rozliczenia (np. 2026)")
    parser.add_argument("--dir", type=str, default="data", help="Katalog z plikami wyeksportowanymi z T212")
    args = parser.parse_args()
    
    invest_csv = os.path.join(args.dir, str(args.rok), "trading-212-invest.csv")
    cfd_json = os.path.join(args.dir, str(args.rok), "trading-212-cfd.json")
    
    print(f"\n--- Rozliczanie PIT-38 za rok {args.rok} ---")
    
    # 1. Oblicz Invest
    inv_rev, inv_cost, div_gross, div_tax_paid = 0.0, 0.0, 0.0, 0.0
    if os.path.exists(invest_csv):
        inv_rev, inv_cost, div_gross, div_tax_paid = parse_invest_csv(invest_csv)
    else:
        print(f"Brak pliku Invest (akcje/ETF). Pomijam: {invest_csv}")
    
    # 2. Oblicz CFD
    cfd_rev, cfd_cost = 0.0, 0.0
    if os.path.exists(cfd_json):
        cfd_rev, cfd_cost = parse_cfd_json(cfd_json)
    else:
        print(f"Brak pliku CFD. Pomijam: {cfd_json}")
    
    # 3. Podsumowanie
    total_rev = inv_rev + cfd_rev
    total_cost = inv_cost + cfd_cost
    income = max(0, total_rev - total_cost)
    tax_19 = income * 0.19
    
    div_tax_due = div_gross * 0.19
    div_tax_to_pay = max(0, div_tax_due - div_tax_paid)
    
    print("\n======= WYNIKI DLA PIT-38 (Platformy Zagraniczne) =======")
    print(f"Poz. 22 (Przychody z odpłatnego zbycia): {total_rev:.2f} PLN")
    print(f"  - z czego Akcje/ETF: {inv_rev:.2f} PLN")
    print(f"  - z czego CFD:       {cfd_rev:.2f} PLN")
    
    print(f"\nPoz. 23 (Koszty uzyskania przychodów): {total_cost:.2f} PLN")
    print(f"  - z czego Akcje/ETF: {inv_cost:.2f} PLN")
    print(f"  - z czego CFD:       {cfd_cost:.2f} PLN")
    
    print(f"\nPoz. 24 (Dochód) lub Poz. 25 (Strata): {(total_rev - total_cost):.2f} PLN")
    if income > 0:
         print(f"-> Podatek należny (19%): {tax_19:.2f} PLN")
    
    print("\n--- ZRYCZAŁTOWANY PODATEK OD DYWIDEND ZAGRANICZNYCH (SEKCJA G) ---")
    print(f"Poz. 47 (Zryczałtowany podatek obliczony - 19% w PL od kwoty brutto): {div_tax_due:.2f} PLN")
    print(f"Poz. 48 (Podatek zapłacony za granicą): {div_tax_paid:.2f} PLN")
    print(f"-> Różnica do dopłaty w Polsce: {div_tax_to_pay:.2f} PLN")
    print("=================================================================\n")

if __name__ == "__main__":
    main()
