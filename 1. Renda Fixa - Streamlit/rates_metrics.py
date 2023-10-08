import numpy as np
import pandas as pd
import os
import sys
import json
        


def pct_benchmark(s_ret, b_ret, d, name, benchmark):
    """
    s_ret : retorno da serie no periodo
    b_ret : retorno do benchmark no periodo
    d: numero de dias do periodo (lembrando que se s_ret e b_ret tiverem acontecido 
        em quantidade de dias diferntes, isso deve ser levado em conta)
    benchmark: aqui eu apenas descrevo o nome do benchmark
    """
    b_percentage = (1-(s_ret+1)**(1/d))/(1-(b_ret+1)**(1/d) )

    y = (1+b_ret)**(1/d)-1

    b_plus = ((1 + b_percentage*y)/(1+y))**252-1
    dic = {f'{benchmark}':b_ret,
          f"{name}":s_ret,
          f"% {benchmark}":b_percentage,
          f"{benchmark}_plus":b_plus}
    return dic


def dayRate(q, name, benchmark):
    q = q[[name, benchmark]].dropna()
    dayRates = q.pct_change().iloc[-1].fillna(0)
    d = pct_benchmark(dayRates[name],dayRates[benchmark],1, name, benchmark)
    return d


def monthRate(q, name, benchmark):
    q = q[[name, benchmark]]
    ratesMonthly = q.resample('m').last().pct_change()
    number_days = q.groupby(q.index.to_period('M')).count()
    if np.isnan(ratesMonthly[name].iloc[-1]):
        ratesMonthly[name].iloc[-1] = (q[name].iloc[-1] - startingQuotes[name])/startingQuotes[name]
        index0 = q[name].dropna().index[0]
        try:
            index1 = q[name].dropna().index[-1]
        except IndexError:
            index1 = q[name].dropna().index[-1]
        ratesMonthly[benchmark].iloc[-1] = \
            q[benchmark].loc[index1]/q[benchmark].loc[index0] - 1
    ratesMonthly = ratesMonthly[[name, benchmark]].fillna(0)
    return pct_benchmark(ratesMonthly[name].iloc[-1],ratesMonthly[benchmark].iloc[-1],number_days[name].iloc[-1], name, benchmark)


def yearRate(q, name, benchmark):
    ratesYearly = q.resample('y').last().pct_change()
    number_days = q.groupby(q.index.to_period('Y')).count()
    if np.isnan(ratesYearly[name].iloc[-1]):
        ratesYearly[name].iloc[-1] = (q[name].iloc[-1] - startingQuotes[name] )/startingQuotes[name]
        index0 = q[name].dropna().index[0]
        try:
            index1 = q[name].dropna().index[-1]
        except IndexError:
            index1 = q[name].dropna().index[-1]
        ratesYearly[benchmark].iloc[-1] = \
            q[benchmark].loc[index1]/q[benchmark].loc[index0] - 1
    ratesYearly = ratesYearly.fillna(0)
    return pct_benchmark(ratesYearly[name].iloc[-1],ratesYearly[benchmark].iloc[-1],number_days[name].iloc[-1], name, benchmark)


def rates12m(q, name, benchmark):
    q = q[[name, benchmark]]
    number_days = q.groupby(q.index.to_period('M')).count().iloc[1:].sum()[name]
    number_days = q.last('13m').resample('12m',closed='right').count().max()[name]
    change = q.last('13m').resample('12m',closed='right').last().pct_change()
    if np.isnan(change[name].iloc[-1]):
        return startRate(q, name, benchmark)
    else:
        return pct_benchmark(change[name].iloc[-1],change[benchmark].iloc[-1],number_days, name, benchmark)
    
def rates3m(q, name, benchmark):
    q = q[[name, benchmark]]
    number_days = q.groupby(q.index.to_period('M')).count().iloc[1:].sum()[name]
    number_days = q.last('4m').resample('3m',closed='right').count().max()[name]
    change = q.last('4m').resample('3m',closed='right').last().pct_change()
    if np.isnan(change[name].iloc[-1]):
        return startRate(q, name, benchmark)
    else:
        return pct_benchmark(change[name].iloc[-1],change[benchmark].iloc[-1],number_days, name, benchmark)


def startRate(q, name, benchmark):
    index0 = q[name].dropna().index[0]
    try:
        index1 = q[name].dropna().index[-1]
    except IndexError:
        index1 = q[name].dropna().index[-1]
    ratesStart = pd.DataFrame(
        data={
            name: [(q[name].iloc[-1] - startingQuotes[name])/startingQuotes[name]],
            benchmark: (q[benchmark].loc[index1])/(q[benchmark].loc[index0])-1
            }
        )
    ratesStart = ratesStart.iloc[-1].fillna(0)
    number_days = len(q[name].dropna())
    return pct_benchmark(ratesStart[name],ratesStart[benchmark],number_days, name, benchmark)


def weekRate(q, name, benchmark):
    ratesweek = q.resample("w").last().pct_change()
    return ratesweek
