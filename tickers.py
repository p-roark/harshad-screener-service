# tickers.py
"""Canonical ticker lists for SP500, NDX100, MidCap400, and SmallCap600 universes.
Imported by screener.py and optimizer.py to avoid circular imports.
"""

SP500_TICKERS = [
    # Technology
    'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'GOOG', 'META', 'AVGO', 'ORCL', 'CSCO', 'ACN',
    'IBM', 'TXN', 'QCOM', 'AMAT', 'MU', 'LRCX', 'ADI', 'KLAC', 'MCHP', 'STX',
    'KEYS', 'FTNT', 'PANW', 'CDNS', 'SNPS', 'TYL', 'PTC', 'NOW', 'CRM', 'PLTR',
    # Healthcare
    'LLY', 'UNH', 'JNJ', 'MRK', 'ABBV', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN',
    'ISRG', 'VRTX', 'REGN', 'CI', 'CVS', 'HCA', 'ELV', 'CNC', 'HUM', 'BIIB',
    'GILD', 'MRNA', 'DXCM', 'IQV', 'ZTS', 'IDXX', 'BAX', 'BDX', 'SYK', 'BSX',
    # Financials
    'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'AXP',
    'SPGI', 'ICE', 'SCHW', 'CME', 'PGR', 'AFL', 'MET', 'ALL', 'TRV', 'PRU',
    'AIG', 'USB', 'PNC', 'TFC', 'COF', 'SYF', 'FITB', 'KEY', 'CFG', 'ALLY',
    # Consumer Discretionary
    'AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'LOW', 'TGT', 'COST', 'TJX',
    'BKNG', 'HLT', 'MAR', 'GM', 'F', 'YUM', 'CMG', 'DRI', 'ULTA', 'BBY',
    # Consumer Staples
    'PG', 'KO', 'PEP', 'WMT', 'PM', 'MO', 'STZ', 'CL', 'KMB', 'CLX',
    'MDLZ', 'KHC', 'GIS', 'SYY', 'KR', 'ADM',
    # Industrials
    'CAT', 'DE', 'HON', 'UPS', 'RTX', 'LMT', 'BA', 'GE', 'MMM', 'EMR',
    'ETN', 'PH', 'ROK', 'FDX', 'CSX', 'UNP', 'NSC', 'WM', 'RSG', 'CTAS',
    'FAST', 'GWW', 'DOV', 'ITW', 'SWK', 'IR', 'AME', 'XYL', 'PCAR', 'ODFL',
    # Energy
    'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'VLO', 'PSX', 'KMI', 'OKE',
    'WMB', 'HAL', 'BKR', 'DVN', 'FANG', 'OXY', 'APA', 'CTRA', 'PR', 'NOG',
    # Real Estate
    'PLD', 'AMT', 'CCI', 'EQIX', 'PSA', 'DLR', 'O', 'SPG', 'VICI', 'EXR',
    'AVB', 'EQR', 'WY', 'ARE', 'MAA',
    # Utilities
    'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'XEL', 'WEC', 'ES', 'AWK',
    'ETR', 'FE', 'PPL', 'CMS', 'AES',
    # Communication
    'NFLX', 'DIS', 'CMCSA', 'T', 'VZ', 'CHTR', 'EA', 'TTWO', 'FOXA', 'WBD',
    # Materials
    'LIN', 'APD', 'ECL', 'SHW', 'NEM', 'FCX', 'NUE', 'STLD', 'VMC', 'MLM',
    'PPG', 'IFF', 'ALB', 'CF', 'MOS',
]

NDX100_TICKERS = [
    'AAPL', 'MSFT', 'NVDA', 'AMZN', 'META', 'TSLA', 'GOOGL', 'GOOG', 'AVGO', 'COST',
    'NFLX', 'AMD', 'CSCO', 'ADBE', 'QCOM', 'INTU', 'LIN', 'TXN', 'AMAT', 'ISRG',
    'AMGN', 'MU', 'BKNG', 'CMCSA', 'LRCX', 'HON', 'REGN', 'VRTX', 'ADI', 'KLAC',
    'PANW', 'SNPS', 'SBUX', 'CDNS', 'GILD', 'MDLZ', 'ADP', 'CTAS', 'CSX', 'PYPL',
    'MAR', 'ORLY', 'PCAR', 'CHTR', 'MRNA', 'ADSK', 'ROST', 'FTNT', 'MNST', 'ABNB',
    'MCHP', 'PAYX', 'DXCM', 'AEP', 'NXPI', 'WDAY', 'KDP', 'BIIB', 'ODFL', 'FAST',
    'EA', 'XEL', 'TTD', 'EXC', 'VRSK', 'BKR', 'LULU', 'ON', 'ZS', 'TEAM',
    'CTSH', 'DLTR', 'GEHC', 'IDXX', 'KHC', 'ROP', 'FANG', 'CDW', 'ILMN',
    'WBD', 'ENPH', 'DDOG', 'CPRT', 'MDB', 'CRWD', 'OKTA', 'ZM', 'ALGN', 'CEG',
    'INTC', 'ARM', 'MELI', 'AZN', 'ASML', 'PDD', 'CCEP', 'GFS', 'SMCI', 'RIVN',
]

