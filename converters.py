import pandas as pd

def proto_dict_convert(trentbars):
    trentbars_list = [
        {
            "volume": tb.volume,
            "low": tb.low,
            "deltaOpen": tb.deltaOpen,
            "deltaClose": tb.deltaClose,
            "deltaHigh": tb.deltaHigh,
            "utcTimestampInMinutes": tb.utcTimestampInMinutes
        } for tb in trentbars
    ]

    # Μετατροπή της λίστας σε DataFrame
    df = pd.DataFrame(trentbars_list)

    # Αποθήκευση του DataFrame σε CSV
    df.to_csv("trentbars_data.csv", index=False, encoding="utf-8")

    return trentbars_list
