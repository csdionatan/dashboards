import pandas as pd
import rates_metrics as rates

def builder(quotes):
    last_day = quotes.index[-1].strftime('%Y-%m-%d')
    df = pd.DataFrame(
        data = {
            f'{last_day}':[],
            'Rent Dia:': [],
            'Rent Mês': [],
            'Rent 3m': [],
            'Rent Ano': [],
            'Rent 12m': [],            
        }
    )
    
    for q in quotes.columns:
        if q == 'CDI':
            continue
        else:
            name = q
            benchmark = 'CDI'
            line = build_line(quotes, q, benchmark=benchmark)
            df = pd.concat(
                [
                    df,
                    line
                ]
            )
    df = df.set_index(df.columns[0])
    for col in df.columns:
        df[col] = df[col].astype(str).str.replace('.',',',regex=False)
        df[col] = df[col].astype(str).str.replace(';','.',regex=False)
    return df

def build_line(quotes, name, benchmark):
    last_day = quotes.index[-1].strftime('%Y-%m-%d')
    q = quotes
    ratesDaily = rates.dayRate(q,name,benchmark)
    ratesMonthly = rates.monthRate(q, name, benchmark)
    rates3m = rates.rates3m(q, name, benchmark)
    ratesYearly = rates.yearRate(q, name, benchmark)
    rates12m = rates.rates12m(q, name, benchmark)
    r = []
    rates_list = [ratesDaily,
                  ratesMonthly,
                  rates3m,
                  ratesYearly,
                  rates12m]
    for rate in rates_list:
        r.append(
            '{:+.2%} ({:.1%} CDI)'.format(
                rate[name],
                rate[f'% {benchmark}'] if rate[f'% {benchmark}'] else 0
                )
            )
    df = pd.DataFrame(
        data={
            f'{last_day}': [name],
            'Rent Dia:': [r[0]],
            'Rent Mês': [r[1]],
            'Rent 3m': [r[2]],
            'Rent Ano': [r[3]],
            'Rent 12m': [r[4]],
            }
        )
    return df