MIDCAP_TICKERS = [
    # Technology
    'EPAM', 'GLOB', 'GDDY', 'WEX', 'SAIC', 'EXLS', 'CACI', 'MANH', 'QLYS', 'TENB',
    'QTWO', 'PCTY', 'SPSC', 'APPF', 'NCNO', 'ALKT', 'PEGA', 'PRGS',
    # Healthcare
    'ACAD', 'ALKS', 'PRGO', 'HALO', 'ITGR', 'MMSI', 'NEOG', 'OMCL', 'INVA', 'AGIO',
    'CLDX', 'HRTX', 'RCUS', 'TGTX', 'ACLS', 'PNTG', 'SGRY', 'ICUI',
    # Consumer Discretionary
    'BURL', 'FIVE', 'RH', 'DKS', 'BOOT', 'CBRL', 'CAKE', 'JACK',
    'PLAY', 'POOL', 'SBH', 'XPEL', 'GOOS', 'TXRH', 'FAT', 'GOLF',
    # Financials
    'AFG', 'BANF', 'BHF', 'CBSH', 'CFR', 'EWBC', 'FHN', 'GBCI', 'BOKF',
    'CVBF', 'GATX', 'HWC', 'LKFN', 'AUB', 'EFC', 'FFBC', 'NBTB', 'WSBC',
    # Industrials
    'AGCO', 'ALG', 'BWA', 'HRI', 'ITT', 'MWA', 'PRIM', 'GNRC', 'GVA',
    'HAYW', 'KTOS', 'AIR', 'ARCB', 'HUBB', 'WNEB', 'SXI', 'ASTE', 'BCPC',
    # Energy
    'DNOW', 'RES', 'HESM', 'VNOM', 'WTTR', 'PUMP', 'TRGP',
    # Materials
    'ATR', 'AVNT', 'CLF', 'HWKN', 'OI', 'SEE', 'LBRT', 'TREX', 'UFPI', 'WOR',
    # Real Estate
    'AIV', 'BRT', 'CUBE', 'IRT', 'LTC', 'STAG', 'GOOD', 'NNN',
]

SMALLCAP_TICKERS = [
    # Technology
    'CRUS', 'POWI', 'SMTC', 'DIOD', 'ONTO', 'FORM', 'KLIC', 'AEIS', 'AMBA', 'COHU',
    'ALRM', 'RMBS', 'BL', 'TTEC', 'ACVA',
    # Healthcare
    'ADUS', 'NHC', 'AHCO', 'CCRN', 'ANIK', 'TMDX', 'ENSG', 'HCKT', 'AMSF',
    'MNKD', 'RCKT', 'SUPN', 'HROW', 'PAHC',
    # Consumer Discretionary
    'BJRI', 'BLMN', 'GIII', 'MNRO', 'FRPT', 'KURA', 'PLCE', 'SCVL', 'SONO',
    'CATO', 'DXLG',
    # Consumer Staples
    'CENT', 'LANC', 'SENEA', 'HAIN',
    # Financials
    'CATY', 'FFIN', 'FULT', 'HAFC', 'HTBK', 'IBCP', 'INDB', 'TCBI',
    'WSFS', 'EGBN', 'CFFN', 'LCNB',
    # Industrials
    'AAON', 'APOG', 'BCO', 'BFAM', 'LNN', 'HURN', 'KFRC', 'POWL',
    'MYRG', 'UFPT', 'GFF', 'STRA',
    # Energy
    'MGY', 'TALO', 'PBF', 'DINO', 'RRC',
    # Materials
    'AMWD', 'ASIX', 'BMI', 'KALU', 'MTRN',
    # Real Estate
    'DEA', 'IIPR', 'NXRT', 'SAFE', 'ALEX',
    # Communication
    'AMCX', 'GTN', 'NXST',
    # Utilities
    'MGEE', 'YORW',
]

ALL_TICKERS: list[str] = sorted(set(SP500_TICKERS + NDX100_TICKERS + MIDCAP_TICKERS + SMALLCAP_TICKERS))

CRYPTO_TICKERS = [
    'BTC-USD',   # Bitcoin
    'ETH-USD',   # Ethereum
    'SOL-USD',   # Solana
    'BNB-USD',   # BNB
    'XRP-USD',   # XRP
    'ADA-USD',   # Cardano
    'AVAX-USD',  # Avalanche
    'DOGE-USD',  # Dogecoin
    'DOT-USD',   # Polkadot
    'LINK-USD',  # Chainlink
    'LTC-USD',   # Litecoin
    'NEAR-USD',  # NEAR Protocol
    'UNI-USD',   # Uniswap
    'ATOM-USD',  # Cosmos
    'XLM-USD',   # Stellar
    'ALGO-USD',  # Algorand
    'FIL-USD',   # Filecoin
    'APT-USD',   # Aptos
    'ARB-USD',   # Arbitrum
    'OP-USD',    # Optimism
]
