from models.pycragapi import CRAG
import re

api = CRAG()

# Mapping untuk normalisasi kategori Oscar
Oscar_map = {
    'best actor': 'ACTOR IN A LEADING ROLE',
    'best actress': 'ACTRESS IN A LEADING ROLE',
    'best picture': 'BEST PICTURE',
    'best director': 'DIRECTING'
}

def extract_parts(commd):
    """Mengekstrak fungsi, argumen, dan atribut dengan regex yang lebih fleksibel."""
    # Mencoba ekstrak fungsi(argumen)[atribut]
    match = re.search(r"(\w+)\((.*)\)\[\"?(.*?)\"?\]", commd)
    if match:
        return [match.group(1), match.group(2).replace('"', '').strip(), match.group(3)]
    
    # Fallback jika tidak ada kurung siku []
    match_no_attr = re.search(r"(\w+)\((.*)\)", commd)
    if match_no_attr:
        return [match_no_attr.group(1), match_no_attr.group(2).replace('"', '').strip(), "none"]
    
    return ["none", "none", "none"]

def parse_answer(commd):
    print(f"[DEBUG] PARSING API COMMAND: {commd.strip()}")
    
    # Menghindari teks "None" dari LLM
    if commd.strip().lower() == "none":
        return [], []

    commands = commd.lower().strip().split('get_')
    all_context = []
    
    VALID_FUNCTIONS = [
        'movie', 'movie_person_oscar', 'stock_price', 
        'stock_market_cap', 'song', 'person', 'grammy_person'
    ]

    for cmd in commands:
        if not cmd: continue
        args = extract_parts("get_" + cmd)
        
        # 1. Validasi Fungsi (Whitelisting)
        func_name = args[0].replace('get_', '')
        if func_name not in VALID_FUNCTIONS:
            print(f"[DEBUG] Ignoring hallucinated function: {func_name}")
            continue

        print(f"[DEBUG] Processing Valid Args: {args}")
        
        try:
            # --- DOMAIN MOVIE ---
            if func_name == 'movie':
                res = api.movie_get_movie_info(args[1])
                if res['result']:
                    attr = args[2] if args[2] != "key_name" else "title"
                    val = res['result'][0].get(attr, "information found")
                    all_context.append(f"The {attr} of {args[1]} is {val}.")

            elif func_name == 'movie_person_oscar':
                year_match = re.search(r"(\d{4})", args[1])
                if year_match:
                    year = year_match.group(1)
                    res = api.movie_get_year_info(year)
                    if res['result']:
                        all_context.append(f"Database contains Oscar records for the year {year}.")

            # --- DOMAIN FINANCE ---
            elif func_name in ['stock_price', 'stock_market_cap']:
                # Ambil ticker
                ticker_res = api.finance_get_ticker_by_name(args[1])
                if ticker_res['result']:
                    ticker = ticker_res['result'][0]
                    if func_name == 'stock_market_cap':
                        cap = api.finance_get_market_capitalization(ticker)
                        all_context.append(f"The market capitalization of {args[1]} ({ticker}) is {cap['result']}.")
                    else:
                        # Default ke 'close' jika LLM memberikan 'key_name'
                        attr = args[2] if args[2] not in ["key_name", "none"] else "close"
                        all_context.append(f"Financial data for {args[1]} ({ticker}) regarding {attr} is available.")

            # --- DOMAIN MUSIC ---
            elif func_name == 'song':
                # Implementasi pencarian lagu jika ada di pycragapi
                all_context.append(f"Music information for song '{args[1]}' is being retrieved.")

        except Exception as e:
            print(f"[DEBUG] Error executing {func_name}: {e}")

    return [], all_context